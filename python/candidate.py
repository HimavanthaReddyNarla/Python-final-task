"""Candidate data operations and input validation."""

import re
from typing import Any

from database import execute, query_all


def normalize_skills(skills: str) -> str:
    return ", ".join(dict.fromkeys(
        skill.strip().lower() for skill in skills.split(",") if skill.strip()
    ))


def validate_candidate(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    skills = normalize_skills(str(data.get("skills", "")))
    location = str(data.get("location", "")).strip()
    try:
        experience = float(data.get("experience_years", 0))
    except (TypeError, ValueError) as error:
        raise ValueError("Experience must be a number.") from error
    if not name or not location or not skills:
        raise ValueError("Name, skills, and location are required.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Enter a valid email address.")
    if not phone or len(phone) > 30:
        raise ValueError("Enter a phone number of 1 to 30 characters.")
    if not 0 <= experience <= 99:
        raise ValueError("Experience must be between 0 and 99 years.")
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience": experience,
        "location": location,
    }


def register_candidate(candidate: dict[str, Any]) -> int:
    return execute(
        """INSERT INTO candidates
        (name, email, phone, skills, experience_years, location)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            candidate["name"], candidate["email"], candidate["phone"],
            candidate["skills"], candidate["experience"], candidate["location"],
        ),
    )


def get_candidates(search: str = "") -> list[dict[str, Any]]:
    value = search.strip()
    if not value:
        return query_all("SELECT * FROM candidates ORDER BY created_at DESC")
    term = f"%{value}%"
    return query_all(
        """SELECT * FROM candidates
        WHERE name LIKE %s OR email LIKE %s OR skills LIKE %s OR location LIKE %s
        ORDER BY created_at DESC""",
        (term, term, term, term),
    )
