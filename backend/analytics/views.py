import logging

from django.conf import settings
from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema, inline_serializer
from elasticsearch import Elasticsearch
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.models import Profile, Skill

logger = logging.getLogger(__name__)

class OverviewView(APIView):
    @extend_schema(
        responses=inline_serializer(
            "AnalyticsOverviewResponse",
            {"kpis": serializers.DictField(), "charts": serializers.DictField()},
        )
    )
    def get(self, request):
        base = Profile.objects.aggregate(total=Count("id"), countries=Count("location_country", distinct=True), average_experience=Avg("inferred_years_experience"))
        charts = {"top_skills": [], "top_industries": [], "top_job_roles": [], "experience_distribution": []}
        try:
            result = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=5).search(index=settings.ELASTICSEARCH_INDEX, size=0, aggs={
                "top_skills": {"terms": {"field": "skills.keyword", "size": 10}}, "top_industries": {"terms": {"field": "industry.keyword", "size": 8}},
                "top_job_roles": {"terms": {"field": "current_job_title.keyword", "size": 8}}, "experience_distribution": {"histogram": {"field": "inferred_years_experience", "interval": 5, "min_doc_count": 1}}})
            charts = {k: [{"label": str(b["key"]), "count": b["doc_count"]} for b in v["buckets"]] for k, v in result["aggregations"].items()}
        except Exception:
            logger.exception("Failed to load Elasticsearch analytics; returning empty charts")
        return Response({"kpis": {**base, "unique_skills": Skill.objects.count()}, "charts": charts})
