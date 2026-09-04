import ast
import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from django.db import transaction
from django.utils.dateparse import parse_date

from profiles.models import Education, Experience, Profile, ProfileSkill, Skill

SOURCE_PATH = re.compile(r"^(?:[A-Za-z]:\\|/).+")
LIST_FIELDS = {"skills", "emails", "phone_numbers", "experience", "education", "languages", "certifications"}


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def safe_nested(value: Any, expected=list):
    if value in (None, ""):
        return expected()
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = ast.literal_eval(value)
    if not isinstance(parsed, expected):
        raise ValueError(f"expected {expected.__name__}")
    return parsed


def as_list(value: Any) -> list[str]:
    parsed = safe_nested(value) if isinstance(value, str) and value.lstrip().startswith(("[", "(")) else value
    if parsed in (None, ""):
        return []
    if isinstance(parsed, (list, tuple, set)):
        values = []
        for item in parsed:
            candidate = item.get("name") or item.get("address") if isinstance(item, dict) else item
            if normalize_text(candidate):
                values.append(normalize_text(candidate))
        return values
    return [item.strip() for item in str(parsed).split(",") if item.strip()]


def safe_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)[:10]
    if re.fullmatch(r"\d{4}", text):
        text += "-01-01"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text += "-01"
    return parse_date(text) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else None


def nested_value(value: Any, key: str = "name") -> str:
    return normalize_text(value.get(key)) if isinstance(value, dict) else normalize_text(value)


@dataclass
class ImportReport:
    source: str
    raw_rows: int = 0
    imported_rows: int = 0
    repaired_rows: int = 0
    rejected_rows: int = 0
    duplicate_rows: int = 0
    parse_warnings: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    rows: list[dict] = field(default_factory=list)

    def reject(self, row_number: int, reason: str):
        self.rejected_rows += 1
        self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1
        self.rows.append({"row_number": row_number, "status": "rejected", "reason": reason})

    def repaired(self, row_number: int, reasons: list[str]):
        self.repaired_rows += 1
        self.rows.append({"row_number": row_number, "status": "repaired", "repairs": reasons})


class ProfileImporter:
    aliases = {
        "linkedin_id": ["linkedin_id", "id"],
        "linkedin_url": ["linkedin_url", "linkedin_profile_url", "profile_url"],
        "full_name": ["full_name", "name"],
        "first_name": ["first_name"],
        "last_name": ["last_name"],
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.report = ImportReport(source=str(self.path))

    def run(self) -> ImportReport:
        for number, raw in self._rows():
            self.report.raw_rows += 1
            try:
                record, repairs = self._normalize(raw)
                if repairs:
                    self.report.repaired(number, repairs)
                created = self._upsert(record)
                self.report.imported_rows += 1
                if not created:
                    self.report.duplicate_rows += 1
            except (ValueError, SyntaxError, TypeError, KeyError) as exc:
                self.report.reject(number, type(exc).__name__ + ": " + str(exc)[:120])
        return self.report

    def _rows(self) -> Iterable[tuple[int, dict]]:
        if self.path.suffix.lower() == ".json":
            payload = json.loads(self.path.read_text(encoding="utf-8-sig"))
            for number, item in enumerate(payload if isinstance(payload, list) else payload.get("profiles", []), 1):
                yield number, item
            return

        with self.path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader)
            for number, row in enumerate(reader, 2):
                source_path_repaired = False
                if row == headers:
                    self.report.raw_rows += 1
                    self.report.reject(number, "repeated_header")
                    continue
                if len(row) == len(headers) + 1 and SOURCE_PATH.match(row[0] or ""):
                    row, source_path_repaired = row[1:], True
                if len(row) != len(headers):
                    self.report.raw_rows += 1
                    self.report.reject(number, f"column_count:{len(row)}_expected:{len(headers)}")
                    continue
                item = dict(zip(headers, row, strict=True))
                if source_path_repaired:
                    item["__source_path_repaired"] = True
                yield number, item

    def _pick(self, raw: dict, name: str, default=""):
        for key in self.aliases.get(name, [name]):
            if raw.get(key) not in (None, ""):
                return raw[key]
        return default

    def _semantic_layout(self, raw: dict) -> dict:
        values = [value for key, value in raw.items() if not key.startswith("__")]
        version_index = next(
            (index for index, value in enumerate(values) if "current_version" in str(value) and "status" in str(value)),
            None,
        )
        if version_index is None and ("experience" in raw or "education" in raw):
            return {
                "experience_index": 53,
                "experiences": safe_nested(raw.get("experience", [])),
                "educations": safe_nested(raw.get("education", [])),
                "social_profiles": [],
                "locations": [
                    {
                        "name": raw.get("location_name", ""),
                        "country": raw.get("location_country", ""),
                        "region": raw.get("location_region", ""),
                        "locality": raw.get("location_locality", ""),
                    }
                ],
                "countries": as_list(raw.get("location_country", "")),
                "skills": as_list(raw.get("skills", [])),
                "emails": safe_nested(raw.get("emails", [])),
                "phones": as_list(raw.get("phone_numbers", [])) or as_list(raw.get("mobile_phone", "")),
                "summary": normalize_text(raw.get("summary")),
                "years": normalize_text(raw.get("inferred_years_experience")),
            }
        if version_index is None or version_index < 14:
            raise ValueError("missing_semantic_anchor")
        experience_index = version_index - 5
        if experience_index < 12 or experience_index + 4 >= len(values):
            raise ValueError("invalid_semantic_layout")
        return {
            "experience_index": experience_index,
            "experiences": safe_nested(values[experience_index]),
            "educations": safe_nested(values[experience_index + 1]),
            "social_profiles": safe_nested(values[experience_index + 2]),
            "locations": safe_nested(values[experience_index - 1]),
            "countries": as_list(values[experience_index - 2]),
            "skills": as_list(values[experience_index - 5]),
            "emails": safe_nested(values[experience_index - 7]),
            "phones": as_list(values[experience_index - 8]),
            "summary": normalize_text(values[experience_index - 9]),
            "years": normalize_text(values[experience_index - 10]),
        }

    def _normalize(self, raw: dict) -> tuple[dict, list[str]]:
        repairs = ["removed_source_path_column"] if raw.pop("__source_path_repaired", False) else []
        semantic = self._semantic_layout(raw)
        experiences = semantic["experiences"]
        educations = semantic["educations"]
        if any(not isinstance(item, dict) for item in experiences + educations):
            raise ValueError("nested_items_must_be_objects")

        active = [item for item in experiences if item.get("is_primary") is True]
        if not active:
            active = [item for item in experiences if not item.get("end_date")]
        primary = max(active, key=lambda item: str(item.get("start_date") or ""), default=None)
        title = nested_value(primary.get("title")) if primary else ""
        company_data = primary.get("company") if primary else None
        company = nested_value(company_data or (primary or {}).get("company_name"))
        industry = nested_value(company_data, "industry") if isinstance(company_data, dict) else ""

        first = normalize_text(self._pick(raw, "first_name"))
        last = normalize_text(self._pick(raw, "last_name"))
        full_name = normalize_text(self._pick(raw, "full_name")) or f"{first} {last}".strip()
        if not full_name:
            raise ValueError("missing_identity")

        linkedin_profile = next(
            (
                item
                for item in semantic["social_profiles"]
                if isinstance(item, dict) and item.get("network") == "linkedin"
            ),
            {},
        )
        linkedin_url = normalize_text(linkedin_profile.get("url") or self._pick(raw, "linkedin_url")) or None
        if linkedin_url and "linkedin.com/" not in linkedin_url.casefold():
            raise ValueError("invalid_linkedin_url")
        if linkedin_url and not re.match(r"^https?://", linkedin_url, re.I):
            linkedin_url = "https://" + linkedin_url.lstrip("/")
            repairs.append("normalized_linkedin_url")
        linkedin_id = normalize_text(linkedin_profile.get("id") or self._pick(raw, "linkedin_id")) or None
        if not linkedin_id and not linkedin_url:
            linkedin_id = "generated:" + hashlib.sha256(
                f"{full_name}|{company}|{title}".lower().encode()
            ).hexdigest()[:32]
            repairs.append("generated_stable_identity")

        try:
            years = float(semantic["years"]) if semantic["years"] else None
        except ValueError:
            years = None
            repairs.append("discarded_invalid_experience_years")
        if years is not None and not 0 <= years <= 80:
            years = None
            repairs.append("discarded_implausible_experience_years")

        locations = [item for item in semantic["locations"] if isinstance(item, dict)]
        location = locations[0] if locations else {}
        country = normalize_text(location.get("country")) or next(iter(semantic["countries"]), "")
        email_items = semantic["emails"]
        emails = [item for item in email_items if isinstance(item, dict) and item.get("address")]
        emails.sort(key=lambda item: item.get("type") not in {"current_professional", "professional"})
        email_values = [normalize_text(item["address"]) for item in emails]
        email_values.extend(normalize_text(item) for item in email_items if isinstance(item, str) and normalize_text(item))
        if raw.get("primary_email") and normalize_text(raw["primary_email"]) not in email_values:
            email_values.insert(0, normalize_text(raw["primary_email"]))

        if semantic["experience_index"] != 53:
            repairs.append(f"semantic_column_realign:{semantic['experience_index']}")
        known = {key for keys in self.aliases.values() for key in keys} | LIST_FIELDS
        return (
            {
                "linkedin_id": linkedin_id,
                "linkedin_url": linkedin_url,
                "full_name": full_name,
                "first_name": first,
                "last_name": last,
                "gender": normalize_text(raw.get("gender")),
                "industry": industry,
                "summary": semantic["summary"],
                "current_job_title": title,
                "current_company_name": company,
                "location_name": normalize_text(location.get("name")),
                "location_country": country,
                "location_region": normalize_text(location.get("region")),
                "location_locality": normalize_text(location.get("locality")),
                "inferred_years_experience": years,
                "primary_email": next(iter(email_values), ""),
                "mobile_phone": next(iter(semantic["phones"]), ""),
                "emails_json": email_values,
                "phone_numbers_json": semantic["phones"],
                "skills": semantic["skills"],
                "experience": experiences,
                "education": educations,
                "extras": {key: value for key, value in raw.items() if key not in known},
                "raw_payload": raw,
            },
            repairs,
        )

    @transaction.atomic
    def _upsert(self, data: dict) -> bool:
        lookup = {"linkedin_id": data["linkedin_id"]} if data["linkedin_id"] else {"linkedin_url": data["linkedin_url"]}
        nested = {key: data.pop(key) for key in ("skills", "experience", "education")}
        profile, created = Profile.objects.update_or_create(**lookup, defaults=data)
        ProfileSkill.objects.filter(profile=profile).delete()
        for name in nested["skills"]:
            skill, _ = Skill.objects.get_or_create(normalized_name=name.casefold(), defaults={"name": name})
            ProfileSkill.objects.get_or_create(profile=profile, skill=skill)

        profile.experiences.all().delete()
        for item in nested["experience"]:
            company = item.get("company") if isinstance(item.get("company"), dict) else {}
            title = item.get("title") if isinstance(item.get("title"), dict) else {}
            Experience.objects.create(
                profile=profile,
                company_name=nested_value(company or item.get("company_name")),
                company_industry=nested_value(company, "industry") or normalize_text(item.get("company_industry")),
                title=nested_value(title or item.get("title")),
                role=nested_value(title, "role") or normalize_text(item.get("role")),
                sub_role=nested_value(title, "sub_role") or normalize_text(item.get("sub_role")),
                start_date=safe_date(item.get("start_date")),
                end_date=safe_date(item.get("end_date")),
                is_primary=bool(item.get("is_primary")),
                summary=normalize_text(item.get("summary")),
                location_names=as_list(item.get("location_names", [])),
                raw_payload=item,
            )

        profile.educations.all().delete()
        for item in nested["education"]:
            school = item.get("school") if isinstance(item.get("school"), dict) else {}
            Education.objects.create(
                profile=profile,
                school_name=nested_value(school or item.get("school_name")),
                degrees=as_list(item.get("degrees", [])),
                majors=as_list(item.get("majors", [])),
                minors=as_list(item.get("minors", [])),
                start_date=safe_date(item.get("start_date")),
                end_date=safe_date(item.get("end_date")),
                gpa=normalize_text(item.get("gpa")),
                summary=normalize_text(item.get("summary")),
                raw_payload=item,
            )
        return created
