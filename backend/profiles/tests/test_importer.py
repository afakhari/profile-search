import json

import pytest

from profiles.models import Profile
from profiles.services.importer import ProfileImporter, safe_nested

pytestmark = pytest.mark.django_db

def test_safe_nested_never_uses_eval():
    assert safe_nested("[{'name': 'Python'}]") == [{"name": "Python"}]
    with pytest.raises((ValueError, SyntaxError)):
        safe_nested("__import__('os').system('unsafe')")

def test_import_is_idempotent_and_recovers_primary_job(tmp_path):
    source = tmp_path / "profiles.json"
    source.write_text(json.dumps([{"full_name": "Test Person", "skills": ["Python"], "experience": [{"title": "Engineer", "company_name": "Acme", "is_primary": True}]}]), encoding="utf-8")
    first = ProfileImporter(source).run()
    second = ProfileImporter(source).run()
    assert first.imported_rows == second.imported_rows == 1
    assert Profile.objects.count() == 1
    assert second.duplicate_rows == 1
    assert Profile.objects.get().current_job_title == "Engineer"

def test_malformed_nested_row_is_quarantined(tmp_path):
    source = tmp_path / "profiles.json"
    source.write_text(json.dumps([{"full_name": "Bad", "experience": "not valid"}]), encoding="utf-8")
    report = ProfileImporter(source).run()
    assert report.rejected_rows == 1
    assert Profile.objects.count() == 0


def test_semantic_realign_recovers_shifted_real_dataset_shape():
    keys = ["full_name", "first_name", "last_name", "gender", "linkedin_url", "linkedin_username", "linkedin_id"]
    keys.extend(f"column_{index}" for index in range(7, 58))
    values = [""] * 58
    values[0:7] = ["Ada Example", "Ada", "Example", "female", "linkedin.com/in/ada", "ada", "42"]
    values[42] = "9.0"
    values[43] = "Security engineering"
    values[44] = "['+10000000000']"
    values[45] = "[{'address': 'ada@example.test', 'type': 'professional'}]"
    values[47] = "['Python', 'Elasticsearch']"
    values[50] = "['canada']"
    values[51] = "[{'name': 'Toronto, Canada', 'country': 'canada', 'region': 'ontario'}]"
    values[52] = "[{'company': {'name': 'Acme', 'industry': 'security'}, 'title': {'name': 'Security Engineer', 'role': 'engineering'}, 'is_primary': True}]"
    values[53] = "[{'school': {'name': 'Example University'}, 'degrees': ['MSc']}]"
    values[54] = "[{'network': 'linkedin', 'id': '42', 'url': 'linkedin.com/in/ada'}]"
    values[55] = "[]"
    values[56] = "[]"
    values[57] = "{'status': 'updated', 'current_version': '13.0'}"

    record, repairs = ProfileImporter("unused.csv")._normalize(dict(zip(keys, values, strict=True)))

    assert record["current_job_title"] == "Security Engineer"
    assert record["current_company_name"] == "Acme"
    assert record["industry"] == "security"
    assert record["skills"] == ["Python", "Elasticsearch"]
    assert record["location_country"] == "canada"
    assert record["primary_email"] == "ada@example.test"
    assert "semantic_column_realign:52" in repairs
