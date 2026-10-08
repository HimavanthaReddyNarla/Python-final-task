"""Job posting, searching, and profile-based recommendation."""

from typing import Any

from database import execute, query_all


def post_job(data: dict[str, Any]) -> int:
    try:
        company_id = int(data.get("company_id", ""))
        experience = float(data.get("experience_required", 0))
        salary = float(data.get("salary", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("Choose a company and enter valid experience and salary amounts.") from error
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    skills = ", ".join(dict.fromkeys(
        value.strip().lower()
        for value in str(data.get("skills", "")).split(",")
        if value.strip()
    ))
    location = str(data.get("location", "")).strip()
    if not all((title, description, skills, location)):
        raise ValueError("Title, description, skills, and location are required.")
    if not 0 <= experience <= 99 or salary < 0:
        raise ValueError("Experience and salary must be non-negative; experience cannot exceed 99.")
    return execute(
        """INSERT INTO jobs
        (company_id, title, description, skills, experience_required, location, salary)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (company_id, title, description, skills, experience, location, salary),
    )


def get_jobs(search: str = "", open_only: bool = False) -> list[dict[str, Any]]:
    term = f"%{search.strip()}%"
    open_clause = "AND j.status = 'Open'" if open_only else ""
    return query_all(
        f"""SELECT j.*, c.name AS company_name FROM jobs j
        JOIN companies c ON c.id = j.company_id
        WHERE (j.title LIKE %s OR j.skills LIKE %s OR j.location LIKE %s
               OR c.name LIKE %s) {open_clause}
        ORDER BY j.created_at DESC""",
        (term, term, term, term),
    )


def recommend_jobs(skills: str, experience: float, location: str) -> list[dict[str, Any]]:
    """Rank open jobs by skill overlap, experience fit, and location match."""
    wanted_skills = {
        item.strip().lower() for item in skills.split(",") if item.strip()
    }
    if not wanted_skills:
        raise ValueError("Enter at least one skill to get recommendations.")
    jobs = get_jobs(open_only=True)
    recommendations: list[dict[str, Any]] = []
    for job in jobs:
        job_skills = {
            item.strip().lower() for item in job["skills"].split(",") if item.strip()
        }
        overlap = wanted_skills & job_skills
        if not overlap or experience < float(job["experience_required"]):
            continue
        score = (len(overlap) / len(wanted_skills)) * 70
        score += 20 if location.strip().casefold() == job["location"].casefold() else 0
        score += 10 if experience >= float(job["experience_required"]) else 0
        job["matched_skills"] = sorted(overlap)
        job["match_score"] = round(score)
        recommendations.append(job)
    return sorted(recommendations, key=lambda item: item["match_score"], reverse=True)
