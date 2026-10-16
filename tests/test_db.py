"""
Unit tests for EduPulse database utilities, configuration, and SQL query handling.
Uses mocking where appropriate to enable standalone execution without live MySQL.
Supports both pytest and python -m unittest.
"""

import unittest
from unittest.mock import MagicMock, patch
from mysql.connector import Error

import db


class TestDatabaseConfig(unittest.TestCase):
    """Test database configuration loading from environment variables."""

    def test_default_config(self):
        config = db.get_db_config()
        self.assertIn("host", config)
        self.assertIn("port", config)
        self.assertIn("user", config)
        self.assertIn("password", config)
        self.assertIn("database", config)
        self.assertEqual(config["database"], "edupulse_db")


class TestDatabaseSafetyAndErrors(unittest.TestCase):
    """Test graceful handling of database exceptions and parameterized calls."""

    @patch("db.mysql.connector.connect")
    def test_connection_failure_handling(self, mock_connect):
        """Verify test_connection returns (False, msg) gracefully on Error."""
        mock_connect.side_effect = Error(msg="Access denied for user 'root'@'localhost'", errno=1045)
        success, msg = db.test_connection()
        self.assertFalse(success)
        self.assertTrue("1045" in msg or "Access denied" in msg)

    @patch("db.get_connection")
    def test_add_student_parameterized_execution(self, mock_get_conn):
        """Verify that student insertion uses parameterized query with bound arguments."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with patch("db.student_exists", return_value=False):
            success, msg = db.add_student("STU999", "Tester Name", "Computer Science", 1)
            self.assertTrue(success)
            self.assertIn("STU999", msg)
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args
            query = call_args[0][0]
            params = call_args[0][1]
            self.assertIn("%s", query)
            self.assertEqual(params, ("STU999", "Tester Name", "Computer Science", 1))
            mock_conn.commit.assert_called_once()

    @patch("db.get_connection")
    def test_bulk_insert_students_transaction_rollback(self, mock_get_conn):
        """Verify transaction rollback if an unexpected error occurs during bulk import."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Error(msg="Table 'edupulse_db.students' doesn't exist", errno=1146)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        raw_students = [{"student_id": "STU901", "student_name": "Test", "department": "CS", "semester": 2}]
        inserted, rejected, errors = db.bulk_insert_students(raw_students)
        self.assertEqual(inserted, 0)
        self.assertEqual(rejected, 1)
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
