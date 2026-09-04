from django.urls import path

from search.views import ProfileSearchView

from .views import ProfileDetailView

urlpatterns = [path("search", ProfileSearchView.as_view()), path("<int:pk>", ProfileDetailView.as_view())]
