import os

from dotenv import load_dotenv
from kavenegar import *

load_dotenv()


def send_otp_code(phone_number, code):
    try:
        api_key = os.environ.get("KavenegarAPI")
        api = KavenegarAPI(api_key)

        params = {
            "sender": "",
            "receptor": phone_number,
            "message": f"کد تایید شما برای این ثبت نام در سایت ما : {code}",
        }

        response = api.sms_send(params)

    except APIException as e:
        print(e)

    except HTTPException as e:
        print(e)
