from django.conf import settings
from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    genre = models.CharField(max_length=50)

    class Meta:
        unique_together = ("title", "author", "genre")

    def __str__(self):
        return f"{self.title} by {self.author}"


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()

    class Meta:
        unique_together = ("book_id", "user_id")
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="rating_range",
            )
        ]

    def __str__(self):
        return f"Review of {self.book_id} by {self.user_id}: {self.rating}"


class UserRecommendationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    genre_weight = models.FloatField(default=0)
    author_weight = models.FloatField(default=0)
    similar_user_weight = models.FloatField(default=0)

    def __str__(self):
        return f"Preferences for {self.user.user_name}"
