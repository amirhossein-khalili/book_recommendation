# book/views.py
from django.db import connection
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Review
from .serializers import BookSerializer, ReviewSerializer


class BookListView(APIView):
    """
    This API will return a list of all books along with the user's rating and the average rating of all users.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.id, b.title, b.author, b.genre, r.rating as user_rating, avg_r.avg_rating
                FROM book_book b
                LEFT JOIN book_review r ON b.id = r.book_id AND r.user_id = %s
                LEFT JOIN (
                    SELECT book_id, AVG(rating) as avg_rating
                    FROM book_review
                    GROUP BY book_id
                ) avg_r ON b.id = avg_r.book_id
                """,
                [user_id],
            )
            books = cursor.fetchall()

        books_list = [self.format_book(book) for book in books]

        return Response(books_list, status=status.HTTP_200_OK)

    def format_book(self, book):
        return {
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "genre": book[3],
            "user_rating": book[4],
            "average_rating": book[5],
        }


class BookFilterView(APIView):

    def get(self, request, *args, **kwargs):
        genre = kwargs.get("genre")

        with connection.cursor() as cursor:
            cursor.execute("""SELECT * FROM book_book WHERE genre=%s""", [genre])
            books = cursor.fetchall()

        books_list = [self.format_book(book) for book in books]

        return Response(books_list, status=status.HTTP_200_OK)

    def format_book(self, book):
        return {
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "genre": book[3],
        }


class BookDetailView(APIView):
    def get(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM book_book WHERE id=%s", [pk])
            book = cursor.fetchone()
        if book:
            book_data = {
                "id": book[0],
                "title": book[1],
                "author": book[2],
                "genre": book[3],
                "publish_date": book[4],
            }
            return Response(book_data, status=status.HTTP_200_OK)
        return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class ReviewAddView(APIView):
    def post(self, request):
        book_id = request.data.get("book")
        review_text = request.data.get("review_text")
        rating = request.data.get("rating")
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO book_review (book_id, review_text, rating) VALUES (%s, %s, %s)",
                [book_id, review_text, rating],
            )
        return Response(
            {"message": "Review added successfully"}, status=status.HTTP_201_CREATED
        )


class ReviewUpdateView(APIView):
    def put(self, request, pk):
        review_text = request.data.get("review_text")
        rating = request.data.get("rating")
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE book_review SET review_text=%s, rating=%s WHERE id=%s",
                [review_text, rating, pk],
            )
        return Response(
            {"message": "Review updated successfully"}, status=status.HTTP_200_OK
        )


class ReviewDeleteView(APIView):
    def delete(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM book_review WHERE id=%s", [pk])
        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class BookRecommendView(APIView):
    def get(self, request, genre):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM book_book WHERE genre=%s", [genre])
            books = cursor.fetchall()
        books_list = [
            {
                "id": book[0],
                "title": book[1],
                "author": book[2],
                "genre": book[3],
                "publish_date": book[4],
            }
            for book in books
        ]
        return Response(books_list, status=status.HTTP_200_OK)
