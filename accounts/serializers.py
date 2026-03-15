from rest_framework import serializers
from accounts.models import User, Profile
from django.contrib.auth.password_validation import validate_password
from utils.utils import generate_setup_url, send_setup_link
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from shops.serializers import ShopSerializer
from shops.models import Shop

class ProfileSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(required=False, allow_null=True)
    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'shop', 'address', 'avatar', 'bio']
        read_only_fields = ['id', 'user']

    def validate(self, attrs):
        role = attrs.get('role')
        shop = attrs.get('shop')

        if role == Profile.RoleChoices.STAFF and not shop:
            raise serializers.ValidationError("Staff must be assigned to a shop.")
       
        if role == Profile.RoleChoices.ADMIN and shop:
            raise serializers.ValidationError("Admin should not be assigned to a shop.")
        
        return attrs


class UserListCreateSerializer(serializers.ModelSerializer):
    # Flat input fields mapped into Profile for creation.
    role = serializers.ChoiceField(choices=Profile.RoleChoices.choices, source='profile.role', required=True)
    shop = serializers.PrimaryKeyRelatedField(
        source='profile.shop',
        queryset=Shop.objects.all(),
        required=False,
        allow_null=True,
    )
    avatar = serializers.ImageField(source='profile.avatar', required=False, allow_null=True)
    address = serializers.CharField(source='profile.address', required=False, allow_blank=True, allow_null=True)
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True, allow_null=True)
    shop_name = serializers.CharField(source='profile.shop.name', read_only=True)

    is_password_set = serializers.SerializerMethodField(read_only=True)

    def get_is_password_set(self, obj):
        return obj.has_usable_password()

    class Meta:
        model = User
        fields = [
            'id',
            'phone_number',
            'first_name',
            'last_name',
            'date_joined',
            'last_login',
            'role',
            'shop',
            'shop_name',
            'address',
            'bio',
            'avatar',
            'is_password_set',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'phone_number': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        profile_data = attrs.get('profile', {})
        role = profile_data.get('role')
        shop = profile_data.get('shop')

        if role == Profile.RoleChoices.STAFF and not shop:
            raise serializers.ValidationError({'shop': 'Staff must be assigned to a shop.'})

        if role == Profile.RoleChoices.ADMIN and shop:
            raise serializers.ValidationError({'shop': 'Admin should not be assigned to a shop.'})

        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})

        phone_number = validated_data.pop('phone_number')
        # create user with transaction
        with transaction.atomic():
            user = User.objects.create_user(phone_number=phone_number, **validated_data)
            Profile.objects.create(user=user, **profile_data)
            # send setup link to user
            send_setup_link(generate_setup_url(user), phone_number)
            return user


class SetupPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        # decode user
        try:
            uid_int = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid_int)
        except Exception:
            raise serializers.ValidationError({"uid": "Invalid setup link"})

        # Verify one-time token
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        # Validate password
        # validate_password(attrs['password'], user=user)

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.save(update_fields=['password'])
        return user


class UserDetailsSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'phone_number', 'date_joined', 'last_login']

    # def update(self, instance, validated_data):
    #     # Extract profile data if provided (use pop with default to avoid KeyError)
    #     profile_data = validated_data.pop('profile', None)
        
    #     # Update user fields
    #     instance.first_name = validated_data.get('first_name', instance.first_name)
    #     instance.last_name = validated_data.get('last_name', instance.last_name)
    #     instance.save()

    #     # Update or create profile if profile_data is provided
    #     if profile_data is not None:
    #         profile, created = Profile.objects.get_or_create(
    #             user=instance,
    #             defaults=profile_data
    #         )
    #         # If profile already existed, update it with new data
    #         if not created:
    #             for attr, value in profile_data.items():
    #                 setattr(profile, attr, value)
    #             profile.save()
        
    #     return instance


class UserDetailsUpdateSerializer(serializers.ModelSerializer):

    role = serializers.ChoiceField(choices=Profile.RoleChoices.choices, source='profile.role', required=False)
    shop = serializers.PrimaryKeyRelatedField(
        source='profile.shop',
        queryset=Shop.objects.all(),
        required=False,
        allow_null=True,
    )
    avatar = serializers.ImageField(source='profile.avatar', required=False, allow_null=True)
    address = serializers.CharField(source='profile.address', required=False, allow_blank=True, allow_null=True)
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'shop', 'avatar', 'address', 'bio']

    def validate(self, attrs):
        profile_data = attrs.get('profile', {})
        profile = getattr(self.instance, 'profile', None)
        existing_role = getattr(profile, 'role', None)
        existing_shop = getattr(profile, 'shop', None)

        # Merge incoming data with existing values for PATCH semantics.
        role = profile_data.get('role', existing_role)
        shop = profile_data.get('shop', existing_shop)

        if role == Profile.RoleChoices.STAFF and not shop:
            raise serializers.ValidationError({'shop': 'Staff must be assigned to a shop.'})

        if role == Profile.RoleChoices.ADMIN:
            # Force admin profiles to have no shop on edit.
            attrs.setdefault('profile', {})
            attrs['profile']['shop'] = None
        return attrs

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user_update_fields = []
        if 'first_name' in validated_data:
            instance.first_name = validated_data.get('first_name')
            user_update_fields.append('first_name')
        if 'last_name' in validated_data:
            instance.last_name = validated_data.get('last_name')
            user_update_fields.append('last_name')
        if user_update_fields:
            instance.save(update_fields=user_update_fields)

        if profile_data is not None:
            profile, created = Profile.objects.get_or_create(
                user=instance,
                defaults=profile_data
            )
            if not created:
                for attr, value in profile_data.items():
                    setattr(profile, attr, value)
                profile.save(update_fields=list(profile_data.keys()))
        
        return instance

