"""
Unit tests for EduPulse dynamic analytics and rule-based recommendation engine.
Tests empty database handling, student-level vs subject-level aggregations,
KPI calculations, and advisory rules with edge cases.
Supports both pytest and python -m unittest.
"""

import unittest
import pandas as pd

from analytics import (
    calculate_kpis,
    get_student_summary,
    generate_recommendations,
    get_recommendation_summary,
)


def get_sample_performance_df() -> pd.DataFrame:
    """Provides a synthetic merged DataFrame with known values for testing."""
    return pd.DataFrame([
        {
            "record_id": 1,
            "student_id": "STU1",
            "student_name": "Alice",
            "department": "Computer Science",
            "semester": 4,
            "subject": "Data Structures",
            "marks": 90.0,
            "attendance": 95.0,
            "study_hours": 4.0,
            "assignment_score": 92.0,
            "record_date": "2026-03-01",
        },
        {
            "record_id": 2,
            "student_id": "STU1",
            "student_name": "Alice",
            "department": "Computer Science",
            "semester": 4,
            "subject": "Database Systems",
            "marks": 80.0,
            "attendance": 85.0,
            "study_hours": 3.0,
            "assignment_score": 88.0,
            "record_date": "2026-03-05",
        },
        {
            "record_id": 3,
            "student_id": "STU2",
            "student_name": "Bob",
            "department": "Information Technology",
            "semester": 2,
            "subject": "Programming in C",
            "marks": 35.0,  # Below 40 -> Needs academic support
            "attendance": 65.0,  # Below 75% -> Needs attendance review
            "study_hours": 1.0,
            "assignment_score": 45.0,  # Below 50 -> Needs assignment support
            "record_date": "2026-03-02",
        },
        {
            "record_id": 4,
            "student_id": "STU3",
            "student_name": "Charlie",
            "department": "Electronics",
            "semester": 6,
            "subject": "Digital Signals",
            "marks": 60.0,
            "attendance": 80.0,
            "study_hours": 2.5,
            "assignment_score": 70.0,
            "record_date": "2026-03-03",
        },
    ])


class TestKPICalculations(unittest.TestCase):
    """Test dynamic KPI calculations and empty states."""

    def test_empty_dataframe_handling(self):
        kpis = calculate_kpis(pd.DataFrame(), students_df=pd.DataFrame())
        self.assertEqual(kpis["total_students"], 0)
        self.assertEqual(kpis["total_records"], 0)
        self.assertEqual(kpis["avg_marks"], 0.0)
        self.assertEqual(kpis["pass_percentage"], 0.0)
        self.assertEqual(kpis["students_needing_support"], 0)
        self.assertFalse(kpis["has_data"])

    def test_empty_records_with_registered_students(self):
        st_df = pd.DataFrame([{"student_id": "STU1"}, {"student_id": "STU2"}])
        kpis = calculate_kpis(pd.DataFrame(), students_df=st_df)
        self.assertEqual(kpis["total_students"], 2)
        self.assertEqual(kpis["total_records"], 0)
        self.assertFalse(kpis["has_data"])

    def test_kpi_averages_and_totals(self):
        df = get_sample_performance_df()
        kpis = calculate_kpis(df)
        self.assertEqual(kpis["total_students"], 3)
        self.assertEqual(kpis["total_records"], 4)
        self.assertEqual(kpis["avg_marks"], 66.25)
        self.assertEqual(kpis["avg_attendance"], 81.25)
        self.assertTrue(kpis["has_data"])

    def test_student_level_vs_subject_level_pass_percentage(self):
        df = get_sample_performance_df()
        kpis = calculate_kpis(df, pass_mark_threshold=40.0)
        self.assertEqual(kpis["pass_percentage"], 66.7)

    def test_students_needing_support_count(self):
        df = get_sample_performance_df()
        kpis = calculate_kpis(df)
        self.assertEqual(kpis["students_needing_support"], 1)


class TestStudentSummary(unittest.TestCase):
    """Test student-level aggregation and status assignment."""

    def test_student_summary_aggregation(self):
        df = get_sample_performance_df()
        summary = get_student_summary(df)
        self.assertEqual(len(summary), 3)

        stu1_row = summary[summary["student_id"] == "STU1"].iloc[0]
        self.assertEqual(stu1_row["subjects_taken"], 2)
        self.assertEqual(stu1_row["avg_marks"], 85.0)
        self.assertEqual(stu1_row["status"], "Distinction / Strong")

        stu2_row = summary[summary["student_id"] == "STU2"].iloc[0]
        self.assertEqual(stu2_row["subjects_taken"], 1)
        self.assertEqual(stu2_row["avg_marks"], 35.0)
        self.assertEqual(stu2_row["status"], "Needs Support")

        stu3_row = summary[summary["student_id"] == "STU3"].iloc[0]
        self.assertEqual(stu3_row["status"], "Good Standing")


class TestRuleBasedRecommendations(unittest.TestCase):
    """Test recommendation engine logic and configurable threshold edge cases."""

    def test_recommendation_rules(self):
        df = get_sample_performance_df()
        recs = generate_recommendations(df)
        self.assertGreater(len(recs), 0)

        # Check STU1 has High Achievement
        stu1_recs = [r for r in recs if r["student_id"] == "STU1"]
        self.assertTrue(any(r["category"] == "High Achievement" for r in stu1_recs))

        # Check STU2 triggers Academic Support, Attendance Review, Assignment Support
        stu2_recs = [r for r in recs if r["student_id"] == "STU2"]
        categories = {r["category"] for r in stu2_recs}
        self.assertIn("Academic Support", categories)
        self.assertIn("Attendance Review", categories)
        self.assertIn("Assignment Support", categories)

        for r in recs:
            self.assertGreater(len(r["reason"]), 0)
            self.assertGreater(len(r["actionable_suggestion"]), 0)

    def test_custom_configurable_thresholds(self):
        df = get_sample_performance_df()
        recs_custom = generate_recommendations(df, marks_threshold=65.0)
        stu3_recs = [r for r in recs_custom if r["student_id"] == "STU3"]
        self.assertTrue(any(r["category"] == "Academic Support" for r in stu3_recs))

    def test_recommendation_summary_counts(self):
        df = get_sample_performance_df()
        recs = generate_recommendations(df)
        counts = get_recommendation_summary(recs)
        self.assertGreaterEqual(counts["Academic Support"], 1)
        self.assertGreaterEqual(counts["Attendance Review"], 1)
        self.assertGreaterEqual(counts["Assignment Support"], 1)
        self.assertGreaterEqual(counts["High Achievement"], 1)


if __name__ == "__main__":
    unittest.main()
