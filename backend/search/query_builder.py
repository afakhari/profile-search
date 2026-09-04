from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProfileSearchRequest:
    q: str = ""
    skills: list[str] = field(default_factory=list)
    skills_mode: str = "all"
    job_title: str = ""
    country: str = ""
    industry: str = ""
    min_experience: float | None = None
    max_experience: float | None = None
    sort: str = "relevance"
    page: int = 1
    page_size: int = 20

class ProfileSearchQueryBuilder:
    def __init__(self, request: ProfileSearchRequest):
        self.request = request

    def build(self) -> dict:
        r = self.request
        filters: list[dict] = []
        if r.skills:
            clauses = [{"term": {"skills.keyword": skill.lower()}} for skill in r.skills]
            filters.append({"bool": {"must" if r.skills_mode == "all" else "should": clauses, **({"minimum_should_match": 1} if r.skills_mode == "any" else {})}})
        if r.job_title:
            filters.append({"match_phrase": {"current_job_title": r.job_title}})
        if r.country:
            filters.append({"term": {"location.country": r.country.lower()}})
        if r.industry:
            filters.append({"term": {"industry.keyword": r.industry.lower()}})
        if r.min_experience is not None or r.max_experience is not None:
            bounds = {k: v for k, v in (("gte", r.min_experience), ("lte", r.max_experience)) if v is not None}
            filters.append({"range": {"inferred_years_experience": bounds}})

        if r.q:
            q = r.q.strip()
            should = [
                {"term": {"full_name.keyword": {"value": q.lower(), "boost": 8}}},
                {"term": {"skills.keyword": {"value": q.lower(), "boost": 7}}},
                {"match_phrase": {"current_job_title": {"query": q, "boost": 6}}},
                {"match_phrase": {"current_company_name": {"query": q, "boost": 4}}},
                {"multi_match": {"query": q, "fields": ["full_name^5", "current_job_title^5", "skills^5", "current_company_name^3", "industry^2", "summary"], "type": "best_fields"}},
                {"nested": {"path": "experience", "query": {"multi_match": {"query": q, "fields": ["experience.title^4", "experience.company_name^3", "experience.summary"]}}, "inner_hits": {"name": "matched_experience", "size": 2}}},
                {"nested": {"path": "education", "query": {"multi_match": {"query": q, "fields": ["education.school_name^2", "education.degrees^2", "education.majors^2", "education.summary"]}}, "inner_hits": {"name": "matched_education", "size": 2}}},
                {"multi_match": {"query": q, "fields": ["full_name^3", "current_job_title^3", "skills^4", "current_company_name^2"], "type": "bool_prefix", "boost": 0.8}},
                {"multi_match": {"query": q, "fields": ["full_name^3", "current_job_title^3", "skills^4", "summary"], "fuzziness": "AUTO", "prefix_length": 1, "boost": 0.5}},
            ]
            query = {"bool": {"should": should, "minimum_should_match": 1, "filter": filters}}
        else:
            query = {"bool": {"must": [{"match_all": {}}], "filter": filters}}

        sort = {"experience_desc": [{"inferred_years_experience": "desc"}], "experience_asc": [{"inferred_years_experience": "asc"}]}.get(r.sort, ["_score"] if r.q else [{"full_name.keyword": "asc"}])
        return {
            "query": query, "from": (r.page - 1) * r.page_size, "size": r.page_size, "sort": sort,
            "track_total_hits": True,
            "highlight": {"pre_tags": ["[[H]]"], "post_tags": ["[[/H]]"], "fields": {"summary": {"fragment_size": 180}, "current_job_title": {}, "skills": {}}},
            "aggs": {"skills": {"terms": {"field": "skills.keyword", "size": 20}}, "countries": {"terms": {"field": "location.country", "size": 20}}, "industries": {"terms": {"field": "industry.keyword", "size": 20}}, "job_titles": {"terms": {"field": "current_job_title.keyword", "size": 20}}},
        }
