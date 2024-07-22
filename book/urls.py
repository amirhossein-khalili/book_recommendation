from django.urls import include, path

from . import views

app_name = "book"


# ----------------------------------------------------------------
# -------------------     BOOK PART OF URLS         --------------
# ----------------------------------------------------------------
book_urls = [
    path("list/", views.BookListView.as_view(), name="book-list"),
    path("genre/", views.BookGenreListView.as_view(), name="book-list-genre"),
    path("genre/<str:genre>/", views.BookFilterView.as_view(), name="book-filter"),
]

# ----------------------------------------------------------------
# -------------------     REVIEW PART OF URLS         ------------
# ----------------------------------------------------------------
review_urls = [
    path("add/", views.ReviewAddView.as_view(), name="review-add"),
    path("update/<int:pk>/", views.ReviewUpdateView.as_view(), name="review-update"),
    path("delete/<int:pk>/", views.ReviewDeleteView.as_view(), name="review-delete"),
    path("list/", views.ReviewListView.as_view(), name="review-list"),
]

urlpatterns = [
    path("book/", include(book_urls)),
    path("review/", include(review_urls)),
    path("suggest/", views.BookSuggestView.as_view(), name="book-suggest"),
]
