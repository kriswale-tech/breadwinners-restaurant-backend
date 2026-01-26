from rest_framework import serializers
from accounts.models import User, Profile
from django.contrib.auth.password_validation import validate_password

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'phone_number', 'address', 'avatar', 'bio']
        read_only_fields = ['id', 'user']


class UserListCreateSerializer(serializers.ModelSerializer):
    # profile serializer for create
    profile = ProfileSerializer(required=True, write_only=True)

    # password serializer for create
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})

    avatar = serializers.ImageField(source='profile.avatar', read_only=True, allow_null=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    role = serializers.CharField(source='profile.role', read_only=True)


    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined', 'last_login', 'phone_number','role', 'avatar', 'password', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_password(self, value):
        validate_password(value) # validate the password by checking the password validation rules from settings.py
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        profile_data = validated_data.pop('profile')

        user = User.objects.create_user(password=password, **validated_data)
        Profile.objects.create(user=user, **profile_data)
        return user


class UserDetailsSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']

    def update(self, instance, validated_data):
        # Extract profile data if provided (use pop with default to avoid KeyError)
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields (email is read-only, so it won't be in validated_data)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        # Update or create profile if profile_data is provided
        if profile_data is not None:
            profile, created = Profile.objects.get_or_create(
                user=instance,
                defaults=profile_data
            )
            # If profile already existed, update it with new data
            if not created:
                for attr, value in profile_data.items():
                    setattr(profile, attr, value)
                profile.save()
        
        return instance