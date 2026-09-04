from rest_framework import serializers

from .models import Education, Experience, Profile, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["name"]

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        exclude = ["profile", "raw_payload"]

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        exclude = ["profile", "raw_payload"]

class ProfileDetailSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    location = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        exclude = ["raw_payload", "emails_json", "phone_numbers_json", "extras"]
    def get_location(self, obj) -> dict[str, str]:
        return {"name": obj.location_name, "country": obj.location_country, "region": obj.location_region, "locality": obj.location_locality}
