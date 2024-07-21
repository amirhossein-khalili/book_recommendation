import logging

from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from utils import code_generator

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    SignupStepOneSerializer,
    SignupStepTwoSerializer,
)

logger = logging.getLogger(__name__)


# ==================================================
#   Authentication
# ==================================================


class SignupStepOneView(APIView):
    """
    in this part first we check the user data

    and if the user data is valid then we save the user data

    in the cache and send a verification code to user email

    the user data have 1 hour expiration but the verification

    code have only 3 minutes expiration .

    """

    serializer_class = SignupStepOneSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            verification_code = self.send_verification_code(email)

            if verification_code:

                cache.set(
                    f"signup_{email}_user_data",
                    serializer.validated_data,
                    3600,
                )

                cache.set(
                    f"signup_{email}_verification_code",
                    verification_code,
                    180,
                )

                return Response(
                    {"message": "Verification code sent to email"},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {
                        "error": "Failed to send verification code. Please try again later."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_verification_code(self, user_email):
        try:
            code = code_generator()

            send_mail(
                "Verification in the Amir Social Media",
                f"This is your verification code: {code}",
                "amirhossein.khalili.supn@gmail.com",
                [user_email],
                fail_silently=False,
            )

            return code

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return None


class SignupStepTwoView(APIView):
    """

    in this section we get and check if user data exist in the cache

    then we check if the code that user add be true and valid

    if code time passed and the code is expired but the user data is not expired

    then we create a new code and send it to user and set the new code to cache

    after that if the user will be created and data will remove from the cache

    if user not exists in the cache: he should again complete the first step of the verification

    """

    serializer_class = SignupStepTwoSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            code = serializer.validated_data["code"]

            user_data = cache.get(f"signup_{email}_user_data")

            if user_data:
                code_data = cache.get(f"signup_{email}_verification_code")

                if not code_data:
                    verification_code = self.send_verification_code(email)

                    if verification_code:
                        cache.set(
                            f"signup_{email}_verification_code",
                            verification_code,
                            180,
                        )

                        return Response(
                            {
                                "message": "Your code has expired. A new code has been sent to you.",
                            },
                            status=status.HTTP_200_OK,
                        )

                    else:
                        return Response(
                            {
                                "error": "Your code has expired. Failed to send verification code. Please try again later."
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                if code == code_data:
                    user = User(
                        phone_number=user_data["phone_number"], email=user_data["email"]
                    )
                    user.set_password(user_data["password"])
                    user.save()

                    # Delete user data from cache
                    cache.delete(f"signup_{email}_user_data")
                    cache.delete(f"signup_{email}_verification_code")

                    return Response(
                        {"message": "You have signed up successfully 🥳🎉."},
                        status=status.HTTP_201_CREATED,
                    )

                else:
                    return Response(
                        {"error": "invalid code"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(
                {"error": "Please complete the first step of the signup process."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_verification_code(self, user_email):
        try:
            code = code_generator()

            send_mail(
                "Verification in the Amir Social Media",
                f"This is your verification code: {code}",
                "amirhossein.khalili.supn@gmail.com",
                [user_email],
                fail_silently=False,
            )

            return code

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return None


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
