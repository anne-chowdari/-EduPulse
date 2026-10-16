"""
Unit tests for EduPulse Graphical Reports & Visual Analytics module (reports.py).
Tests chart data preparation, analytical summaries, empty-state resilience,
student-level vs assessment-level pass calculations, and PDF generation.
Supports both pytest and python -m unittest.
"""

import unittest
import pandas as pd

import reports


def get_test_performance_dataset() -> pd.DataFrame:
    """Provides a synthetic multi-subject, multi-department dataset for testing."""
    return pd.DataFrame([
        {
            "record_id": 1,
            "student_id": "STU1",
            "student_name": "Alice Smith",
            "department": "Computer Science",
            "semester": 4,
            "subject": "Data Structures",
            "marks": 92.0,
            "attendance": 96.0,
            "study_hours": 4.5,
            "assignment_score": 90.0,
            "record_date": "2026-03-01",
        },
        {
            "record_id": 2,
            "student_id": "STU1",
            "student_name": "Alice Smith",
            "department": "Computer Science",
            "semester": 4,
            "subject": "Database Systems",
            "marks": 88.0,
            "attendance": 94.0,
            "study_hours": 4.0,
            "assignment_score": 86.0,
            "record_date": "2026-03-05",
        },
        {
            "record_id": 3,
            "student_id": "STU2",
            "student_name": "Bob Jones",
            "department": "Information Technology",
            "semester": 2,
            "subject": "Programming in C",
            "marks": 36.0,  # Below pass mark 40
            "attendance": 68.0,  # Below attendance 75%
            "study_hours": 1.0,
            "assignment_score": 45.0,  # Below assignment 50
            "record_date": "2026-03-02",
        },
        {
            "record_id": 4,
            "student_id": "STU2",
            "student_name": "Bob Jones",
            "department": "Information Technology",
            "semester": 2,
            "subject": "Web Development",
            "marks": 42.0,  # Pass mark
            "attendance": 70.0,
            "study_hours": 1.5,
            "assignment_score": 55.0,
            "record_date": "2026-03-08",
        },
        {
            "record_id": 5,
            "student_id": "STU3",
            "student_name": "Charlie Brown",
            "department": "Electronics",
            "semester": 6,
            "subject": "Digital Signals",
            "marks": 65.0,
            "attendance": 82.0,
            "study_hours": 3.0,
            "assignment_score": 75.0,
            "record_date": "2026-03-03",
        },
    ])


class TestTopPerformingStudents(unittest.TestCase):
    """Test student-level ranking and distinction calculation."""

    def test_top_students_ranking_and_aggregations(self):
        df = get_test_performance_dataset()
        top_df = reports.get_top_performing_students(df, top_n=5)

        self.assertEqual(len(top_df), 3)  # 3 unique students: Alice, Charlie, Bob
        self.assertEqual(top_df.iloc[0]["student_id"], "STU1")
        self.assertEqual(top_df.iloc[0]["rank"], 1)
        self.assertEqual(top_df.iloc[0]["avg_marks"], 90.0)  # (92 + 88) / 2
        self.assertEqual(top_df.iloc[0]["standing"], "🌟 High Distinction")

        # Bob avg: (36 + 42) / 2 = 39.0 -> Needs Academic Support
        bob_row = top_df[top_df["student_id"] == "STU2"].iloc[0]
        self.assertEqual(bob_row["avg_marks"], 39.0)
        self.assertEqual(bob_row["standing"], "🚨 Academic Support")

    def test_top_students_empty_handling(self):
        empty_df = pd.DataFrame()
        top_df = reports.get_top_performing_students(empty_df)
        self.assertTrue(top_df.empty)
        self.assertIn("rank", top_df.columns)
        self.assertIn("avg_marks", top_df.columns)


class TestSubjectPerformanceAnalysis(unittest.TestCase):
    """Test subject breakdown, pass percentages, and attention flagging."""

    def test_subject_analysis_metrics(self):
        df = get_test_performance_dataset()
        subj_df = reports.get_subject_performance_analysis(df, pass_threshold=40.0)

        # 4 distinct subjects: Data Structures, Database Systems, Programming in C, Web Development, Digital Signals
        self.assertEqual(len(subj_df), 5)

        # Programming in C has marks=36.0 (fails cutoff 40.0) -> pass rate 0.0%, status Needs Attention
        c_row = subj_df[subj_df["subject"] == "Programming in C"].iloc[0]
        self.assertEqual(c_row["pass_percentage"], 0.0)
        self.assertEqual(c_row["status"], "Needs Attention")

        # Data Structures has marks=92.0 -> pass rate 100.0%, status Satisfactory
        ds_row = subj_df[subj_df["subject"] == "Data Structures"].iloc[0]
        self.assertEqual(ds_row["pass_percentage"], 100.0)
        self.assertEqual(ds_row["status"], "Satisfactory")

    def test_subject_analysis_empty_handling(self):
        subj_df = reports.get_subject_performance_analysis(pd.DataFrame())
        self.assertTrue(subj_df.empty)
        self.assertIn("total_assessments", subj_df.columns)


class TestStudyHoursAnalysis(unittest.TestCase):
    """Test study hours binning, correlation, and department summaries."""

    def test_study_hours_binned_and_correlation(self):
        df = get_test_performance_dataset()
        binned, dept_study, corr = reports.get_study_hours_analysis(df)

        self.assertFalse(binned.empty)
        self.assertFalse(dept_study.empty)
        # Verify correlation is positive between hours and marks in this dataset
        self.assertGreater(corr, 0.5)

        # Check department average study hours
        cs_dept = dept_study[dept_study["department"] == "Computer Science"].iloc[0]
        self.assertAlmostEqual(cs_dept["avg_study_hours"], 4.25, delta=0.1)

    def test_study_hours_empty_handling(self):
        binned, dept_study, corr = reports.get_study_hours_analysis(pd.DataFrame())
        self.assertTrue(binned.empty)
        self.assertTrue(dept_study.empty)
        self.assertEqual(corr, 0.0)


class TestAttendanceAnalysis(unittest.TestCase):
    """Test department attendance, threshold violations, and quadrant groupings."""

    def test_attendance_quadrants_and_low_attendance(self):
        df = get_test_performance_dataset()
        dept_att, low_att, quadrants = reports.get_attendance_analysis_data(df, threshold=75.0)

        # Bob Jones has avg attendance 69.0% -> below 75%
        self.assertEqual(len(low_att), 1)
        self.assertEqual(low_att.iloc[0]["student_id"], "STU2")

        # Quadrant counts
        # Alice: High Att & Pass (marks 90 >= 40, att 95 >= 75)
        # Charlie: High Att & Pass (marks 65 >= 40, att 82 >= 75)
        # Bob: Low Att & Need Support (marks 39 < 40, att 69 < 75)
        self.assertEqual(quadrants["High Att & Pass"], 2)
        self.assertEqual(quadrants["Low Att & Need Support"], 1)

    def test_attendance_empty_handling(self):
        dept_att, low_att, quadrants = reports.get_attendance_analysis_data(pd.DataFrame())
        self.assertTrue(dept_att.empty)
        self.assertTrue(low_att.empty)
        self.assertEqual(sum(quadrants.values()), 0)


class TestOverallSummaryAndConsistency(unittest.TestCase):
    """Test student-level vs assessment-level pass rates and metric consistency."""

    def test_pass_rate_distinction(self):
        """
        Total assessments: 5
        Passing assessments (marks >= 40): 4 (92, 88, 42, 65). Only 36 fails.
        Assessment pass rate: 4 / 5 = 80.0%

        Students: 3 (Alice, Bob, Charlie)
        Student averages:
        Alice: 90.0 (Pass)
        Charlie: 65.0 (Pass)
        Bob: (36 + 42)/2 = 39.0 (Fail)
        Student pass rate: 2 / 3 = 66.7%
        """
        df = get_test_performance_dataset()
        summary = reports.get_overall_academic_summary(df, pass_threshold=40.0)

        self.assertEqual(summary["total_students"], 3)
        self.assertEqual(summary["total_assessments"], 5)
        self.assertEqual(summary["assessment_pass_rate"], 80.0)
        self.assertEqual(summary["student_pass_rate"], 66.7)
        self.assertEqual(summary["students_needing_support"], 1)

    def test_key_observations_generation(self):
        df = get_test_performance_dataset()
        obs = reports.generate_key_observations(df)
        self.assertGreaterEqual(len(obs), 3)
        # Verify it mentions student count and assessments
        combined_text = " ".join(obs)
        self.assertIn("assessment(s)", combined_text)
        self.assertIn("student(s)", combined_text)


class TestPDFReportGeneration(unittest.TestCase):
    """Test PDF generation with embedded charts and tables."""

    def test_pdf_generation_valid_output(self):
        df = get_test_performance_dataset()
        pdf_bytes = reports.generate_pdf_academic_report(
            df,
            filters_dict={"department": "All", "semester": "All", "subject": "All", "date_scope": "All Dates"},
            pass_threshold=40.0,
            attendance_threshold=75.0,
        )

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        # Standard PDF magic header
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_empty_dataset(self):
        empty_df = pd.DataFrame()
        pdf_bytes = reports.generate_pdf_academic_report(empty_df)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
