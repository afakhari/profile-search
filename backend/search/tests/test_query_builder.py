from search.query_builder import ProfileSearchQueryBuilder, ProfileSearchRequest


def body(**kwargs):
    return ProfileSearchQueryBuilder(ProfileSearchRequest(**kwargs)).build()

def test_filters_are_in_bool_filter_and_pagination_is_bounded_upstream():
    result = body(q="security", country="Canada", page=2, page_size=20)
    assert result["from"] == 20
    assert {"term": {"location.country": "canada"}} in result["query"]["bool"]["filter"]

def test_skills_all_uses_must():
    filters = body(skills=["Python", "Django"], skills_mode="all")["query"]["bool"]["filter"]
    assert len(filters[0]["bool"]["must"]) == 2

def test_skills_any_uses_should_with_minimum_one():
    clause = body(skills=["Python", "Django"], skills_mode="any")["query"]["bool"]["filter"][0]["bool"]
    assert len(clause["should"]) == 2 and clause["minimum_should_match"] == 1

def test_exact_phrase_and_fuzzy_are_ordered_by_boost():
    should = body(q="Python")["query"]["bool"]["should"]
    assert should[0]["term"]["full_name.keyword"]["boost"] == 8
    assert should[-1]["multi_match"]["boost"] == .5
    prefix = next(item["multi_match"] for item in should if item.get("multi_match", {}).get("type") == "bool_prefix")
    assert prefix["boost"] > should[-1]["multi_match"]["boost"]
    assert any("nested" in item and item["nested"]["path"] == "experience" for item in should)
