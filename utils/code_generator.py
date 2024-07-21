import logging
import random
import string

from django.core.mail import send_mail
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def code_generator(length=6):

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    return code
