# book_recommendation/celery.py
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# تنظیمات پیش فرض Django برای celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "book_recommendation.settings")

app = Celery("book_recommendation")

# تنظیمات را از فایل تنظیمات Django دریافت می‌کند
app.config_from_object("django.conf:settings", namespace="CELERY")

# به طور خودکار وظایف را در تمام اپلیکیشن‌های Django پیدا می‌کند
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
