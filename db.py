"""
Database access and management module for EduPulse.
Handles MySQL connections, schema initialization, CRUD operations,
and bulk transactional operations with parameterized queries.
"""

import os
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import mysql.connector
from mysql.connector import Error
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_config() -> Dict[str, Any]:
    """Retrieve database configuration from environment variables."""
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "edupulse_db"),
    }


def get_connection(include_database: bool = True) -> mysql.connector.MySQLConnection:
    """
    Establish and return a connection to MySQL server.
    
    :param include_database: If True, connects directly to MYSQL_DATABASE.
                              If False, connects to the MySQL server instance.
    """
    config = get_db_config()
    conn_params = {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"],
        "password": config["password"],
        "autocommit": False,
    }
    if include_database:
        conn_params["database"] = config["database"]

    return mysql.connector.connect(**conn_params)


def test_connection() -> Tuple[bool, str]:
    """Test MySQL connectivity and return status flag with diagnostic message."""
    connection = None
    try:
        connection = get_connection(include_database=True)
        if connection.is_connected():
            return True, "Successfully connected to MySQL database."
        return False, "Unable to establish active connection."
    except Error as e:
        return False, f"MySQL Connection Error [{e.errno}]: {e.msg}"
    finally:
        if connection and connection.is_connected():
            connection.close()


def init_db() -> Tuple[bool, str]:
    """
    Initialize the database and tables if they do not already exist.
    Creates edupulse_db, students table, and performance table.
    """
    config = get_db_config()
    db_name = config["database"]
    server_conn = None
    cursor = None
    try:
        # Step 1: Connect to server without database and create database if not present
        server_conn = get_connection(include_database=False)
        cursor = server_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4;")
        server_conn.commit()
    except Error as e:
        return False, f"Error creating database '{db_name}': {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if server_conn and server_conn.is_connected():
            server_conn.close()

    # Step 2: Connect to database and create required tables and indexes
    db_conn = None
    try:
        db_conn = get_connection(include_database=True)
        cursor = db_conn.cursor()

        # Students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(50) NOT NULL,
                student_name VARCHAR(100) NOT NULL,
                department VARCHAR(50) NOT NULL,
                semester INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (student_id),
                CONSTRAINT chk_semester CHECK (semester >= 1 AND semester <= 12)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                marks DECIMAL(5, 2) NOT NULL,
                attendance DECIMAL(5, 2) NOT NULL,
                study_hours DECIMAL(4, 1) NOT NULL,
                assignment_score DECIMAL(5, 2) NOT NULL,
                record_date DATE NOT NULL,
                CONSTRAINT fk_performance_student 
                    FOREIGN KEY (student_id) 
                    REFERENCES students(student_id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
                CONSTRAINT chk_marks CHECK (marks >= 0.00 AND marks <= 100.00),
                CONSTRAINT chk_attendance CHECK (attendance >= 0.00 AND attendance <= 100.00),
                CONSTRAINT chk_study_hours CHECK (study_hours >= 0.0),
                CONSTRAINT chk_assignment CHECK (assignment_score >= 0.00 AND assignment_score <= 100.00)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        db_conn.commit()
        return True, "Database and tables initialized successfully."
    except Error as e:
        if db_conn:
            db_conn.rollback()
        return False, f"Error initializing tables: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if db_conn and db_conn.is_connected():
            db_conn.close()


# -----------------------------------------------------------------------------
# STUDENT CRUD OPERATIONS
# -----------------------------------------------------------------------------

def student_exists(student_id: str) -> bool:
    """Check if a student with the given ID already exists."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM students WHERE student_id = %s LIMIT 1", (student_id.strip(),))
        return cursor.fetchone() is not None
    except Error:
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def add_student(student_id: str, student_name: str, department: str, semester: int) -> Tuple[bool, str]:
    """Add a new student record to the database."""
    student_id = student_id.strip()
    student_name = student_name.strip()
    department = department.strip()

    if not student_id or not student_name or not department:
        return False, "Student ID, Name, and Department cannot be empty."
    if semester < 1 or semester > 12:
        return False, "Semester must be between 1 and 12."

    if student_exists(student_id):
        return False, f"Student ID '{student_id}' already exists. Duplicate IDs are not permitted."

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO students (student_id, student_name, department, semester)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (student_id, student_name, department, semester))
        conn.commit()
        return True, f"Student '{student_name}' ({student_id}) added successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error adding student: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_student(student_id: str, student_name: str, department: str, semester: int) -> Tuple[bool, str]:
    """Update existing student details."""
    student_id = student_id.strip()
    student_name = student_name.strip()
    department = department.strip()

    if not student_name or not department:
        return False, "Student Name and Department cannot be empty."
    if semester < 1 or semester > 12:
        return False, "Semester must be between 1 and 12."

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE students 
            SET student_name = %s, department = %s, semester = %s
            WHERE student_id = %s
        """
        cursor.execute(sql, (student_name, department, semester, student_id))
        if cursor.rowcount == 0:
            return False, f"No student found with ID '{student_id}'."
        conn.commit()
        return True, f"Student '{student_id}' updated successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error updating student: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_student(student_id: str) -> Tuple[bool, str]:
    """Delete a student and cascade-delete associated performance records."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM students WHERE student_id = %s"
        cursor.execute(sql, (student_id.strip(),))
        if cursor.rowcount == 0:
            return False, f"Student '{student_id}' not found."
        conn.commit()
        return True, f"Student '{student_id}' and all related records deleted successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error deleting student: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_all_students(
    search_term: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[int] = None,
) -> pd.DataFrame:
    """Retrieve all students matching optional search, department, and semester filters."""
    conn = None
    try:
        conn = get_connection()
        query = "SELECT student_id, student_name, department, semester, created_at FROM students WHERE 1=1"
        params: List[Any] = []

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += " AND (student_id LIKE %s OR student_name LIKE %s)"
            params.extend([term, term])

        if department and department != "All":
            query += " AND department = %s"
            params.append(department)

        if semester and semester != "All":
            query += " AND semester = %s"
            params.append(int(semester))

        query += " ORDER BY student_id ASC"

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return pd.DataFrame(columns=["student_id", "student_name", "department", "semester", "created_at"])
        return pd.DataFrame(rows)
    except Error as e:
        raise RuntimeError(f"Database error loading students: {e.msg}") from e
    finally:
        if conn and conn.is_connected():
            conn.close()


# -----------------------------------------------------------------------------
# PERFORMANCE CRUD OPERATIONS
# -----------------------------------------------------------------------------

def add_performance_record(
    student_id: str,
    subject: str,
    marks: float,
    attendance: float,
    study_hours: float,
    assignment_score: float,
    record_date: Any,
) -> Tuple[bool, str]:
    """Add a subject performance record for an existing student."""
    student_id = student_id.strip()
    subject = subject.strip()

    if not student_id or not subject:
        return False, "Student ID and Subject are required."

    if not student_exists(student_id):
        return False, f"Student '{student_id}' does not exist. Please register the student first."

    if not (0 <= marks <= 100):
        return False, "Marks must be between 0 and 100."
    if not (0 <= attendance <= 100):
        return False, "Attendance must be between 0 and 100%."
    if study_hours < 0:
        return False, "Daily Study Hours must be non-negative."
    if not (0 <= assignment_score <= 100):
        return False, "Assignment score must be between 0 and 100."

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check for exact duplicate submission on the same date
        dup_check = """
            SELECT record_id FROM performance 
            WHERE student_id = %s AND subject = %s AND record_date = %s
            LIMIT 1
        """
        cursor.execute(dup_check, (student_id, subject, record_date))
        if cursor.fetchone():
            return False, f"A performance record for '{student_id}' in '{subject}' on {record_date} already exists."

        sql = """
            INSERT INTO performance (student_id, subject, marks, attendance, study_hours, assignment_score, record_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (student_id, subject, float(marks), float(attendance), float(study_hours), float(assignment_score), record_date))
        conn.commit()
        return True, f"Performance record for '{subject}' added successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error adding performance record: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_performance_record(
    record_id: int,
    subject: str,
    marks: float,
    attendance: float,
    study_hours: float,
    assignment_score: float,
    record_date: Any,
) -> Tuple[bool, str]:
    """Update an existing performance record."""
    subject = subject.strip()
    if not subject:
        return False, "Subject cannot be empty."
    if not (0 <= marks <= 100):
        return False, "Marks must be between 0 and 100."
    if not (0 <= attendance <= 100):
        return False, "Attendance must be between 0 and 100."
    if study_hours < 0:
        return False, "Study hours must be non-negative."
    if not (0 <= assignment_score <= 100):
        return False, "Assignment score must be between 0 and 100."

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE performance 
            SET subject = %s, marks = %s, attendance = %s, study_hours = %s, 
                assignment_score = %s, record_date = %s
            WHERE record_id = %s
        """
        cursor.execute(sql, (subject, float(marks), float(attendance), float(study_hours), float(assignment_score), record_date, record_id))
        if cursor.rowcount == 0:
            return False, f"No performance record found with ID {record_id}."
        conn.commit()
        return True, "Performance record updated successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error updating performance: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_performance_record(record_id: int) -> Tuple[bool, str]:
    """Delete an individual performance record by ID."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM performance WHERE record_id = %s", (record_id,))
        if cursor.rowcount == 0:
            return False, f"Record ID {record_id} not found."
        conn.commit()
        return True, f"Record ID {record_id} deleted successfully."
    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error deleting record: {e.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_performance_by_student(student_id: str) -> pd.DataFrame:
    """Retrieve all performance records for a specific student."""
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT record_id, student_id, subject, marks, attendance, 
                   study_hours, assignment_score, record_date
            FROM performance
            WHERE student_id = %s
            ORDER BY record_date DESC, subject ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (student_id.strip(),))
        rows = cursor.fetchall()
        cursor.close()

        cols = ["record_id", "student_id", "subject", "marks", "attendance", "study_hours", "assignment_score", "record_date"]
        if not rows:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(rows)
    except Error as e:
        raise RuntimeError(f"Database error loading student performance: {e.msg}") from e
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_all_performance() -> pd.DataFrame:
    """Retrieve all performance records across all students."""
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT record_id, student_id, subject, marks, attendance, 
                   study_hours, assignment_score, record_date
            FROM performance
            ORDER BY record_date DESC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        cols = ["record_id", "student_id", "subject", "marks", "attendance", "study_hours", "assignment_score", "record_date"]
        if not rows:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(rows)
    except Error as e:
        raise RuntimeError(f"Database error loading performance records: {e.msg}") from e
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_merged_data(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    subject: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> pd.DataFrame:
    """
    Retrieve joined student and performance data with dynamic filters.
    Returns a unified DataFrame used for analytics and interactive charts.
    """
    conn = None
    try:
        conn = get_connection()
        query = """
            SELECT 
                p.record_id,
                s.student_id,
                s.student_name,
                s.department,
                s.semester,
                p.subject,
                CAST(p.marks AS FLOAT) AS marks,
                CAST(p.attendance AS FLOAT) AS attendance,
                CAST(p.study_hours AS FLOAT) AS study_hours,
                CAST(p.assignment_score AS FLOAT) AS assignment_score,
                p.record_date
            FROM performance p
            INNER JOIN students s ON p.student_id = s.student_id
            WHERE 1=1
        """
        params: List[Any] = []

        if department and department != "All":
            query += " AND s.department = %s"
            params.append(department)

        if semester and semester != "All":
            query += " AND s.semester = %s"
            params.append(int(semester))

        if subject and subject != "All":
            query += " AND p.subject = %s"
            params.append(subject)

        if date_from:
            query += " AND p.record_date >= %s"
            params.append(str(date_from))

        if date_to:
            query += " AND p.record_date <= %s"
            params.append(str(date_to))

        query += " ORDER BY p.record_date DESC, s.student_id ASC"

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        cols = [
            "record_id", "student_id", "student_name", "department", 
            "semester", "subject", "marks", "attendance", "study_hours", 
            "assignment_score", "record_date"
        ]
        if not rows:
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(rows)
        # Ensure correct numeric types
        for col in ["marks", "attendance", "study_hours", "assignment_score"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Error as e:
        raise RuntimeError(f"Database error fetching merged analytics data: {e.msg}") from e
    finally:
        if conn and conn.is_connected():
            conn.close()


# -----------------------------------------------------------------------------
# TRANSACTION-SAFE BULK OPERATIONS FOR CSV IMPORT
# -----------------------------------------------------------------------------

def bulk_insert_students(students_list: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """
    Bulk insert students with transaction rollback on critical failure.
    Skips individual invalid/duplicate records and reports rejected rows.
    
    :return: (inserted_count, rejected_count, error_messages)
    """
    if not students_list:
        return 0, 0, ["No student records provided to import."]

    conn = None
    cursor = None
    inserted_count = 0
    rejected_count = 0
    errors: List[str] = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO students (student_id, student_name, department, semester)
            VALUES (%s, %s, %s, %s)
        """

        for idx, row in enumerate(students_list, start=1):
            sid = str(row.get("student_id", "")).strip()
            name = str(row.get("student_name", "")).strip()
            dept = str(row.get("department", "")).strip()
            sem_raw = row.get("semester", "")

            # Validation
            if not sid or not name or not dept:
                rejected_count += 1
                errors.append(f"Row {idx}: Missing required fields (student_id, student_name, or department).")
                continue

            try:
                sem = int(sem_raw)
                if not (1 <= sem <= 12):
                    raise ValueError("Semester out of range.")
            except (ValueError, TypeError):
                rejected_count += 1
                errors.append(f"Row {idx} ({sid}): Semester must be an integer between 1 and 12 (got '{sem_raw}').")
                continue

            # Check duplicate in DB or current transaction
            try:
                cursor.execute(sql, (sid, name, dept, sem))
                inserted_count += 1
            except mysql.connector.IntegrityError:
                rejected_count += 1
                errors.append(f"Row {idx} ({sid}): Duplicate student ID already exists.")
            except Error as e:
                rejected_count += 1
                errors.append(f"Row {idx} ({sid}): Database error: {e.msg}")

        conn.commit()
        return inserted_count, rejected_count, errors
    except Error as e:
        if conn:
            conn.rollback()
        return 0, len(students_list), [f"Transaction failed and was rolled back: {e.msg}"]
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def bulk_insert_performance(perf_list: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """
    Bulk insert performance records with foreign key validation and transaction safety.
    
    :return: (inserted_count, rejected_count, error_messages)
    """
    if not perf_list:
        return 0, 0, ["No performance records provided to import."]

    conn = None
    cursor = None
    inserted_count = 0
    rejected_count = 0
    errors: List[str] = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Cache existing student IDs to validate foreign key without round trips
        cursor.execute("SELECT student_id FROM students")
        existing_student_ids = {row[0] for row in cursor.fetchall()}

        sql = """
            INSERT INTO performance (student_id, subject, marks, attendance, study_hours, assignment_score, record_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for idx, row in enumerate(perf_list, start=1):
            sid = str(row.get("student_id", "")).strip()
            subject = str(row.get("subject", "")).strip()

            if not sid or not subject:
                rejected_count += 1
                errors.append(f"Row {idx}: Missing student_id or subject.")
                continue

            if sid not in existing_student_ids:
                rejected_count += 1
                errors.append(f"Row {idx}: Student ID '{sid}' not found in students table.")
                continue

            try:
                marks = float(row.get("marks", 0))
                att = float(row.get("attendance", 0))
                hrs = float(row.get("study_hours", 0))
                asg = float(row.get("assignment_score", 0))
                rdate = str(row.get("record_date", "")).strip()

                if not (0 <= marks <= 100):
                    raise ValueError(f"Marks {marks} out of bounds (0-100).")
                if not (0 <= att <= 100):
                    raise ValueError(f"Attendance {att} out of bounds (0-100).")
                if hrs < 0:
                    raise ValueError(f"Study hours {hrs} cannot be negative.")
                if not (0 <= asg <= 100):
                    raise ValueError(f"Assignment score {asg} out of bounds (0-100).")
                if not rdate:
                    raise ValueError("Missing record_date.")

                cursor.execute(sql, (sid, subject, marks, att, hrs, asg, rdate))
                inserted_count += 1
            except (ValueError, TypeError) as val_err:
                rejected_count += 1
                errors.append(f"Row {idx} ({sid} - {subject}): Invalid numeric or date value: {val_err}")
            except Error as db_err:
                rejected_count += 1
                errors.append(f"Row {idx} ({sid} - {subject}): Database insertion error: {db_err.msg}")

        conn.commit()
        return inserted_count, rejected_count, errors
    except Error as e:
        if conn:
            conn.rollback()
        return 0, len(perf_list), [f"Transaction failed and was rolled back: {e.msg}"]
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
