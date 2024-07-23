from celery import shared_task
from django.core.cache import cache
from django.db import connection
from django_redis import get_redis_connection

from utils import get_keys_with_pattern

# from .models import Recommendation, UserBookRating, UserRecommendationPreference


@shared_task
def update_recommendation_weights():
    pattern = "*RecommendationPreference_*"
    redis_keys = get_keys_with_pattern(pattern)

    for redis_key in redis_keys:
        cleaned_key = redis_key.decode("utf-8")
        key = cleaned_key.strip(":1:")
        user_id = key.strip("RecommendationPreference_")

        data = cache.get(key)

        if data:
            genre_count = 0
            author_count = 0
            similar_user_count = 0

            for service_name in data:

                list_book_ids = extract_values_list_dicts(data[service_name], "id")
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM book_review WHERE book_id = ANY(%s) AND user_id = %s;",
                        [list_book_ids, user_id],
                    )
                    count = cursor.fetchone()[0]

                if service_name == "genre":
                    genre_count += count
                elif service_name == "author":
                    author_count += count
                elif service_name == "similar_user":
                    similar_user_count += count

                total_count = genre_count + author_count + similar_user_count

                if total_count > 0:
                    genre_weight = (genre_count / total_count) * 100
                    author_weight = (author_count / total_count) * 100
                    similar_user_weight = (similar_user_count / total_count) * 100

                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT COUNT(*) FROM book_userrecommendationpreference WHERE user_id = %s ;",
                            [user_id],
                        )
                        count = cursor.fetchone()[0]

                    if count == 1:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                UPDATE book_userrecommendationpreference
                                SET genre_weight = %s,
                                author_weight = %s,
                                similar_user_weight =  %s
                                WHERE user_id =  %s;
                                """,
                                [
                                    genre_weight,
                                    author_weight,
                                    similar_user_weight,
                                    user_id,
                                ],
                            )

                    elif count == 0:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO book_userrecommendationpreference 
                                (genre_weight ,author_weight ,similar_user_weight , user_id)
                                VALUES (%s , %s , %s , %s );
                                """,
                                [
                                    genre_weight,
                                    author_weight,
                                    similar_user_weight,
                                    user_id,
                                ],
                            )
