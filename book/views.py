from django.core.cache import cache
from django.db import connection
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import (
    combine_dict_items,
    extract_values_list_dicts,
    get_keys_with_pattern,
    remove_duplicates,
)

from .models import Book, Review
from .serializers import BookSerializer, ReviewAddSerializer, ReviewUpdateSerializer
from .services import BookRecommendationServiceFactory


class BookListView(APIView):
    """
     This API view returns a list of all books along with the user's rating and the average rating of all users.

    Permissions:
    •  Only authenticated users can access this view.


    Methods:
    •  get: Handles GET requests to retrieve the list of books.


    get(request):
    Retrieves a list of all books with the following details:
    •  Book ID

    •  Title

    •  Author

    •  Genre

    •  User's rating for the book (if available)

    •  Average rating of the book from all users


    Parameters:
    •  request: The HTTP request object.


    Returns:
    •  Response: A JSON response containing the list of books with their details and ratings.

    •  HTTP 200 OK: If the request is successful.


    format_book(book):
    Formats the book data into a dictionary.

    Parameters:
    •  book: A tuple containing the book details and ratings.


    Returns:
    •  dict: A dictionary with the formatted book details.

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
    """
    This API view filters books based on the specified genre.

    Methods:
    •  get: Handles GET requests to retrieve the list of books filtered by genre.


    get(request, *args, **kwargs):
    Retrieves a list of books that match the specified genre.

    Parameters:
    •  request: The HTTP request object.

    •  args: Additional positional arguments.

    •  kwargs: Additional keyword arguments, including:

    •  genre: The genre to filter books by.


    Returns:
    •  Response: A JSON response containing the list of filtered books.

    •  HTTP 200 OK: If the request is successful.


    format_book(book):
    Formats the book data into a dictionary.

    Parameters:
    •  book: A tuple containing the book details.


    Returns:
    •  dict: A dictionary with the formatted book details.

    """

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
    This API view returns a list of distinct genres from the books.

    Methods:
    •  get: Handles GET requests to retrieve the list of genres.


    get(request, *args, **kwargs):
    Retrieves a list of distinct genres from the books.

    Parameters:
    •  request: The HTTP request object.

    •  args: Additional positional arguments.

    •  kwargs: Additional keyword arguments.


    Returns:
    •  Response: A JSON response containing the list of genres.

    •  HTTP 200 OK: If the request is successful.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT genre FROM book_book")
            genres = cursor.fetchall()

        # Flatten the list of tuples into a single list
        genre_list = [genre[0] for genre in genres]

        return Response(genre_list, status=status.HTTP_200_OK)


class BookDetailView(APIView):
    """
    This API view returns the details of a specific book based on its primary key (ID).

    Methods:
    •  get: Handles GET requests to retrieve the details of a book.


    get(request, pk):
    Retrieves the details of a book with the specified primary key (ID).

    Parameters:
    •  request: The HTTP request object.

    •  pk: The primary key (ID) of the book to retrieve.


    Returns:
    •  Response: A JSON response containing the book details if found.

    •  HTTP 200 OK: If the book is found.

    •  HTTP 404 Not Found: If the book is not found.

    """

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
    """
    This API view allows authenticated users to add a review for a book.

    Attributes:
    •  serializer_class: The serializer class used for validating the review data.

    •  permission_classes: The permission classes that restrict access to authenticated users only.


    Methods:
    •  post: Handles POST requests to add a new review.


    post(request):
    Adds a new review for a book.

    Parameters:
    •  request: The HTTP request object containing the review data.


    Returns:
    •  Response: A JSON response with a success message if the review is added successfully.

    •  HTTP 201 Created: If the review is added successfully.

    •  HTTP 400 Bad Request: If the review data is invalid.

    """

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

        # ----------------------------------------------------------------
        #  validate data with serializer
        # ----------------------------------------------------------------
        data = request.data.copy()
        data["user"] = request.user.id
        ser_data = self.serializer_class(data=data)

        if ser_data.is_valid():

            # ----------------------------------------------------------------
            #  check exist
            # ----------------------------------------------------------------
            user_review = self.get_user_review(pk)
            if user_review is None:
                return Response(
                    {"message": "Review not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ----------------------------------------------------------------
            #  check user permission manual
            # ----------------------------------------------------------------

            if user_review != requested_user_id:
                return Response(
                    {"message": "You do not have access to change this review"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ----------------------------------------------------------------
            #   update data
            # ----------------------------------------------------------------

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
    """
    This API view allows authenticated users to delete their review for a book.

    Attributes:
    •  permission_classes: The permission classes that restrict access to authenticated users only.


    Methods:
    •  delete: Handles DELETE requests to delete an existing review.

    •  get_user_review: Retrieves the user ID of the review's author.


    delete(request, *args, **kwargs):
    Deletes an existing review for a book.

    Parameters:
    •  request: The HTTP request object.

    •  args: Additional positional arguments.

    •  kwargs: Additional keyword arguments, including:

    •  pk: The primary key (ID) of the review to delete.


    Returns:
    •  Response: A JSON response with a success message if the review is deleted...
    """

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
    This API view returns a list of all reviews belonging to the authenticated user.

    Attributes:
    •  permission_classes: The permission classes that restrict access to authenticated users only.


    Methods:
    •  get: Handles GET requests to retrieve the list of reviews.

    •  format_review: Formats the review data into a dictionary.


    get(request):
    Retrieves a list of all reviews belonging to the authenticated user.

    Parameters:
    •  request: The HTTP request object.


    Returns:
    •  Response: A JSON response containing the list of reviews.

    •  HTTP 200 OK: If the request is successful.


    format_review(review):
    Formats the review data into a dictionary.

    Parameters:
    •  review: A tuple containing the review details.


    Returns:
    •  dict: A dictionary with the formatted review details.

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


class BookSuggestView(APIView):
    """
    This API view provides book suggestions for authenticated users based on their preferences and past reviews.

    Attributes:
    •  permission_classes: The permission classes that restrict access to authenticated users only.

    •  serializer_class: The serializer class used for validating the review data.

    •  list_services: A list of recommendation services used to fetch book suggestions.


    Methods:
    •  get: Handles GET requests to retrieve book suggestions.

    •  save_list_books: Saves the list of suggested books in the cache.

    •  get_list_books_from_cache: Retrieves the list of suggested books from the cache.

    •  fetch_books_from_service: Fetches book suggestions from a specified recommendation service.

    •  get_user_preference: Retrieves the user's preference data from the database.


    get(request, *args, **kwargs):
    Retrieves book suggestions for the authenticated user.

    Parameters:
    •  request: The HTTP request object.

    •  args: Additional positional arguments.

    •  kwargs: Additional keyword arguments.


    Returns:
    •  Response: A JSON response containing the list of suggested books.

    •  HTTP 200 OK: If the request is successful.

    •  HTTP 200 OK: If there is not enough data about the user to provide suggestions.


    save_list_books(recom_perf, user_id):
    Saves the list of suggested books in the cache.

    Parameters:
    •  recom_perf: A dictionary containing the recommended books.

    •  user_id: The ID of the user.


    get_list_books_from_cache(user_id):
    Retrieves the list of suggested books from the cache.

    Parameters:
    •  user_id: The ID of the user.


    Returns:
    •  list: A list of suggested books if found in the cache.

    •  None: If no suggested books are found in the cache.


    fetch_books_from_service(service_name, user_id, num_items=10):
    Fetches book suggestions from a specified recommendation service.

    Parameters:
    •  service_name: The name of the recommendation service.

    •  user_id: The ID of the user.

    •  num_items: The number of book suggestions to fetch (default is 10).


    Returns:
    •  list: A list of recommended books.


    get_user_preference(user_id):
    Retrieves the user's preference data from the database.

    Parameters:
    •  user_id: The ID of the user.


    Returns:
    •  dict: A dictionary containing the user's preference data if found.

    •  None: If no preference data is found.

    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReviewAddSerializer
    list_services = ["genre", "author", "similar_user"]

    def get(self, request, *args, **kwargs):
        user_id = request.user.id

        # ----------------------------------------------------------------
        # check if have not the review raise error
        # ----------------------------------------------------------------
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM book_review WHERE user_id = %s ;",
                [user_id],
            )
            count = cursor.fetchone()[0]

        if count == 0:
            return Response(
                {"error": "there is not enough data about you"},
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------------------
        # check items in the cache
        # ----------------------------------------------------------------

        cache_books = self.get_list_books_from_cache(user_id)
        if cache_books:
            unique_all_books = remove_duplicates(cache_books)
            return Response(unique_all_books)

        # ----------------------------------------------------------------
        # check user preference and return suggestion list according it
        # ----------------------------------------------------------------
        preference = self.get_user_preference(user_id)

        all_books = []
        recom_perf = {}
        if not preference:
            for service_name in self.list_services:
                books_list = self.fetch_books_from_service(service_name, user_id)
                recom_perf[service_name] = books_list
                all_books = all_books + books_list
        else:
            for service_name in self.list_services:
                num_items = int(preference[service_name] / 10)
                books_list = self.fetch_books_from_service(
                    service_name, user_id, num_items
                )
                recom_perf[service_name] = books_list
                all_books = all_books + books_list
        # ----------------------------------------------------------------
        # save the data of suggestion list in the cache
        # ----------------------------------------------------------------
        self.save_list_books(recom_perf, user_id)

        # ----------------------------------------------------------------
        # return unique items of books list
        # ----------------------------------------------------------------
        unique_all_books = remove_duplicates(all_books)
        return Response(unique_all_books, status=status.HTTP_200_OK)

    def save_list_books(self, recom_perf, user_id):
        each_day_seconds = 86400

        cache.set(
            f"RecommendationPreference_{user_id}",
            recom_perf,
            each_day_seconds * 3,
        )

    def get_list_books_from_cache(self, user_id):
        recom_perf = cache.get(f"RecommendationPreference_{user_id}")
        if recom_perf:
            book_list = combine_dict_items(recom_perf)
            return book_list
        return None

    def fetch_books_from_service(self, service_name, user_id, num_items=10):
        service = BookRecommendationServiceFactory.create_service(service_name)
        books_list = service.get_recommended_books(user_id, num_items)

        return books_list

    def get_user_preference(self, user_id):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM book_userrecommendationpreference WHERE user_id=%s",
                [user_id],
            )
            preference = cursor.fetchone()

        if preference:
            formatted_preference = {
                "id": preference[0],
                "genre": preference[1],
                "author": preference[2],
                "similar_user": preference[3],
                "user_id": preference[4],
            }
            return formatted_preference
        return None
