-- ============================================================================
-- EduPulse — Student Performance Analytics Hub
-- Database Initialization Script (MySQL)
-- ============================================================================

-- 1. Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS edupulse_db;
USE edupulse_db;

-- 2. Create Students Table
-- Stores core academic profile for each enrolled student
CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(50) NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    semester INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    CONSTRAINT chk_semester CHECK (semester >= 1 AND semester <= 12)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Create Performance Records Table
-- Stores individual subject performance metrics per student
-- Each student can have multiple performance records across different subjects
CREATE TABLE IF NOT EXISTS performance (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    marks DECIMAL(5, 2) NOT NULL,
    attendance DECIMAL(5, 2) NOT NULL,
    study_hours DECIMAL(4, 1) NOT NULL,       -- Labeled as Daily Study Hours (hrs/day)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Helpful Indexing for Fast Search & Analytics Filtering
CREATE INDEX idx_student_dept ON students(department);
CREATE INDEX idx_student_sem ON students(semester);
CREATE INDEX idx_perf_student ON performance(student_id);
CREATE INDEX idx_perf_subject ON performance(subject);
CREATE INDEX idx_perf_date ON performance(record_date);
