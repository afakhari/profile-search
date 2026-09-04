from rest_framework import serializers

from .query_builder import ProfileSearchRequest


class ProfileSearchParamsSerializer(serializers.Serializer):
    max_result_window = 10_000
    q = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    skills = serializers.CharField(required=False, allow_blank=True, default="")
    skills_mode = serializers.ChoiceField(choices=["all", "any"], default="all")
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    country = serializers.CharField(required=False, allow_blank=True, max_length=120, default="")
    industry = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    min_experience = serializers.FloatField(required=False, min_value=0, max_value=80)
    max_experience = serializers.FloatField(required=False, min_value=0, max_value=80)
    sort = serializers.ChoiceField(choices=["relevance", "experience_desc", "experience_asc"], default="relevance")
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=50, default=20)
    def validate(self, attrs):
        if attrs.get("min_experience") is not None and attrs.get("max_experience") is not None and attrs["min_experience"] > attrs["max_experience"]:
            raise serializers.ValidationError("حداقل سابقه نمی‌تواند از حداکثر سابقه بیشتر باشد.")
        page = attrs.get("page", 1)
        page_size = attrs.get("page_size", 20)
        if page * page_size > self.max_result_window:
            raise serializers.ValidationError({"page": "صفحهٔ درخواستی خارج از محدودهٔ نتایج است."})
        return attrs
    def to_request(self):
        data = self.validated_data.copy()
        data["skills"] = [x.strip() for x in data.pop("skills", "").split(",") if x.strip()][:20]
        return ProfileSearchRequest(**data)


class MatchReasonSerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()


class HighlightSerializer(serializers.Serializer):
    field = serializers.CharField()
    text = serializers.CharField()


class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    current_job_title = serializers.CharField()
    current_company_name = serializers.CharField()
    location = serializers.DictField(child=serializers.CharField())
    inferred_years_experience = serializers.FloatField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField())
    match_reasons = MatchReasonSerializer(many=True)
    highlights = HighlightSerializer(many=True)
    score = serializers.FloatField(allow_null=True)


class FacetBucketSerializer(serializers.Serializer):
    value = serializers.CharField()
    count = serializers.IntegerField()


class SearchResponseSerializer(serializers.Serializer):
    meta = serializers.DictField()
    results = SearchResultSerializer(many=True)
    facets = serializers.DictField(child=serializers.ListField(child=FacetBucketSerializer()))


class SuggestionsResponseSerializer(serializers.Serializer):
    suggestions = serializers.ListField(child=serializers.CharField())
