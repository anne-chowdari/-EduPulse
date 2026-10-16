# EduPulse — Student Performance Analytics Hub

**EduPulse** is an academic intelligence and performance monitoring application built for colleges and universities. It allows educators, academic coordinators, and department heads to track student grades, attendance compliance, assignment submissions, and daily study hours.

EduPulse computes institutional academic KPIs dynamically from a persistent MySQL database and generates transparent, explainable, rule-based recommendations to help faculty identify students who need academic support or intervention early.

EduPulse follows the architecture and workflow demonstrated in the BizPulse reference project, elevated into a complete educational analytics solution.

---

## 🎯 1. Project Objectives

- **Continuous Academic Tracking:** Provide real-time visibility into student performance across departments, semesters, and individual subjects.
- **Dynamic KPI Computation:** Calculate institutional statistics (total enrollments, overall averages, attendance compliance, and student pass percentages) strictly from live database data without hardcoded or synthetic placeholder metrics.
- **Transparent Academic Support Rules:** Flag at-risk students and high achievers using clear, configurable academic rules with actionable faculty suggestions.
- **Fair Student-Level Aggregations:** Separate student-level metrics (e.g. overall pass rate) from subject-level assessment counts, preventing multiple subject entries from skewing student metrics.
- **Secure Data Persistence:** Store academic records safely in MySQL with relational integrity, foreign key cascading, and parameterized queries.
- **Standardized Data Import & Export:** Provide bulk CSV upload with pre-import validation and downloadable institutional reports.

---

## ✨ 2. Key Features

### 📊 Interactive Dashboard
- **Dynamic Metric Cards:** Total students, total assessments, average marks, average attendance, student-level pass rate, and count of students needing academic support.
- **Interactive Plotly Visualizations:**
  - Average Marks by Subject (horizontal bar chart with color gradient)
  - Average Marks by Department
  - Marks Distribution with Pass Cutoff Reference Line
  - Attendance vs Marks Correlation (bubble size scaled by daily study hours)
  - Continuous Assignment Scores Distribution by Subject
  - Semester-wise Academic Performance and Attendance Trend Lines
- **Multi-Level Global Filters:** Filter metrics and charts by Department, Semester, Subject, and Custom Date Window.

### 👤 Student Profile Management
- Enroll students with Student ID, Full Name, Department, and Semester (Sem 1 to Sem 12).
- Automatic trimming, duplicate ID prevention, and data validation.
- Complete search and filtering by student ID, name, department, and semester.
- Profile editing and permanent student deletion with cascading cleanup of subject records.

### 📝 Performance Tracking
- Record subject-level assessments for any enrolled student.
- Captures: Subject, Marks (0–100), Attendance (0–100%), Daily Study Hours (hrs/day, non-negative), Continuous Assignment Score (0–100), and Assessment Date.
- Prevents duplicate entries for the same subject and assessment date.
- Displays immediate academic assessment history for the selected student.

### 💡 Rule-Based Academic Insights & Mentoring Engine
- Generates clear, pedagogical recommendations categorized into:
  - 🚨 **Academic Support:** Marks below institutional passing mark (default < 40/100).
  - 📅 **Attendance Review:** Attendance below institutional minimum benchmark (default < 75%).
  - 📝 **Assignment Coaching:** Continuous assignment score below threshold (default < 50/100).
  - 🌟 **High Achievement:** Subject mastery meeting or exceeding threshold (default ≥ 75/100).
- Interactive sliders to dynamically adjust institutional thresholds.
- Displays the exact reason and actionable counseling suggestions (e.g., 1-on-1 tutoring, assignment clinics, honors eligibility).
- Clear pedagogical disclaimer emphasizing decision-support use rather than predictive claims.

### 📥 Reports & Batch Data Management
- **CSV Data Import:**
  - Bulk import student profiles (`student_id,student_name,department,semester`).
  - Bulk import performance records (`student_id,subject,marks,attendance,study_hours,assignment_score,record_date`).
  - Pre-import validation preview, foreign key verification, and transactional safety with atomic rollback.
  - Downloadable sample CSV templates.
- **CSV Data Export:**
  - Download Student Directory, Raw Performance Records, Aggregated Student Summaries, and Mentoring Recommendations.

---

## 🛠️ 3. Technology Stack

- **Programming Language:** Python 3 (Tested on Python 3.9+)
- **User Interface:** [Streamlit](https://streamlit.io/) (Light theme with deep blue accents)
- **Database:** MySQL Server (InnoDB engine, utf8mb4)
- **Database Driver:** `mysql-connector-python`
- **Data Processing:** [Pandas](https://pandas.pydata.org/)
- **Data Visualizations:** [Plotly Express & Graph Objects](https://plotly.com/python/)
- **Configuration:** `python-dotenv` for local environment variables
- **Testing Frameworks:** `pytest` and Python `unittest`
- **Version Control:** Git & GitHub

---

## 📁 4. Project Folder Structure

```text
EduPulse/
├── app.py                      # Main Streamlit web application & page navigation
├── db.py                       # MySQL connection management, schema init & CRUD operations
├── analytics.py                # Validation rules, dynamic KPIs & recommendation engine
├── database.sql                # Complete MySQL DDL schema script with constraints & indexes
├── requirements.txt            # Python dependencies
├── .env.example                # Template for database environment variables
├── .env                        # Local database credentials (ignored by Git)
├── .gitignore                  # Git ignore rules for virtual environments and secrets
├── README.md                   # Complete documentation and setup manual
├── data/
│   ├── sample_students.csv     # Synthetic student dataset for testing & demonstration
│   └── sample_performance.csv  # Synthetic performance records for testing & demonstration
└── tests/
    ├── __init__.py             # Test suite package initializer
    ├── test_validation.py      # Tests for inputs, boundary ranges, and CSV validation
    ├── test_analytics.py       # Tests for dynamic KPIs, aggregations, and advisory rules
    └── test_db.py              # Tests for database configuration, queries, and transactions
```

---

## 🗄️ 5. Relational Database Schema

### `students` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `student_id` | `VARCHAR(50)` | `PRIMARY KEY` | Unique institutional student identifier |
| `student_name` | `VARCHAR(100)` | `NOT NULL` | Full name of the student |
| `department` | `VARCHAR(50)` | `NOT NULL` | Academic department / branch |
| `semester` | `INT` | `CHECK (semester BETWEEN 1 AND 12)` | Current semester |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Enrollment record timestamp |

### `performance` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | `INT` | `AUTO_INCREMENT, PRIMARY KEY` | Unique assessment record identifier |
| `student_id` | `VARCHAR(50)` | `FOREIGN KEY ... ON DELETE CASCADE` | References `students(student_id)` |
| `subject` | `VARCHAR(100)` | `NOT NULL` | Course / subject title |
| `marks` | `DECIMAL(5,2)` | `CHECK (marks BETWEEN 0 AND 100)` | Assessment score out of 100 |
| `attendance` | `DECIMAL(5,2)` | `CHECK (attendance BETWEEN 0 AND 100)` | Attendance percentage |
| `study_hours` | `DECIMAL(4,1)` | `CHECK (study_hours >= 0)` | Daily study hours (hrs/day) |
| `assignment_score` | `DECIMAL(5,2)` | `CHECK (assignment_score BETWEEN 0 AND 100)`| Continuous assignment grade |
| `record_date` | `DATE` | `NOT NULL` | Date of assessment record |

---

## 💻 6. Installation & Execution Guide (macOS)

### Step 1: Open Terminal & Navigate to Project
```bash
cd /Users/venkatasrikasyapkondiparthi/Downloads/varma
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Upgrade pip & Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

## 🐬 7. MySQL Setup Instructions

### Option A: If MySQL Server is already installed locally
1. Start your local MySQL server (or verify it is running in MySQL Workbench / System Settings).
2. Open terminal and log in to MySQL:
   ```bash
   mysql -u root -p
   ```
3. Initialize the database schema by running `database.sql`:
   ```sql
   source database.sql;
   ```
   *(Or copy and paste the contents of `database.sql` into MySQL Workbench and execute).*

### Option B: Installing MySQL on macOS using Homebrew (if not yet installed)
```bash
# 1. Install MySQL via Homebrew
brew install mysql

# 2. Start the MySQL background service
brew services start mysql

# 3. Secure MySQL installation (optional for local development)
mysql_secure_installation

# 4. Initialize EduPulse database
mysql -u root < database.sql
```

---

## ⚙️ 8. Environment Configuration (`.env`)

1. Copy `.env.example` to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and verify your credentials:
   ```ini
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_actual_mysql_password
   MYSQL_DATABASE=edupulse_db
   ```
*(Note: Never commit `.env` to Git. It is already included in `.gitignore`.)*

---

## 🚀 9. Commands to Launch the Application

Launch the Streamlit web application:
```bash
python3 -m streamlit run app.py
```
Or simply:
```bash
streamlit run app.py
```

The application will open in your default browser at:
```text
http://localhost:8501
```

---

## 📥 10. How to Import Sample CSV Files

Sample data files are provided in the `data/` folder for testing:
1. Start the application and navigate to **Reports & Data Import** in the sidebar.
2. Under the **Batch CSV Import** tab:
   - **Step 1:** Upload `data/sample_students.csv` into the **Upload Student Profiles CSV** uploader.
   - Inspect the preview table and click **Confirm & Import Students to MySQL**.
   - **Step 2:** Upload `data/sample_performance.csv` into the **Upload Performance Records CSV** uploader.
   - Click **Confirm & Import Performance Records**.
3. Navigate to **Dashboard** or **Academic Insights** to see live calculations and interactive Plotly charts immediately!

---

## 🧪 11. Testing the Application

The test suite contains **34 comprehensive unit tests** testing boundary validation, KPI calculations, student-level aggregations, academic advisory rules, and database transaction rollback.

Tests can be executed using either `pytest` or Python's built-in `unittest` runner:

### Running with Pytest:
```bash
python3 -m pytest tests/ -v
```

### Running with Python Unittest:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

All unit tests are designed to execute independently of an active MySQL database using synthetic DataFrames and mock connections.

---

## 🔧 12. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `MySQL Connection Error [2003]` | MySQL server daemon is not running. | Run `brew services start mysql` or start MySQL in System Settings / MySQL Workbench. |
| `MySQL Connection Error [1045]: Access denied` | Incorrect username or password in `.env`. | Open `.env` and enter the correct `MYSQL_USER` and `MYSQL_PASSWORD`. |
| `Table 'edupulse_db.students' doesn't exist` | Schema was not initialized. | Run `mysql -u root -p < database.sql` or click the "Attempt Auto-Initialize Database Schema" button on the app screen. |
| `Student ID already exists` | Attempting to enroll a student with an ID already present. | Use a unique Student ID or update the existing student on the **Student Records** page. |
| `Student ID not found in students table` during CSV import | Performance CSV contains student IDs that are not enrolled. | Import `sample_students.csv` first before importing `sample_performance.csv`. |

---

## 📸 13. Application Screenshots

### Dashboard Overview
*(Placeholder: Live interactive KPI cards and Plotly analytics)*
```text
+---------------------------------------------------------------------------------------+
| 🎓 EduPulse — Student Performance Analytics Hub                                      |
+---------------------------------------------------------------------------------------+
| Total Students: 12 | Total Records: 30 | Avg Marks: 71.4/100 | Pass Rate: 83.3%       |
+---------------------------------------------------------------------------------------+
| [Plotly: Marks by Subject]           | [Plotly: Marks by Department]                 |
| [Plotly: Marks Distribution]          | [Plotly: Attendance vs Marks (Scatter)]       |
| [Plotly: Assignment Scores by Subj]   | [Plotly: Semester-wise Performance Trend]     |
+---------------------------------------------------------------------------------------+
```

### Academic Insights & Mentoring View
*(Placeholder: Rule-based recommendation engine with actionable faculty interventions)*
```text
+---------------------------------------------------------------------------------------+
| Academic Support: 4 | Attendance Review: 6 | Assignment Coaching: 5 | High Honors: 14 |
+---------------------------------------------------------------------------------------+
| ID     | Student Name | Subject           | Reason                 | Suggestion       |
| STU103 | Rohan Verma  | Computer Networks | Marks (35.0) < 40.0    | 1-on-1 tutoring  |
| STU105 | Kavya Reddy  | Discrete Math     | Attendance (62.0%)<75% | Advisory notice  |
+---------------------------------------------------------------------------------------+
```

---

## 📜 14. License & Academic Disclaimer

EduPulse is an educational mini-project demonstration. All metric calculations and advisory recommendations are decision-support indicators designed for faculty assistance and do not predict personal outcomes.
