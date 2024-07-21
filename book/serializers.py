# book/serializers.py
from rest_framework import serializers

from .models import Book, Review


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "genre", "publish_date"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "book", "review_text", "rating"]
