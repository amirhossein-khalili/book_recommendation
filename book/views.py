# book/views.py
from django.core.cache import cache
from django.db import connection
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import remove_duplicates

from .models import Book, Review
from .serializers import BookSerializer, ReviewAddSerializer, ReviewUpdateSerializer
from .services import BookRecommendationServiceFactory


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


class BookGenreListView(APIView):
    """
    This API will give you a list of genres of the books.
    """

    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT genre FROM book_book")
            genres = cursor.fetchall()

        # Flatten the list of tuples into a single list
        genre_list = [genre[0] for genre in genres]

        return Response(genre_list, status=status.HTTP_200_OK)


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
    serializer_class = ReviewAddSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data["user"] = request.user.id
        ser_data = self.serializer_class(data=data)

        if ser_data.is_valid():
            book_id = data.get("book")
            user_id = data.get("user")
            rating = data.get("rating")

            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO book_review (book_id , user_id , rating) VALUES (%s, %s, %s)",
                    [book_id, user_id, rating],
                )

            return Response(
                {"message": "Review added successfully"}, status=status.HTTP_201_CREATED
            )

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewUpdateView(APIView):
    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        rating = request.data.get("rating")
        requested_user_id = request.user.id

        data = request.data.copy()
        data["user"] = request.user.id
        ser_data = self.serializer_class(data=data)

        if ser_data.is_valid():

            user_review = self.get_user_review(pk)
            if user_review is None:
                return Response(
                    {"message": "Review not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if user_review != requested_user_id:
                return Response(
                    {"message": "You do not have access to change this review"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE book_review SET rating=%s WHERE id=%s",
                    [rating, pk],
                )

            return Response(
                {"message": "Review updated successfully"}, status=status.HTTP_200_OK
            )

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_user_review(self, pk):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM book_review WHERE id=%s",
                [pk],
            )
            review = cursor.fetchone()
            if review is None:
                return None
            user_review = review[0]
        return user_review


class ReviewDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        requested_user_id = request.user.id

        data = request.data.copy()
        data["user"] = request.user.id

        user_review = self.get_user_review(pk)
        if user_review is None:
            return Response(
                {"message": "Review not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user_review != requested_user_id:
            return Response(
                {"message": "You do not have access to delete this review"},
                status=status.HTTP_403_FORBIDDEN,
            )

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM book_review WHERE id=%s",
                [pk],
            )

        return Response(
            {"message": "Review Deleted successfully"}, status=status.HTTP_200_OK
        )

    def get_user_review(self, pk):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM book_review WHERE id=%s",
                [pk],
            )
            review = cursor.fetchone()
            if review is None:
                return None
            user_review = review[0]
        return user_review


class ReviewListView(APIView):
    """
    This API will return a list of all reviews belong to the user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT  r.id , r.rating , r.book_id ,b.title , b.author , b.genre
                FROM book_review as r
                LEFT JOIN book_book b ON b.id = r.book_id
                WHERE (user_id = %s);
                """,
                [user_id],
            )
            reviews = cursor.fetchall()

        reviews_list = [self.format_review(review) for review in reviews]

        return Response(reviews_list, status=status.HTTP_200_OK)

    def format_review(self, review):
        return {
            "id": review[0],
            "rating": review[1],
            "book_id": review[2],
            "title": review[3],
            "author": review[4],
            "genre": review[5],
        }


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


class BookSuggestView(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = ReviewAddSerializer
    list_services = ["genre", "author", "similar_user"]

    def get(self, request, *args, **kwargs):

        user_id = request.user.id

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM book_userrecommendationpreference WHERE user_id=%s",
                [user_id],
            )
            preference = cursor.fetchone()

        all_books = []
        recom_perf = {}
        if not preference:
            for service in self.list_services:
                num_items = 10
                service = BookRecommendationServiceFactory.create_service(service)
                books_list = service.get_recommended_books(user_id, num_items)
                recom_perf[service] = books_list
                all_books = all_books + books_list

        self.save_list_books(recom_perf, user_id)

        return Response(all_books)

    def save_list_books(self, recom_perf, user_id):
        each_day_seconds = 86400

        cache.set(
            f"RecommendationPreference_{user_id}",
            recom_perf,
            each_day_seconds * 3,
        )
