"""
Unit tests for EduPulse data validation logic.
Tests boundary conditions, invalid inputs, missing fields, and CSV parsing.
Independent of a live MySQL database.
Supports both pytest and python -m unittest.
"""

import unittest
from datetime import date
import pandas as pd

from analytics import (
    validate_student_inputs,
    validate_performance_inputs,
    validate_student_csv,
    validate_performance_csv,
)


class TestStudentInputValidation(unittest.TestCase):
    """Test individual student input fields."""

    def test_valid_student(self):
        valid, msg = validate_student_inputs("STU001", "Alice Smith", "Computer Science", 3)
        self.assertTrue(valid)
        self.assertIn("Valid", msg)

    def test_missing_student_id(self):
        valid, msg = validate_student_inputs("", "Alice Smith", "Computer Science", 3)
        self.assertFalse(valid)
        self.assertIn("Student ID cannot be empty", msg)

    def test_whitespace_only_student_id(self):
        valid, msg = validate_student_inputs("   ", "Alice Smith", "Computer Science", 3)
        self.assertFalse(valid)
        self.assertIn("Student ID cannot be empty", msg)

    def test_missing_student_name(self):
        valid, msg = validate_student_inputs("STU001", "", "Computer Science", 3)
        self.assertFalse(valid)
        self.assertIn("Student Name cannot be empty", msg)

    def test_missing_department(self):
        valid, msg = validate_student_inputs("STU001", "Alice Smith", "", 3)
        self.assertFalse(valid)
        self.assertIn("Department cannot be empty", msg)

    def test_invalid_semester_out_of_range(self):
        valid_low, _ = validate_student_inputs("STU001", "Alice Smith", "Computer Science", 0)
        valid_high, _ = validate_student_inputs("STU001", "Alice Smith", "Computer Science", 13)
        self.assertFalse(valid_low)
        self.assertFalse(valid_high)

    def test_invalid_semester_type(self):
        valid, msg = validate_student_inputs("STU001", "Alice Smith", "Computer Science", "Third")
        self.assertFalse(valid)
        self.assertIn("integer", msg.lower())


class TestPerformanceInputValidation(unittest.TestCase):
    """Test performance input fields: marks, attendance, study hours, assignment score."""

    def test_valid_performance(self):
        valid, msg = validate_performance_inputs(
            student_id="STU001",
            subject="Mathematics",
            marks=85.5,
            attendance=90.0,
            study_hours=3.5,
            assignment_score=88.0,
            record_date=date(2026, 3, 1),
        )
        self.assertTrue(valid)
        self.assertIn("Valid", msg)

    def test_marks_out_of_range_negative(self):
        valid, msg = validate_performance_inputs("STU001", "Math", -5.0, 90.0, 3.0, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("Marks must be between 0 and 100", msg)

    def test_marks_out_of_range_above_hundred(self):
        valid, msg = validate_performance_inputs("STU001", "Math", 105.0, 90.0, 3.0, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("Marks must be between 0 and 100", msg)

    def test_attendance_out_of_range(self):
        valid, msg = validate_performance_inputs("STU001", "Math", 75.0, 105.0, 3.0, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("Attendance must be between 0 and 100%", msg)

    def test_negative_study_hours(self):
        valid, msg = validate_performance_inputs("STU001", "Math", 75.0, 85.0, -1.5, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("study hours cannot be negative", msg.lower())

    def test_excessive_study_hours(self):
        valid, msg = validate_performance_inputs("STU001", "Math", 75.0, 85.0, 25.0, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("cannot exceed 24 hours", msg.lower())

    def test_assignment_score_out_of_range(self):
        valid, msg = validate_performance_inputs("STU001", "Math", 75.0, 85.0, 3.0, -10.0, date.today())
        self.assertFalse(valid)
        self.assertIn("Assignment score must be between 0 and 100", msg)

    def test_missing_subject(self):
        valid, msg = validate_performance_inputs("STU001", "  ", 75.0, 85.0, 3.0, 80.0, date.today())
        self.assertFalse(valid)
        self.assertIn("Subject cannot be empty", msg)


class TestCSVValidation(unittest.TestCase):
    """Test CSV file format, column requirements, and row validity."""

    def test_valid_student_csv(self):
        df = pd.DataFrame({
            "student_id": ["STU1", "STU2"],
            "student_name": ["John Doe", "Jane Roe"],
            "department": ["Computer Science", "Information Technology"],
            "semester": [2, 4],
        })
        is_valid, msg, records = validate_student_csv(df)
        self.assertTrue(is_valid)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["student_id"], "STU1")

    def test_student_csv_missing_columns(self):
        df = pd.DataFrame({
            "student_id": ["STU1"],
            "student_name": ["John Doe"],
        })
        is_valid, msg, _ = validate_student_csv(df)
        self.assertFalse(is_valid)
        self.assertIn("Missing required CSV columns", msg)

    def test_student_csv_duplicate_ids(self):
        df = pd.DataFrame({
            "student_id": ["STU1", "STU1"],
            "student_name": ["John Doe", "John Duplicate"],
            "department": ["Computer Science", "Computer Science"],
            "semester": [2, 2],
        })
        is_valid, msg, _ = validate_student_csv(df)
        self.assertFalse(is_valid)
        self.assertIn("Duplicate student_id 'STU1'", msg)

    def test_valid_performance_csv(self):
        df = pd.DataFrame({
            "student_id": ["STU1"],
            "subject": ["Data Structures"],
            "marks": [82.5],
            "attendance": [90.0],
            "study_hours": [3.0],
            "assignment_score": [85.0],
            "record_date": ["2026-03-01"],
        })
        is_valid, msg, records = validate_performance_csv(df, existing_student_ids={"STU1"})
        self.assertTrue(is_valid)
        self.assertEqual(len(records), 1)

    def test_performance_csv_foreign_key_check(self):
        df = pd.DataFrame({
            "student_id": ["NON_EXISTENT_ID"],
            "subject": ["Data Structures"],
            "marks": [82.5],
            "attendance": [90.0],
            "study_hours": [3.0],
            "assignment_score": [85.0],
            "record_date": ["2026-03-01"],
        })
        is_valid, msg, _ = validate_performance_csv(df, existing_student_ids={"STU1", "STU2"})
        self.assertFalse(is_valid)
        self.assertIn("does not exist in the database", msg)

    def test_performance_csv_invalid_marks_row(self):
        df = pd.DataFrame({
            "student_id": ["STU1"],
            "subject": ["Data Structures"],
            "marks": [150.0],
            "attendance": [90.0],
            "study_hours": [3.0],
            "assignment_score": [85.0],
            "record_date": ["2026-03-01"],
        })
        is_valid, msg, _ = validate_performance_csv(df, existing_student_ids={"STU1"})
        self.assertFalse(is_valid)
        self.assertIn("Marks must be between 0 and 100", msg)


if __name__ == "__main__":
    unittest.main()
