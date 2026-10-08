"""Start the local Job Portal web application and open it in a browser."""

import threading
import webbrowser
from pathlib import Path
from typing import Any

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for

from application import (
    APPLICATION_STATUSES,
    apply_for_job,
    delete_application,
    get_applications,
    get_interviews,
    schedule_interview,
    update_application_status,
)
from candidate import get_candidates, register_candidate, validate_candidate
from company import get_companies, register_company
from database import initialize_database, query_all
from jobs import get_jobs, post_job, recommend_jobs
from reports import export_status_report, generate_reports

app = Flask(__name__)
app.secret_key = "local-job-portal-demo-key"
REPORT_PATH = Path(__file__).resolve().parent / "application_report.txt"


def dashboard_counts() -> dict[str, int]:
    tables = ("candidates", "companies", "jobs", "applications")
    return {
        table: int(query_all(f"SELECT COUNT(*) AS total FROM {table}")[0]["total"])
        for table in tables
    }


def handle_form(action: Any) -> Any:
    try:
        action()
        flash("Your request was completed successfully.", "success")
    except ValueError as error:
        flash(str(error), "error")
    except mysql.connector.IntegrityError as error:
        if error.errno == 1062:
            flash("That record already exists. Check for a duplicate email or application.", "error")
        elif error.errno == 1452:
            flash("The selected company, candidate, job, or application no longer exists.", "error")
        else:
            raise
    return redirect(request.referrer or url_for("index"))


@app.get("/")
def index() -> str:
    counts = dashboard_counts()
    jobs = get_jobs(open_only=True)[:5]
    return render_template(
        "index.html",
        counts=counts,
        jobs=jobs,
        candidates=get_candidates(),
        companies=get_companies(),
        applications=get_applications(),
        statuses=APPLICATION_STATUSES,
        interviews=get_interviews(),
        search=request.args.get("search", ""),
        recommendations=None,
        recommendation_values={},
    )


@app.post("/candidates")
def candidates() -> Any:
    return handle_form(lambda: register_candidate(validate_candidate(request.form)))


@app.get("/candidates/search")
def search_candidates() -> str:
    return render_template(
        "index.html", counts=dashboard_counts(), jobs=get_jobs(open_only=True)[:5],
        candidates=get_candidates(request.args.get("q", "")), companies=get_companies(),
        applications=get_applications(), statuses=APPLICATION_STATUSES,
        interviews=get_interviews(), search=request.args.get("q", ""),
        recommendations=None, recommendation_values={},
    )


@app.post("/companies")
def companies() -> Any:
    return handle_form(lambda: register_company(request.form))


@app.post("/jobs")
def jobs() -> Any:
    return handle_form(lambda: post_job(request.form))


@app.get("/jobs/search")
def search_jobs() -> str:
    term = request.args.get("q", "")
    return render_template(
        "index.html", counts=dashboard_counts(), jobs=get_jobs(term, open_only=True),
        candidates=get_candidates(), companies=get_companies(), applications=get_applications(),
        statuses=APPLICATION_STATUSES, interviews=get_interviews(), search=term,
        recommendations=None, recommendation_values={},
    )


@app.post("/applications")
def applications() -> Any:
    return handle_form(
        lambda: apply_for_job(request.form.get("candidate_id"), request.form.get("job_id"))
    )


@app.post("/applications/status")
def application_status() -> Any:
    return handle_form(
        lambda: update_application_status(
            request.form.get("application_id"), request.form.get("status", "")
        )
    )


@app.post("/applications/delete")
def remove_application() -> Any:
    return handle_form(lambda: delete_application(request.form.get("application_id")))


@app.post("/interviews")
def interviews() -> Any:
    return handle_form(lambda: schedule_interview(request.form))


@app.post("/recommendations")
def recommendations() -> str:
    values = {
        "skills": request.form.get("skills", "").strip(),
        "experience": request.form.get("experience", "").strip(),
        "location": request.form.get("location", "").strip(),
    }
    try:
        experience = float(values["experience"])
        if experience < 0 or experience > 99:
            raise ValueError("Experience must be between 0 and 99 years.")
        matches = recommend_jobs(values["skills"], experience, values["location"])
    except ValueError as error:
        flash(str(error), "error")
        matches = []
    return render_template(
        "index.html", counts=dashboard_counts(), jobs=get_jobs(open_only=True)[:5],
        candidates=get_candidates(), companies=get_companies(), applications=get_applications(),
        statuses=APPLICATION_STATUSES, interviews=get_interviews(), search="",
        recommendations=matches, recommendation_values=values,
    )


@app.get("/reports")
def reports() -> str:
    return render_template("reports.html", reports=generate_reports())


@app.post("/reports/export")
def export_report() -> Any:
    try:
        export_status_report(generate_reports(), REPORT_PATH)
    except OSError:
        app.logger.exception("Could not write the application report file.")
        flash("The report could not be written. Check the application's folder permissions.", "error")
    else:
        flash(f"Application status report saved to {REPORT_PATH.name}.", "success")
    return redirect(url_for("reports"))


def open_browser() -> None:
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    try:
        initialize_database()
    except (mysql.connector.Error, ValueError) as error:
        raise SystemExit(
            "Could not connect to MySQL or initialize the job portal database. "
            "Start MySQL and check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
            f"MYSQL_PASSWORD, and MYSQL_DATABASE. Details: {error}"
        ) from error
    threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
