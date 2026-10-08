# Job Portal Management System

A browser-based, menu-driven job portal built with Python and Flask. It runs
immediately on a local SQLite database, with MySQL available as an alternative.
The launcher starts the local server and opens the portal in your default
browser.

## Requirements

- Python 3.10 or newer

## Start on Windows

Double-click `run.bat`. On first launch it installs the packages from
`requirements.txt`, creates the SQLite database and tables, and opens
<http://127.0.0.1:5000>. The SQLite file is stored at
`python/job_portal.sqlite3`.

## Use MySQL instead

Set `DATABASE_BACKEND=mysql` before starting the app. For example, add
`set "DATABASE_BACKEND=mysql"` to `run.bat`. Configure `MYSQL_HOST`,
`MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE`; the defaults
are `127.0.0.1:3306`, user `root`, blank password, and database `job_portal`.
The MySQL user must have permission to create the database on first launch, and
the MySQL service must be running.

## Features

- Register, list, and search candidates
- Register companies and post, browse, and search jobs
- Apply for jobs and update application status
- Schedule interviews
- Recommend open jobs using skills, experience, and location
- View reports for popular jobs, companies, salary averages, open jobs,
  selected candidates, and application statuses
- Export the application-status report to `python/application_report.txt`

All user-provided SQL values are parameterized. The web server is intended for
local classroom/demo use; do not expose it to the public internet.
