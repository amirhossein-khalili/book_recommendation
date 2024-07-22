from django.contrib import admin

from .models import Book, Review, UserRecommendationPreference


class BookAdmin(admin.ModelAdmin):
    pass


class ReviewAdmin(admin.ModelAdmin):
    pass


class UserRecommendationPreferenceAdmin(admin.ModelAdmin):
    pass


admin.site.register(Book, BookAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(UserRecommendationPreference, UserRecommendationPreferenceAdmin)
