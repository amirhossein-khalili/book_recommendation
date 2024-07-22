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

        elif service_type == "author":
            return AuthorBookRecommendationService()

        elif service_type == "similar_user":
            return SimilarUserBookRecommendationService()

        raise ValueError(f"Unknown service type: {service_type}")


class GenreBookRecommendationService(BookRecommendationService):

    def get_recommended_books(self, user_id, num_items):
        # Step 1: Fetch the favorite genres ranked by their average rating
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT book_book.genre, AVG(book_review.rating) as avg_rating
                FROM book_review
                JOIN book_book ON book_review.book_id = book_book.id
                WHERE book_review.user_id = %s
                GROUP BY book_book.genre
                ORDER BY avg_rating DESC;
                """,
                [user_id],
            )
            genres = cursor.fetchall()

        if not genres:
            return []

        # Prepare to collect books from the favorite genres
        genre_list = [genre[0] for genre in genres]
        genre_placeholders = ", ".join(["%s"] * len(genre_list))

        # Step 2: Fetch books from the favorite genres ordered by the ranked genres
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT book_book.*
                FROM book_book
                JOIN (
                    SELECT genre, AVG(rating) as avg_rating
                    FROM book_review
                    JOIN book_book ON book_review.book_id = book_book.id
                    WHERE book_review.user_id = %s
                    GROUP BY genre
                ) as ranked_genres
                ON book_book.genre = ranked_genres.genre
                WHERE book_book.genre IN ({genre_placeholders})
                ORDER BY ranked_genres.avg_rating DESC, book_book.genre, book_book.title
                LIMIT %s;
                """,
                (user_id, *genre_list, num_items),
            )
            books = cursor.fetchall()

        # Format the books data
        return [
            {"id": row[0], "title": row[1], "author": row[2], "genre": row[3]}
            for row in books
        ]


class AuthorBookRecommendationService(BookRecommendationService):

    def get_recommended_books(self, user_id, num_items):
        # Step 1: Fetch the favorite authors ranked by their average rating
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT book_book.author, AVG(book_review.rating) as avg_rating
                FROM book_review
                JOIN book_book ON book_review.book_id = book_book.id
                WHERE book_review.user_id = %s
                GROUP BY book_book.author
                ORDER BY avg_rating DESC;
                """,
                [user_id],
            )
            authors = cursor.fetchall()

        if not authors:
            return []

        # Prepare to collect books from the favorite authors
        author_list = [author[0] for author in authors]
        author_placeholders = ", ".join(["%s"] * len(author_list))

        # Step 2: Fetch books from the favorite authors ordered by the ranked authors
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT book_book.*
                FROM book_book
                JOIN (
                    SELECT author, AVG(rating) as avg_rating
                    FROM book_review
                    JOIN book_book ON book_review.book_id = book_book.id
                    WHERE book_review.user_id = %s
                    GROUP BY author
                ) as ranked_authors
                ON book_book.author = ranked_authors.author
                WHERE book_book.author IN ({author_placeholders})
                ORDER BY ranked_authors.avg_rating DESC, book_book.author, book_book.title
                LIMIT %s;
                """,
                (user_id, *author_list, num_items),
            )
            books = cursor.fetchall()

        # Format the books data
        return [
            {"id": row[0], "title": row[1], "author": row[2], "genre": row[3]}
            for row in books
        ]


class SimilarUserBookRecommendationService(BookRecommendationService):

    def get_recommended_books(self, user_id, num_items):
        # Step 1: Find users with similar ratings
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT br2.user_id, COUNT(*) AS similarity
                FROM book_review br1
                JOIN book_review br2 ON br1.book_id = br2.book_id AND br1.rating = br2.rating
                WHERE br1.user_id = %s AND br2.user_id != %s
                GROUP BY br2.user_id
                ORDER BY similarity DESC
                LIMIT 10;  -- Limiting to top 10 similar users for performance
                """,
                [user_id, user_id],
            )
            similar_users = cursor.fetchall()

        if not similar_users:
            return []

        similar_user_ids = [user[0] for user in similar_users]
        similar_user_placeholders = ", ".join(["%s"] * len(similar_user_ids))

        # Step 2: Find books rated highly by similar users that the current user has not read
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT bb.id, bb.title, bb.author, bb.genre, AVG(br.rating) as avg_rating
                FROM book_review br
                JOIN book_book bb ON br.book_id = bb.id
                WHERE br.user_id IN ({similar_user_placeholders})
                  AND br.rating >= 4  -- Considering highly rated books (rating 4 or 5)
                  AND bb.id NOT IN (
                      SELECT book_id FROM book_review WHERE user_id = %s
                  )
                GROUP BY bb.id, bb.title, bb.author, bb.genre
                ORDER BY avg_rating DESC
                LIMIT %s;
                """,
                (*similar_user_ids, user_id, num_items),
            )
            books = cursor.fetchall()

        # Format the books data
        return [
            {"id": row[0], "title": row[1], "author": row[2], "genre": row[3]}
            for row in books
        ]
