PROFILE_INDEX_MAPPING = {
    "settings": {"analysis": {"normalizer": {"lowercase": {"type": "custom", "filter": ["lowercase", "asciifolding"]}}}},
    "mappings": {"properties": {
        "id": {"type": "integer"},
        "full_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
        "current_job_title": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
        "current_company_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
        "industry": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
        "summary": {"type": "text"},
        "skills": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
        "location": {"properties": {"country": {"type": "keyword", "normalizer": "lowercase"}, "region": {"type": "keyword", "normalizer": "lowercase"}, "locality": {"type": "keyword", "normalizer": "lowercase"}}},
        "inferred_years_experience": {"type": "float"},
        "experience": {"type": "nested", "properties": {"title": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}}, "company_name": {"type": "text"}, "company_industry": {"type": "text"}, "summary": {"type": "text"}, "start_date": {"type": "date"}, "end_date": {"type": "date"}, "is_primary": {"type": "boolean"}, "location_names": {"type": "text"}}},
        "education": {"type": "nested", "properties": {"school_name": {"type": "text"}, "degrees": {"type": "text"}, "majors": {"type": "text"}, "minors": {"type": "text"}, "summary": {"type": "text"}, "start_date": {"type": "date"}, "end_date": {"type": "date"}}},
    }}
}

