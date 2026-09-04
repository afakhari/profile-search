import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from profiles.models import Profile

pytestmark = pytest.mark.django_db

@pytest.fixture
def client():
    user = get_user_model().objects.create_user("reviewer", password="test-password")
    api = APIClient()
    api.force_authenticate(user)
    return api

def test_profile_detail_does_not_expose_internal_payloads(client):
    profile = Profile.objects.create(linkedin_id="1", full_name="Ada", raw_payload={"private": "raw"}, extras={"unused": True})
    response = client.get(f"/api/profiles/{profile.id}")
    assert response.status_code == 200
    assert "raw_payload" not in response.json()
    assert "extras" not in response.json()

def test_search_validates_page_size(client):
    response = client.get("/api/profiles/search?page_size=999")
    assert response.status_code == 400

def test_search_rejects_pages_beyond_elasticsearch_result_window(client):
    response = client.get("/api/profiles/search?page=501&page_size=20")
    assert response.status_code == 400
