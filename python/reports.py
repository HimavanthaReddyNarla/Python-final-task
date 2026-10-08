"""Report queries and text-file export."""

from pathlib import Path
from typing import Any

from database import query_all


def generate_reports() -> dict[str, list[dict[str, Any]]]:
    return {
        "most_applied_jobs": query_all(
            """SELECT j.title, c.name AS company_name, COUNT(a.id) AS application_count
            FROM jobs j JOIN companies c ON c.id = j.company_id
            LEFT JOIN applications a ON a.job_id = j.id
            GROUP BY j.id, j.title, c.name
            ORDER BY application_count DESC, j.title LIMIT 10"""
        ),
        "top_companies": query_all(
            """SELECT c.name, COUNT(a.id) AS application_count
            FROM companies c
            LEFT JOIN jobs j ON j.company_id = c.id
            LEFT JOIN applications a ON a.job_id = j.id
            GROUP BY c.id, c.name
            ORDER BY application_count DESC, c.name LIMIT 10"""
        ),
        "average_salary": query_all(
            """SELECT c.name, ROUND(AVG(j.salary), 2) AS average_salary
            FROM companies c JOIN jobs j ON j.company_id = c.id
            GROUP BY c.id, c.name ORDER BY average_salary DESC"""
        ),
        "open_jobs": query_all(
            """SELECT j.title, c.name AS company_name, j.location, j.salary
            FROM jobs j JOIN companies c ON c.id = j.company_id
            WHERE j.status = 'Open' ORDER BY j.created_at DESC"""
        ),
        "selected_candidates": query_all(
            """SELECT ca.name AS candidate_name, ca.email, j.title AS job_title,
            co.name AS company_name
            FROM applications a
            JOIN candidates ca ON ca.id = a.candidate_id
            JOIN jobs j ON j.id = a.job_id
            JOIN companies co ON co.id = j.company_id
            WHERE a.status = 'Selected' ORDER BY ca.name"""
        ),
        "status_summary": query_all(
            """SELECT status, COUNT(*) AS total
            FROM applications GROUP BY status ORDER BY status"""
        ),
    }


def export_status_report(reports: dict[str, list[dict[str, Any]]], destination: Path) -> None:
    lines = ["JOB PORTAL - APPLICATION STATUS SUMMARY", "=" * 42]
    rows = reports["status_summary"]
    if rows:
        lines.extend(f"{row['status']}: {row['total']}" for row in rows)
    else:
        lines.append("No applications have been recorded.")
    lines.extend(("", f"Total applications: {sum(row['total'] for row in rows)}"))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
