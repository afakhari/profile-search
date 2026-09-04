from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from elasticsearch import Elasticsearch
from rest_framework import permissions, serializers, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

REFRESH_COOKIE = "profile_refresh"

AccessResponse = inline_serializer("AccessResponse", {"access": serializers.CharField()})
MeResponse = inline_serializer("MeResponse", {"id": serializers.IntegerField(), "username": serializers.CharField()})
HealthResponse = inline_serializer(
    "HealthResponse",
    {"status": serializers.CharField(), "services": serializers.DictField(child=serializers.CharField())},
)

class LoginThrottle(throttling.AnonRateThrottle):
    scope = "login"

class CookieLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]
    @extend_schema(request=TokenObtainPairSerializer, responses=AccessResponse)
    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        response = Response({"access": tokens["access"]})
        response.set_cookie(REFRESH_COOKIE, tokens["refresh"], httponly=True, secure=not settings.DEBUG, samesite="Lax", max_age=86400)
        return response

class CookieRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses=AccessResponse)
    def post(self, request):
        refresh = request.COOKIES.get(REFRESH_COOKIE)
        if not refresh:
            return Response({"error": {"code": "missing_refresh_token", "message": "نشست شما منقضی شده است؛ دوباره وارد شوید."}}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)
        response = Response({"access": serializer.validated_data["access"]})
        if "refresh" in serializer.validated_data:
            response.set_cookie(REFRESH_COOKIE, serializer.validated_data["refresh"], httponly=True, secure=not settings.DEBUG, samesite="Lax", max_age=86400)
        return response

class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE)
        return response

class MeView(APIView):
    @extend_schema(responses=MeResponse)
    def get(self, request):
        return Response({"id": request.user.id, "username": request.user.username})

class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(auth=[], responses=HealthResponse)
    def get(self, request):
        services = {"database": "ok", "search": "ok"}
        try:
            connection.ensure_connection()
        except Exception:
            services["database"] = "error"
        try:
            if not Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=2).ping():
                services["search"] = "error"
        except Exception:
            services["search"] = "error"
        overall = "ok" if all(v == "ok" for v in services.values()) else "degraded"
        return Response({"status": overall, "services": services}, status=200 if overall == "ok" else 503)
