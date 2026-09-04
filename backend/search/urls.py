from django.urls import path

from .views import SuggestionsView

urlpatterns = [path("suggestions", SuggestionsView.as_view())]

