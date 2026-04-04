from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from orders.models import Order, PendingPayment
from orders.serializers import OrderListCreateSerializer, OrderDetailSerializer, OrderStatusUpdateSerializer, TrackOrderSerializer
from permissions.shop_permissions import IsShopMember
from django.db.models import Prefetch
from orders.models import OrderItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import uuid
from shops.models import Shop
from django.conf import settings
import requests
import hmac
import hashlib
import json
from django.db import transaction
from products.models import Product, Package


def calculate_order_total_from_items(items):
    """
    Sum line totals. Each item has product XOR package (PK int or Product/Package instance) and quantity.
    """
    if not items:
        raise serializers.ValidationError({"items": "Items are required"})
    total = Decimal("0")
    for item in items:
        qty = item.get("quantity")
        if qty is None or qty < 1:
            raise serializers.ValidationError({"items": "Each item needs quantity >= 1"})
        product = item.get("product")
        package = item.get("package")
        if product is not None and package is not None:
            raise serializers.ValidationError({"items": "Item cannot have both product and package"})
        if product is not None:
            unit_price = product.price if hasattr(product, "price") else Product.objects.get(pk=product).price
        elif package is not None:
            unit_price = package.price if hasattr(package, "price") else Package.objects.get(pk=package).price
        else:
            raise serializers.ValidationError({"items": "Item must have either product or package"})
        total += unit_price * qty
    return total


def amount_to_paystack_pesewas(amount):
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def first_validation_message(detail):
    """Pick a single human-readable string from DRF ValidationError.detail."""
    if detail is None:
        return None
    if isinstance(detail, dict):
        for val in detail.values():
            if isinstance(val, list) and val:
                return str(val[0])
            if isinstance(val, str):
                return val
        return None
    if isinstance(detail, list) and detail:
        return str(detail[0])
    return str(detail)


def verify_failure_response(message, http_status=status.HTTP_400_BAD_REQUEST, **extra):
    body = {"status": "failed", "message": message}
    body.update(extra)
    return Response(body, status=http_status)


# Create your views here.
class OrderView(ListCreateAPIView):
    serializer_class = OrderListCreateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]

        return (
            Order.objects
            .filter(shop_id=shop_id)
            .select_related("shop")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "package")
                )
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(shop_id=self.kwargs["shop_id"])

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated(), IsShopMember()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        order = serializer.instance
        headers = self.get_success_headers(serializer.data)
        return Response(OrderDetailSerializer(order, context={"request": request}).data, status=status.HTTP_201_CREATED, headers=headers)


class OrderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsShopMember]
    lookup_field = "id"
    lookup_url_kwarg = "order_id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return OrderStatusUpdateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]

        return (
            Order.objects
            .filter(shop_id=shop_id)
            .select_related("shop")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "package")
                )
            )
            .order_by("-created_at")
        )


class OrderStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]
        return Order.objects.filter(shop_id=shop_id)

    def get(self, request, *args, **kwargs):
        orders = self.get_queryset()
        
        pending_orders = orders.filter(status=Order.StatusChoices.PENDING)
        confirmed_orders = orders.filter(status=Order.StatusChoices.CONFIRMED)
        delivered_orders = orders.filter(status=Order.StatusChoices.DELIVERED)
        done_orders = orders.filter(status=Order.StatusChoices.DONE)
        cancelled_orders = orders.filter(status=Order.StatusChoices.CANCELLED)

        return Response({
            "pending": pending_orders.count(),
            "confirmed": confirmed_orders.count(),
            "delivered": delivered_orders.count(),
            "done": done_orders.count(),
            "cancelled": cancelled_orders.count()
        }, status=status.HTTP_200_OK)


class InitializePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # validate shop id
        shop_id = kwargs.get("shop_id")
        if not shop_id:
            raise serializers.ValidationError({
                "shop_id": "Shop id is required"
            })
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({
                "shop_id": "Shop does not exist"
            })

        order_data = request.data

        # validate order data
        serializer = OrderListCreateSerializer(data=order_data)
        serializer.is_valid(raise_exception=True)

        def generate_email_from_order(customer_name):
            print(customer_name)
            return f"{customer_name.lower().replace(' ', '_')}@breadwinners.com"
            
        email = request.data.get("email")
        if not email:  # handles None and ""
            customer_name = request.data.get("customer_name")
            if not customer_name:
                raise serializers.ValidationError({"customer_name": "Customer name is required"})
            email = generate_email_from_order(customer_name)
        print(email)

        total_amount = request.data.get("total_amount")

        # validate total amount
        actual_order_amount = calculate_order_total_from_items(serializer.validated_data.get("items"))
        if total_amount is None:
            raise serializers.ValidationError({"total_amount": "Total amount is required"})
        try:
            client_total = Decimal(str(total_amount))
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError({"total_amount": "Invalid total amount"})
        if actual_order_amount.quantize(Decimal("0.01")) != client_total.quantize(Decimal("0.01")):
            raise serializers.ValidationError({
                "total_amount": "Invalid total amount"
            })

        amount_in_pesewas = amount_to_paystack_pesewas(actual_order_amount)

        url = settings.PAYSTACK_INITIALIZE_URL
        callback_url = request.data.get("callback_url")
        if not callback_url:
            raise serializers.ValidationError({
                "callback_url": "Callback url is required"
            })
        # validate callback url as a path not link
        if not callback_url.startswith("/"):
            raise serializers.ValidationError({
                "callback_url": "Callback url must be a path"
            })
        callback_url = f"{settings.FRONTEND_BASE_URL}{callback_url}"

        

        with transaction.atomic():
            reference = str(uuid.uuid4())
            # initialize payment
            PendingPayment.objects.create(
                reference=reference,
                amount=actual_order_amount,
                email=email,
                order_data=order_data,
                shop=shop
            )

            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "amount": int(amount_in_pesewas),
                "reference": reference,
                "callback_url": callback_url,
                "email": email
            }

            try:
                response = requests.post(
                    url, headers=headers, json=data,
                    timeout=30  # or (5, 25)
                )
                response.raise_for_status()
            except requests.Timeout:
                # Raised when connect or read exceeds timeout
                raise serializers.ValidationError({
                    "paystack": "Payment provider took too long to respond. Please try again."
                })
            except requests.RequestException as e:
                print(data)
                raise serializers.ValidationError({
                    "paystack": f"Payment provider unavailable: {str(e)}"
                })
            paystack_data = response.json()
            if not paystack_data.get("status"):
                raise serializers.ValidationError({
                    "paystack": paystack_data.get("message", "Payment initialization failed")
                })
            if "data" not in paystack_data:
                raise serializers.ValidationError({"paystack": "Invalid response from payment provider"})
        return Response(paystack_data["data"])


class VerifyPaymentView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        shop_id = kwargs.get("shop_id")
        reference = request.GET.get("reference")

        if not reference:
            return verify_failure_response("Reference is required.", status.HTTP_400_BAD_REQUEST)
        if shop_id is None:
            return verify_failure_response("Shop id is required.", status.HTTP_400_BAD_REQUEST)

        try:
            pending = PendingPayment.objects.get(reference=reference)
        except PendingPayment.DoesNotExist:
            return verify_failure_response(
                "No payment found for this reference.",
                status.HTTP_404_NOT_FOUND,
            )

        if pending.shop_id != int(shop_id):
            return verify_failure_response(
                "This reference does not belong to this shop.",
                status.HTTP_404_NOT_FOUND,
            )

        if pending.status in (PendingPayment.StatusChoices.COMPLETED, "success"):
            order = pending.order
            if order is not None:
                return Response(
                    {
                        "status": "success",
                        "message": "This payment was already verified.",
                        "order": OrderDetailSerializer(order).data
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": "success",
                        "message": "This payment was already verified.",
                        "order": None
                    },
                    status=status.HTTP_200_OK,
                )

        verify_base = settings.PAYSTACK_VERIFY_URL or "https://api.paystack.co/transaction/verify"
        url = f"{verify_base.rstrip('/')}/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

        try:
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()
        except requests.Timeout:
            return verify_failure_response(
                "Payment provider took too long to respond. Please try again.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException:
            return verify_failure_response(
                "Payment provider is unavailable. Please try again later.",
                status.HTTP_502_BAD_GATEWAY,
            )

        try:
            payload = res.json()
        except ValueError:
            return verify_failure_response(
                "Invalid response from payment provider.",
                status.HTTP_502_BAD_GATEWAY,
            )

        def mark_failed_if_pending():
            with transaction.atomic():
                locked = PendingPayment.objects.select_for_update().get(pk=pending.pk)
                if locked.status not in (PendingPayment.StatusChoices.COMPLETED, "success"):
                    locked.status = PendingPayment.StatusChoices.FAILED
                    locked.save(update_fields=["status"])

        if not payload.get("status"):
            # Do not mark pending as failed: Paystack API errors are often transient; client can retry.
            return verify_failure_response(
                payload.get("message", "Payment verification could not be completed. Please try again."),
                status.HTTP_400_BAD_REQUEST,
            )

        tx = payload.get("data")
        if not isinstance(tx, dict):
            return verify_failure_response(
                "Invalid verification data from payment provider.",
                status.HTTP_400_BAD_REQUEST,
            )

        if tx.get("reference") and tx["reference"] != reference:
            mark_failed_if_pending()
            return verify_failure_response(
                "Payment reference does not match this verification request.",
                status.HTTP_400_BAD_REQUEST,
            )

        if tx.get("status") != "success":
            mark_failed_if_pending()
            return verify_failure_response(
                "Payment was not completed successfully.",
                status.HTTP_400_BAD_REQUEST,
            )

        

        charged = tx.get("amount")
        expected_pesewas = amount_to_paystack_pesewas(pending.amount)
        try:
            charged_int = int(charged)
        except (TypeError, ValueError):
            mark_failed_if_pending()
            return verify_failure_response(
                "Invalid amount returned from payment provider.",
                status.HTTP_400_BAD_REQUEST,
            )

        if charged_int != expected_pesewas:
            mark_failed_if_pending()
            return verify_failure_response(
                "Paid amount does not match the order total.",
                status.HTTP_400_BAD_REQUEST,
            )

        order_data = pending.order_data
        items = order_data.get("items") or []
        try:
            recomputed = calculate_order_total_from_items(items)
        except serializers.ValidationError as exc:
            msg = first_validation_message(exc.detail) or "Stored order data is invalid."
            return Response(
                {"status": "failed", "message": msg, "errors": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # if recomputed.quantize(Decimal("0.01")) != Decimal(pending.amount).quantize(Decimal("0.01")):
        #     return Response(
        #         {
        #             "error": "Order total no longer matches this payment (e.g. prices changed). Contact support if you were charged.",
        #         },
        #         status=status.HTTP_409_CONFLICT,
        #     )

        with transaction.atomic():
            locked = PendingPayment.objects.select_for_update().get(reference=reference)
            if locked.shop_id != int(shop_id):
                return verify_failure_response(
                    "This reference does not belong to this shop.",
                    status.HTTP_404_NOT_FOUND,
                )
            if locked.status in (PendingPayment.StatusChoices.COMPLETED, "success"):
                order = locked.order
                if order is not None:
                    return Response(
                        {
                            "status": "success",
                            "message": "This payment was already verified.",
                            "order": OrderDetailSerializer(order).data
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "status": "success",
                            "message": "This payment was already verified.",
                            "order": None
                        },
                        status=status.HTTP_200_OK,
                    )

            order = Order.objects.create(
                customer_name=order_data["customer_name"],
                customer_phone=order_data["customer_phone"],
                delivery_method=order_data["delivery_method"],
                delivery_address=order_data.get("delivery_address"),
                address_latitude=order_data.get("address_latitude"),
                address_longitude=order_data.get("address_longitude"),
                delivery_notes=order_data.get("delivery_notes"),
                email=order_data.get("email"),
                total_amount=recomputed,
                shop=locked.shop,
                payment_status=Order.PaymentStatusChoices.PAID,
            )

            for item in items:
                if item.get("product"):
                    product = Product.objects.get(pk=item["product"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item["quantity"],
                        unit_price=product.price,
                        total_price=product.price * item["quantity"],
                    )
                elif item.get("package"):
                    package = Package.objects.get(pk=item["package"])
                    OrderItem.objects.create(
                        order=order,
                        package=package,
                        quantity=item["quantity"],
                        unit_price=package.price,
                        total_price=package.price * item["quantity"],
                    )

            locked.status = PendingPayment.StatusChoices.COMPLETED
            locked.save(update_fields=["status"])

        return Response(
            {
                "status": "success",
                "message": "Payment verified and order created.",
                "order": OrderDetailSerializer(order).data
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Paystack webhook endpoint.

        What it does (based on your current payment flow):
        - Verifies the webhook signature (`x-paystack-signature`) using `PAYSTACK_SECRET_KEY`.
        - Extracts `reference` from the webhook payload.
        - Looks up the matching `PendingPayment` row and (idempotently) creates an `Order` + `OrderItem`s.
        - Marks `PendingPayment.status` as `completed` (or `failed`) and links `pending.order = order`.
        """

        # Paystack sends a HMAC signature of the raw request body.
        signature = request.headers.get("x-paystack-signature")
        raw_body = request.body or b""

        if not signature:
            return verify_failure_response(
                "Missing Paystack signature header.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        computed_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
            raw_body,
            hashlib.sha512,
        ).hexdigest()

        # Constant-time compare prevents timing attacks.
        if not hmac.compare_digest(signature, computed_signature):
            return verify_failure_response(
                "Invalid Paystack signature.",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except ValueError:
            return verify_failure_response(
                "Invalid JSON payload from Paystack.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # Typical Paystack shape:
        # {
        #   "event": "charge.success",
        #   "data": { "reference": "...", "status": "success", "amount": <pesewas>, ... }
        # }
        data = payload.get("data") or {}
        reference = data.get("reference")

        if not reference:
            return verify_failure_response(
                "Missing reference in Paystack webhook payload.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine whether Paystack says this transaction is successful.
        event_name = payload.get("event")
        tx_status = (data.get("status") or "").lower()
        is_success = tx_status == "success" or event_name == "charge.success"

        charged = data.get("amount")  # amount in pesewas (integer)
        currency = data.get("currency")

        with transaction.atomic():
            try:
                pending = PendingPayment.objects.select_for_update().get(reference=reference)
            except PendingPayment.DoesNotExist:
                # Unknown reference: acknowledge to stop Paystack from retrying indefinitely.
                return Response(
                    {"status": "ignored", "message": "Unknown payment reference."},
                    status=status.HTTP_200_OK,
                )

            # Idempotency: if we already processed this payment, just ACK.
            if pending.status == PendingPayment.StatusChoices.COMPLETED:
                return Response(
                    {
                        "status": "success",
                        "message": "This payment was already processed.",
                    },
                    status=status.HTTP_200_OK,
                )

            if not is_success:
                pending.status = PendingPayment.StatusChoices.FAILED
                pending.save(update_fields=["status"])
                return verify_failure_response(
                    "Paystack reported a failed payment.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate amount matches what we expect for this PendingPayment.
            expected_pesewas = amount_to_paystack_pesewas(pending.amount)
            if charged is not None:
                try:
                    charged_int = int(charged)
                except (TypeError, ValueError):
                    pending.status = PendingPayment.StatusChoices.FAILED
                    pending.save(update_fields=["status"])
                    return verify_failure_response(
                        "Invalid amount in Paystack webhook payload.",
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                if charged_int != expected_pesewas:
                    pending.status = PendingPayment.StatusChoices.FAILED
                    pending.save(update_fields=["status"])
                    return verify_failure_response(
                        "Paid amount does not match the stored order total.",
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

            # Create the order from the stored order_data (never trust the client again here).
            order_data = pending.order_data or {}
            items = order_data.get("items") or []

            try:
                recomputed_total = calculate_order_total_from_items(items)
            except serializers.ValidationError as exc:
                pending.status = PendingPayment.StatusChoices.FAILED
                pending.save(update_fields=["status"])
                return Response(
                    {
                        "status": "failed",
                        "message": first_validation_message(exc.detail)
                        or "Stored order data is invalid.",
                        "errors": exc.detail,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extra safety: ensure recomputed total matches pending.amount.
            # (pending.amount was derived during initialize, but this catches edge cases.)
            if recomputed_total.quantize(Decimal("0.01")) != Decimal(pending.amount).quantize(Decimal("0.01")):
                pending.status = PendingPayment.StatusChoices.FAILED
                pending.save(update_fields=["status"])
                return verify_failure_response(
                    "Order total no longer matches this payment.",
                    http_status=status.HTTP_409_CONFLICT,
                )

            order = Order.objects.create(
                customer_name=order_data["customer_name"],
                customer_phone=order_data["customer_phone"],
                delivery_method=order_data["delivery_method"],
                delivery_address=order_data.get("delivery_address"),
                address_latitude=order_data.get("address_latitude"),
                address_longitude=order_data.get("address_longitude"),
                delivery_notes=order_data.get("delivery_notes"),
                email=order_data.get("email"),
                total_amount=recomputed_total,
                shop=pending.shop,
                payment_status=Order.PaymentStatusChoices.PAID,
            )

            for item in items:
                if item.get("product"):
                    product = Product.objects.get(pk=item["product"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item["quantity"],
                        unit_price=product.price,
                        total_price=product.price * item["quantity"],
                    )
                elif item.get("package"):
                    package = Package.objects.get(pk=item["package"])
                    OrderItem.objects.create(
                        order=order,
                        package=package,
                        quantity=item["quantity"],
                        unit_price=package.price,
                        total_price=package.price * item["quantity"],
                    )

            # Link the created order back to the PendingPayment row.
            pending.order = order
            pending.status = PendingPayment.StatusChoices.COMPLETED
            pending.save(update_fields=["order", "status"])

        return Response(
            {
                "status": "success",
            },
            status=status.HTTP_200_OK,
        )


class TrackOrderView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        customer_phone = request.query_params.get("customer_phone")
        order_number = request.query_params.get("order_number")
        serializer = TrackOrderSerializer(data={"order_number": order_number, "customer_phone": customer_phone})
        serializer.is_valid(raise_exception=True)
        try:
            order = Order.objects.get(order_number=serializer.validated_data.get("order_number"), customer_phone=serializer.validated_data.get("customer_phone"))
        except Order.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "status": "success",
            "message": "Order found",
            "order": OrderDetailSerializer(order).data,
        }, status=status.HTTP_200_OK)