# generate setup url and send to user
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

def generate_setup_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_SETUP_URL}/{uid}/{token}/"

def send_setup_link(url: str, phone_number: str | None = None):
    # TODO: Implement SMS sending, for now we will just print the link
    prefix = f"[SMS to {phone_number}] " if phone_number else "[SMS] "
    message = f"{prefix}Setup link: {url}, please use this link to setup your account."
    try:
        print(message)
    except Exception as e:
        print(f"Error sending setup link: {e}")

