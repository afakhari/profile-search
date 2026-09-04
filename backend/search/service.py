import time

from django.conf import settings
from elasticsearch import Elasticsearch

from .query_builder import ProfileSearchQueryBuilder, ProfileSearchRequest


class SearchUnavailable(Exception):
    pass

class ProfileSearchService:
    def __init__(self, client=None):
        self.client = client or Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=5)
    def search(self, request: ProfileSearchRequest) -> dict:
        started = time.perf_counter()
        try:
            response = self.client.search(index=settings.ELASTICSEARCH_INDEX, body=ProfileSearchQueryBuilder(request).build())
        except Exception as exc:
            raise SearchUnavailable("سرویس جست‌وجو موقتاً در دسترس نیست.") from exc
        hits = response["hits"]["hits"]
        results = [self._format_hit(hit) for hit in hits]
        facets = {name: [{"value": b["key"], "count": b["doc_count"]} for b in value["buckets"]] for name, value in response.get("aggregations", {}).items()}
        took = response.get("took", round((time.perf_counter() - started) * 1000))
        return {"meta": {"total": response["hits"]["total"]["value"], "page": request.page, "page_size": request.page_size, "sort": request.sort, "took_ms": took}, "results": results, "facets": facets}

    def _format_hit(self, hit):
        source = hit["_source"]
        reasons = []
        highlights = [{"field": key, "text": text} for key, values in hit.get("highlight", {}).items() for text in values]
        highlighted = {x["field"] for x in highlights}
        labels = {"current_job_title": "عنوان شغلی فعلی", "skills": "مهارت", "summary": "خلاصهٔ حرفه‌ای"}
        reasons.extend({"type": field, "label": labels[field]} for field in highlighted if field in labels)
        for key, value in hit.get("inner_hits", {}).items():
            if value["hits"]["hits"]:
                item = value["hits"]["hits"][0]["_source"]
                matched_item = item.get("title") or item.get("school_name") or "تطبیق در سوابق"
                reasons.append({"type": key, "label": f"{matched_item} · {item.get('company_name', '')}".strip(" ·")})
        return {"id": source["id"], "full_name": source["full_name"], "current_job_title": source.get("current_job_title", ""), "current_company_name": source.get("current_company_name", ""), "location": source.get("location", {}), "inferred_years_experience": source.get("inferred_years_experience"), "skills": source.get("skills", []), "match_reasons": reasons, "highlights": highlights, "score": hit.get("_score")}
