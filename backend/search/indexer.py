from django.conf import settings
from elasticsearch import Elasticsearch, helpers

from profiles.models import Profile

from .mappings import PROFILE_INDEX_MAPPING


def profile_document(profile: Profile) -> dict:
    return {"id": profile.id, "full_name": profile.full_name, "current_job_title": profile.current_job_title,
            "current_company_name": profile.current_company_name, "industry": profile.industry, "summary": profile.summary,
            "skills": [s.name for s in profile.skills.all()], "location": {"country": profile.location_country, "region": profile.location_region, "locality": profile.location_locality},
            "inferred_years_experience": profile.inferred_years_experience,
            "experience": [{"title": x.title, "company_name": x.company_name, "company_industry": x.company_industry, "summary": x.summary, "start_date": x.start_date, "end_date": x.end_date, "is_primary": x.is_primary, "location_names": x.location_names} for x in profile.experiences.all()],
            "education": [{"school_name": x.school_name, "degrees": x.degrees, "majors": x.majors, "minors": x.minors, "summary": x.summary, "start_date": x.start_date, "end_date": x.end_date} for x in profile.educations.all()]}

def rebuild_index() -> int:
    client = Elasticsearch(settings.ELASTICSEARCH_URL)
    index = settings.ELASTICSEARCH_INDEX
    client.indices.delete(index=index, ignore_unavailable=True)
    client.indices.create(index=index, **PROFILE_INDEX_MAPPING)
    profiles = Profile.objects.prefetch_related("skills", "experiences", "educations").iterator(chunk_size=250)
    count, _ = helpers.bulk(client, ({"_index": index, "_id": p.id, "_source": profile_document(p)} for p in profiles), chunk_size=250)
    client.indices.refresh(index=index)
    return count

