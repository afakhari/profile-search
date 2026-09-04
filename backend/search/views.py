from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.models import Profile, Skill

from .serializers import ProfileSearchParamsSerializer, SearchResponseSerializer, SuggestionsResponseSerializer
from .service import ProfileSearchService, SearchUnavailable


class ProfileSearchView(APIView):
    @extend_schema(parameters=[ProfileSearchParamsSerializer], responses=SearchResponseSerializer)
    def get(self, request):
        params = ProfileSearchParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        try:
            return Response(ProfileSearchService().search(params.to_request()))
        except SearchUnavailable:
            return Response({"error": {"code": "search_unavailable", "message": "سرویس جست‌وجو موقتاً در دسترس نیست."}}, status=503)

class SuggestionsView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter("type", str, enum=["skill", "job_title"]),
            OpenApiParameter("q", str, description="At least two characters"),
        ],
        responses=SuggestionsResponseSerializer,
    )
    def get(self, request):
        kind, query = request.query_params.get("type", "skill"), request.query_params.get("q", "").strip()
        if kind not in {"skill", "job_title"} or len(query) < 2:
            return Response({"suggestions": []})
        if kind == "skill":
            values = Skill.objects.filter(normalized_name__icontains=query.lower()).values_list("name", flat=True)[:10]
        else:
            values = Profile.objects.filter(Q(current_job_title__icontains=query)).exclude(current_job_title="").values_list("current_job_title", flat=True).distinct()[:10]
        return Response({"suggestions": list(values)})
