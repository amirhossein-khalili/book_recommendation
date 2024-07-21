from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone_number, email, user_name, password=None):
        if not email:
            raise ValueError("The Email field must be set")
        if not phone_number:
            raise ValueError("The phone_number field must be set")

        email = self.normalize_email(email)
        user = self.model(
            phone_number=phone_number,
            email=email,
            user_name=user_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email, user_name, password=None):
        user = self.create_user(
            phone_number=phone_number,
            email=email,
            user_name=user_name,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user
