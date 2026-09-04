from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=160)
    normalized_name = models.CharField(max_length=160, unique=True, db_index=True)
    class Meta:
        ordering = ["normalized_name"]
    def __str__(self):
        return self.name

class Profile(models.Model):
    linkedin_id = models.CharField(max_length=160, unique=True, null=True, blank=True, db_index=True)
    linkedin_url = models.URLField(max_length=500, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=300, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=40, blank=True)
    industry = models.CharField(max_length=250, blank=True, db_index=True)
    summary = models.TextField(blank=True)
    current_job_title = models.CharField(max_length=300, blank=True, db_index=True)
    current_company_name = models.CharField(max_length=300, blank=True)
    location_name = models.CharField(max_length=300, blank=True)
    location_country = models.CharField(max_length=150, blank=True, db_index=True)
    location_region = models.CharField(max_length=150, blank=True)
    location_locality = models.CharField(max_length=150, blank=True)
    inferred_years_experience = models.FloatField(null=True, blank=True, db_index=True)
    primary_email = models.EmailField(blank=True)
    mobile_phone = models.CharField(max_length=80, blank=True)
    emails_json = models.JSONField(default=list, blank=True)
    phone_numbers_json = models.JSONField(default=list, blank=True)
    extras = models.JSONField(default=dict, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    skills = models.ManyToManyField(Skill, through="ProfileSkill", related_name="profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProfileSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "skill"], name="unique_profile_skill")]

class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="experiences")
    company_name = models.CharField(max_length=300, blank=True)
    company_industry = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=300, blank=True)
    role = models.CharField(max_length=200, blank=True)
    sub_role = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    summary = models.TextField(blank=True)
    location_names = models.JSONField(default=list, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    class Meta:
        ordering = ["-is_primary", "-start_date"]

class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="educations")
    school_name = models.CharField(max_length=300, blank=True)
    degrees = models.JSONField(default=list, blank=True)
    majors = models.JSONField(default=list, blank=True)
    minors = models.JSONField(default=list, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    gpa = models.CharField(max_length=40, blank=True)
    summary = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    class Meta:
        ordering = ["-end_date"]
