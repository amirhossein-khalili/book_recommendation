# book/serializers.py
from django.db import connection
from rest_framework import serializers

from .models import Book, Review


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "genre", "publish_date"]


class ReviewAddSerializer(serializers.ModelSerializer):

    user = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ["id", "book", "rating", "user"]

    def validate_book(self, value):
        book_id = int(value.id)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM book_book WHERE id = %s;", [book_id])
            count = cursor.fetchone()[0]

        if count == 0:
            raise serializers.ValidationError("There are no books with this id")

        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):

        user_id = data.get("user")
        book_id = data.get("book").id

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM book_review WHERE (book_id = %s AND user_id = %s);",
                [book_id, user_id],
            )
            count = cursor.fetchone()[0]

        if count > 0:
            raise serializers.ValidationError("User has already reviewed this book")

        return data


class ReviewUpdateSerializer(serializers.ModelSerializer):

    user = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "user"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
