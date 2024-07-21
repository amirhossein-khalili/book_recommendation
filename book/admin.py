from django.contrib import admin

from .models import Book, Review


class BookAdmin(admin.ModelAdmin):
    pass


class ReviewAdmin(admin.ModelAdmin):
    pass


admin.site.register(Book, BookAdmin)
admin.site.register(Review, ReviewAdmin)
