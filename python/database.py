"""MySQL connection and schema initialization for the job portal."""

import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import mysql.connector
from mysql.connector import MySQLConnection


def database_backend() -> str:
    backend = os.getenv("DATABASE_BACKEND", "sqlite").strip().lower()
    if backend not in {"sqlite", "mysql"}:
        raise ValueError("DATABASE_BACKEND must be either 'sqlite' or 'mysql'.")
    return backend


def _configuration() -> dict[str, Any]:
    database_name = os.getenv("MYSQL_DATABASE", "job_portal")
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise ValueError("MYSQL_DATABASE may contain only letters, numbers, and underscores.")
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": database_name,
    }


def _sqlite_connection() -> sqlite3.Connection:
    default_path = Path(__file__).resolve().parent / "job_portal.sqlite3"
    path = Path(os.getenv("SQLITE_DATABASE", str(default_path))).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create the configured database and required tables if they do not exist."""
    if database_backend() == "sqlite":
        with connection_scope() as connection:
            statements = (
                """
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    industry TEXT NOT NULL,
                    location TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    experience_years REAL NOT NULL DEFAULT 0,
                    location TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    experience_required REAL NOT NULL DEFAULT 0,
                    location TEXT NOT NULL,
                    salary REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open'
                        CHECK(status IN ('Open', 'Closed')),
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Applied'
                        CHECK(status IN ('Applied', 'Shortlisted', 'Selected', 'Rejected')),
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (candidate_id, job_id),
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    interview_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id)
                )
                """,
            )
            for statement in statements:
                connection.execute(statement)
            connection.commit()
        return

    config = _configuration()
    database_name = config.pop("database")
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        cursor.close()
    finally:
        connection.close()

    with connection_scope() as connection:
        cursor = connection.cursor()
        statements = (
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL UNIQUE,
                industry VARCHAR(120) NOT NULL,
                location VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL UNIQUE,
                phone VARCHAR(30) NOT NULL,
                skills TEXT NOT NULL,
                experience_years DECIMAL(5, 2) NOT NULL DEFAULT 0,
                location VARCHAR(150) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                title VARCHAR(150) NOT NULL,
                description TEXT NOT NULL,
                skills TEXT NOT NULL,
                experience_required DECIMAL(5, 2) NOT NULL DEFAULT 0,
                location VARCHAR(150) NOT NULL,
                salary DECIMAL(12, 2) NOT NULL,
                status ENUM('Open', 'Closed') NOT NULL DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id INT NOT NULL,
                job_id INT NOT NULL,
                status ENUM('Applied', 'Shortlisted', 'Selected', 'Rejected')
                    NOT NULL DEFAULT 'Applied',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_candidate_job (candidate_id, job_id),
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application_id INT NOT NULL,
                interview_at DATETIME NOT NULL,
                mode VARCHAR(60) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
            """,
        )
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
        cursor.close()


@contextmanager
def connection_scope() -> Iterator[MySQLConnection | sqlite3.Connection]:
    """Yield a database connection and always close it."""
    connection = (
        _sqlite_connection()
        if database_backend() == "sqlite"
        else mysql.connector.connect(**_configuration())
    )
    try:
        yield connection
    finally:
        connection.close()


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection_scope() as connection:
        if isinstance(connection, sqlite3.Connection):
            sql = sql.replace("%s", "?")
        cursor = (
            connection.cursor(dictionary=True)
            if isinstance(connection, MySQLConnection)
            else connection.cursor()
        )
        cursor.execute(sql, params)
        results = (
            cursor.fetchall()
            if isinstance(connection, MySQLConnection)
            else [dict(row) for row in cursor.fetchall()]
        )
        cursor.close()
        return results


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with connection_scope() as connection:
        if isinstance(connection, sqlite3.Connection):
            sql = sql.replace("%s", "?")
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return int(last_id or 0)
