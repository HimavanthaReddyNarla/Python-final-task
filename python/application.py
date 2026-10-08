"""Job application and interview scheduling operations."""

from typing import Any

from database import execute, query_all

APPLICATION_STATUSES = ("Applied", "Shortlisted", "Selected", "Rejected")


def get_applications() -> list[dict[str, Any]]:
    return query_all(
        """SELECT a.id, a.status, a.applied_at, c.name AS candidate_name,
        c.email AS candidate_email, j.title AS job_title, co.name AS company_name
        FROM applications a
        JOIN candidates c ON c.id = a.candidate_id
        JOIN jobs j ON j.id = a.job_id
        JOIN companies co ON co.id = j.company_id
        ORDER BY a.applied_at DESC"""
    )


def apply_for_job(candidate_id: Any, job_id: Any) -> int:
    try:
        candidate_key = int(candidate_id)
        job_key = int(job_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Select a valid candidate and job.") from error
    return execute(
        "INSERT INTO applications (candidate_id, job_id) VALUES (%s, %s)",
        (candidate_key, job_key),
    )


def update_application_status(application_id: Any, status: str) -> None:
    try:
        application_key = int(application_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Select a valid application.") from error
    if status not in APPLICATION_STATUSES:
        raise ValueError("Select one of the available application statuses.")
    execute(
        "UPDATE applications SET status = %s WHERE id = %s",
        (status, application_key),
    )


def delete_application(application_id: Any) -> None:
    try:
        application_key = int(application_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Select a valid application.") from error
    execute("DELETE FROM applications WHERE id = %s", (application_key,))


def schedule_interview(data: dict[str, Any]) -> int:
    try:
        application_id = int(data.get("application_id", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("Select an application for this interview.") from error
    interview_at = str(data.get("interview_at", "")).strip().replace("T", " ")
    mode = str(data.get("mode", "")).strip()
    notes = str(data.get("notes", "")).strip()
    if not interview_at or not mode:
        raise ValueError("Interview date/time and mode are required.")
    return execute(
        """INSERT INTO interviews (application_id, interview_at, mode, notes)
        VALUES (%s, %s, %s, %s)""",
        (application_id, interview_at, mode, notes or None),
    )


def get_interviews() -> list[dict[str, Any]]:
    return query_all(
        """SELECT i.*, c.name AS candidate_name, j.title AS job_title
        FROM interviews i
        JOIN applications a ON a.id = i.application_id
        JOIN candidates c ON c.id = a.candidate_id
        JOIN jobs j ON j.id = a.job_id
        ORDER BY i.interview_at"""
    )
