"""Company registration and lookup operations."""

import re
from typing import Any

from database import execute, query_all


def register_company(data: dict[str, Any]) -> int:
    name = str(data.get("name", "")).strip()
    industry = str(data.get("industry", "")).strip()
    location = str(data.get("location", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    if not all((name, industry, location)):
        raise ValueError("Company name, industry, and location are required.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Enter a valid company email address.")
    return execute(
        "INSERT INTO companies (name, industry, location, email) VALUES (%s, %s, %s, %s)",
        (name, industry, location, email),
    )


def get_companies() -> list[dict[str, Any]]:
    return query_all("SELECT * FROM companies ORDER BY name")
