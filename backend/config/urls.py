from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.views import CookieLoginView, CookieRefreshView, HealthView, LogoutView, MeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", CookieLoginView.as_view()),
    path("api/auth/refresh", CookieRefreshView.as_view()),
    path("api/auth/logout", LogoutView.as_view()),
    path("api/auth/me", MeView.as_view()),
    path("api/health", HealthView.as_view()),
    path("api/profiles/", include("profiles.urls")),
    path("api/search/", include("search.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

