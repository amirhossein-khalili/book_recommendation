from abc import ABC, abstractmethod

from django.db import connection


class BookRecommendationService(ABC):
    @abstractmethod
    def get_recommended_books(self, user_id, num_items):
        pass


class BookRecommendationServiceFactory:
    @staticmethod
    def create_service(service_type):
        if service_type == "genre":
            return GenreBookRecommendationService()

        raise ValueError(f"Unknown service type: {service_type}")


class GenreBookRecommendationService(BookRecommendationService):

    def get_recommended_books(self, user_id, num_items):

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT book_book.genre, AVG(book_review.rating) as avg_rating
                FROM book_review
                JOIN book_book ON book_review.book_id = book_book.id
                WHERE book_review.user_id = %s
                GROUP BY book_book.genre
                ORDER BY avg_rating DESC
                """,
                [user_id],
            )
            genres = cursor.fetchall()

        if not genres:
            return []

        # Prepare to collect books from the favorite genres
        genre_list = [genre[0] for genre in genres]
        genre_placeholders = ", ".join(["%s"] * len(genre_list))

        with connection.cursor() as cursor:
            # Fetch books from the favorite genres
            cursor.execute(
                f"""
                SELECT * FROM book_book
                WHERE genre IN ({genre_placeholders})
                LIMIT %s
                 """,
                (*genre_list, num_items),
            )
            books = cursor.fetchall()

        # Format the books data
        return [
            {"id": row[0], "title": row[1], "author": row[2], "genre": row[3]}
            for row in books
        ]
