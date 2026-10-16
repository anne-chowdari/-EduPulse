"""
Analytics, rule-based recommendation engine, and validation module for EduPulse.
Calculates dynamic KPIs, separates student-level and subject-level aggregations,
and generates rule-based recommendations with actionable suggestions.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# -----------------------------------------------------------------------------
# INPUT VALIDATION FUNCTIONS
# -----------------------------------------------------------------------------

def validate_student_inputs(
    student_id: str,
    student_name: str,
    department: str,
    semester: Any,
) -> Tuple[bool, str]:
    """Validate student form inputs."""
    sid = str(student_id or "").strip()
    name = str(student_name or "").strip()
    dept = str(department or "").strip()

    if not sid:
        return False, "Student ID cannot be empty."
    if len(sid) > 50:
        return False, "Student ID must not exceed 50 characters."
    if not name:
        return False, "Student Name cannot be empty."
    if len(name) > 100:
        return False, "Student Name must not exceed 100 characters."
    if not dept:
        return False, "Department cannot be empty."

    try:
        sem = int(semester)
        if not (1 <= sem <= 12):
            return False, f"Semester must be between 1 and 12 (received {sem})."
    except (ValueError, TypeError):
        return False, "Semester must be a valid integer."

    return True, "Valid student data."


def validate_performance_inputs(
    student_id: str,
    subject: str,
    marks: Any,
    attendance: Any,
    study_hours: Any,
    assignment_score: Any,
    record_date: Any,
) -> Tuple[bool, str]:
    """Validate subject performance inputs."""
    sid = str(student_id or "").strip()
    subj = str(subject or "").strip()

    if not sid:
        return False, "Student ID cannot be empty."
    if not subj:
        return False, "Subject cannot be empty."

    try:
        m = float(marks)
        if not (0.0 <= m <= 100.0):
            return False, f"Marks must be between 0 and 100 (received {m})."
    except (ValueError, TypeError):
        return False, "Marks must be a valid numeric value."

    try:
        att = float(attendance)
        if not (0.0 <= att <= 100.0):
            return False, f"Attendance must be between 0 and 100% (received {att})."
    except (ValueError, TypeError):
        return False, "Attendance must be a valid numeric value."

    try:
        hrs = float(study_hours)
        if hrs < 0.0:
            return False, f"Daily study hours cannot be negative (received {hrs})."
        if hrs > 24.0:
            return False, f"Daily study hours cannot exceed 24 hours (received {hrs})."
    except (ValueError, TypeError):
        return False, "Daily study hours must be a valid numeric value."

    try:
        asg = float(assignment_score)
        if not (0.0 <= asg <= 100.0):
            return False, f"Assignment score must be between 0 and 100 (received {asg})."
    except (ValueError, TypeError):
        return False, "Assignment score must be a valid numeric value."

    if not record_date:
        return False, "Record date cannot be empty."

    return True, "Valid performance data."


def validate_student_csv(df: pd.DataFrame) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Validate DataFrame uploaded via CSV for student registration.
    Required columns: student_id, student_name, department, semester.
    """
    required_cols = {"student_id", "student_name", "department", "semester"}
    cols_present = {c.strip().lower() for c in df.columns}

    if not required_cols.issubset(cols_present):
        missing = required_cols - cols_present
        return False, f"Missing required CSV columns: {', '.join(missing)}", []

    # Standardize column names
    col_map = {c: c.strip().lower() for c in df.columns}
    normalized = df.rename(columns=col_map)

    valid_records = []
    seen_ids = set()

    for idx, row in normalized.iterrows():
        sid = str(row.get("student_id", "")).strip()
        name = str(row.get("student_name", "")).strip()
        dept = str(row.get("department", "")).strip()
        sem = row.get("semester")

        if not sid or pd.isna(sid):
            continue  # Blank line

        if sid in seen_ids:
            return False, f"Row {idx + 2}: Duplicate student_id '{sid}' inside the uploaded CSV file.", []
        seen_ids.add(sid)

        is_valid, msg = validate_student_inputs(sid, name, dept, sem)
        if not is_valid:
            return False, f"Row {idx + 2}: {msg}", []

        valid_records.append({
            "student_id": sid,
            "student_name": name,
            "department": dept,
            "semester": int(sem),
        })

    if not valid_records:
        return False, "CSV contains no valid student rows.", []

    return True, f"Successfully parsed and validated {len(valid_records)} student records.", valid_records


def validate_performance_csv(
    df: pd.DataFrame,
    existing_student_ids: Optional[set] = None,
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Validate DataFrame uploaded via CSV for performance records.
    Required columns: student_id, subject, marks, attendance, study_hours, assignment_score, record_date.
    """
    required_cols = {
        "student_id", "subject", "marks", "attendance", 
        "study_hours", "assignment_score", "record_date"
    }
    cols_present = {c.strip().lower() for c in df.columns}

    if not required_cols.issubset(cols_present):
        missing = required_cols - cols_present
        return False, f"Missing required CSV columns: {', '.join(missing)}", []

    col_map = {c: c.strip().lower() for c in df.columns}
    normalized = df.rename(columns=col_map)

    valid_records = []

    for idx, row in normalized.iterrows():
        sid = str(row.get("student_id", "")).strip()
        subj = str(row.get("subject", "")).strip()
        m = row.get("marks")
        att = row.get("attendance")
        hrs = row.get("study_hours")
        asg = row.get("assignment_score")
        rdate = row.get("record_date")

        if not sid or pd.isna(sid):
            continue

        if existing_student_ids is not None and sid not in existing_student_ids:
            return False, f"Row {idx + 2}: Student ID '{sid}' does not exist in the database. Please register students first.", []

        is_valid, msg = validate_performance_inputs(sid, subj, m, att, hrs, asg, rdate)
        if not is_valid:
            return False, f"Row {idx + 2} ({sid} - {subj}): {msg}", []

        valid_records.append({
            "student_id": sid,
            "subject": subj,
            "marks": float(m),
            "attendance": float(att),
            "study_hours": float(hrs),
            "assignment_score": float(asg),
            "record_date": str(rdate).split(" ")[0].strip(),
        })

    if not valid_records:
        return False, "CSV contains no valid performance rows.", []

    return True, f"Successfully parsed and validated {len(valid_records)} performance records.", valid_records


# -----------------------------------------------------------------------------
# DYNAMIC KPI AND AGGREGATION ENGINE
# -----------------------------------------------------------------------------

def calculate_kpis(
    merged_df: pd.DataFrame,
    students_df: Optional[pd.DataFrame] = None,
    pass_mark_threshold: float = 40.0,
    support_marks_threshold: float = 40.0,
    support_attendance_threshold: float = 75.0,
) -> Dict[str, Any]:
    """
    Calculate dynamic KPIs using clearly documented aggregation rules:
    
    1. Total Students: Count of distinct students registered (from students_df or merged_df).
    2. Total Records: Total number of individual subject-level assessments recorded.
    3. Average Marks: Arithmetic mean of all subject marks across filtered records.
    4. Average Attendance: Arithmetic mean of attendance percentages across records.
    5. Pass Percentage: Calculated at STUDENT LEVEL (percentage of students whose overall
       average marks across taken subjects meet or exceed the pass threshold). This prevents
       students with 5 records from skewing student pass rates.
    6. Students Needing Support: Unique students who have either:
       - An average attendance below the threshold (e.g. < 75%), OR
       - At least one subject score below the academic support threshold (e.g. < 40%).
    """
    if merged_df is None or merged_df.empty:
        # Fallback if students exist but no performance records are recorded yet
        total_st = len(students_df) if students_df is not None and not students_df.empty else 0
        return {
            "total_students": total_st,
            "total_records": 0,
            "avg_marks": 0.0,
            "avg_attendance": 0.0,
            "avg_study_hours": 0.0,
            "avg_assignment": 0.0,
            "pass_percentage": 0.0,
            "students_needing_support": 0,
            "has_data": False,
        }

    # Distinct student count
    if students_df is not None and not students_df.empty:
        # If merged_df is filtered, count distinct students present in filtered data
        total_students = merged_df["student_id"].nunique()
    else:
        total_students = merged_df["student_id"].nunique()

    total_records = len(merged_df)
    avg_marks = float(merged_df["marks"].mean())
    avg_attendance = float(merged_df["attendance"].mean())
    avg_study_hours = float(merged_df["study_hours"].mean())
    avg_assignment = float(merged_df["assignment_score"].mean())

    # STUDENT-LEVEL AGGREGATION: Group by student_id to calculate unbiased student metrics
    student_grouped = merged_df.groupby("student_id").agg(
        student_avg_marks=("marks", "mean"),
        student_min_marks=("marks", "min"),
        student_avg_att=("attendance", "mean")
    ).reset_index()

    # Pass Percentage: students with average marks >= pass_mark_threshold
    passing_students = (student_grouped["student_avg_marks"] >= pass_mark_threshold).sum()
    pass_percentage = float((passing_students / len(student_grouped)) * 100.0) if len(student_grouped) > 0 else 0.0

    # Students Needing Support: student has min marks < support_threshold OR avg attendance < att_threshold
    support_mask = (
        (student_grouped["student_min_marks"] < support_marks_threshold) |
        (student_grouped["student_avg_att"] < support_attendance_threshold)
    )
    students_needing_support = int(support_mask.sum())

    return {
        "total_students": total_students,
        "total_records": total_records,
        "avg_marks": round(avg_marks, 2),
        "avg_attendance": round(avg_attendance, 2),
        "avg_study_hours": round(avg_study_hours, 1),
        "avg_assignment": round(avg_assignment, 2),
        "pass_percentage": round(pass_percentage, 1),
        "students_needing_support": students_needing_support,
        "has_data": True,
    }


def get_student_summary(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce an overall student-level performance summary table.
    Consolidates multiple subject records into single-student academic overview.
    """
    if merged_df is None or merged_df.empty:
        return pd.DataFrame(columns=[
            "student_id", "student_name", "department", "semester",
            "subjects_taken", "avg_marks", "min_marks", "max_marks",
            "avg_attendance", "avg_study_hours", "avg_assignment", "status"
        ])

    grouped = merged_df.groupby(["student_id", "student_name", "department", "semester"]).agg(
        subjects_taken=("subject", "count"),
        avg_marks=("marks", "mean"),
        min_marks=("marks", "min"),
        max_marks=("marks", "max"),
        avg_attendance=("attendance", "mean"),
        avg_study_hours=("study_hours", "mean"),
        avg_assignment=("assignment_score", "mean")
    ).reset_index()

    grouped["avg_marks"] = grouped["avg_marks"].round(2)
    grouped["min_marks"] = grouped["min_marks"].round(2)
    grouped["max_marks"] = grouped["max_marks"].round(2)
    grouped["avg_attendance"] = grouped["avg_attendance"].round(2)
    grouped["avg_study_hours"] = grouped["avg_study_hours"].round(1)
    grouped["avg_assignment"] = grouped["avg_assignment"].round(2)

    def determine_status(row):
        if row["min_marks"] < 40.0 or row["avg_attendance"] < 75.0:
            return "Needs Support"
        elif row["avg_marks"] >= 75.0:
            return "Distinction / Strong"
        return "Good Standing"

    grouped["status"] = grouped.apply(determine_status, axis=1)
    return grouped.sort_values(by="avg_marks", ascending=False)


# -----------------------------------------------------------------------------
# RULE-BASED ACADEMIC INSIGHTS AND RECOMMENDATION ENGINE
# -----------------------------------------------------------------------------

def generate_recommendations(
    merged_df: pd.DataFrame,
    marks_threshold: float = 40.0,
    attendance_threshold: float = 75.0,
    assignment_threshold: float = 50.0,
    high_marks_threshold: float = 75.0,
) -> List[Dict[str, Any]]:
    """
    Rule-based Academic Insights Engine.
    
    Generates transparent, explainable recommendations based on configurable thresholds:
    1. Marks below threshold (default < 40): Academic Subject Support
    2. Attendance below threshold (default < 75%): Attendance Review
    3. Assignment score below threshold (default < 50): Assignment Support
    4. Marks at or above threshold (default >= 75): Strong Subject Performance
    
    Important Pedagogical Notice:
    These recommendations represent decision-support indicators for faculty review.
    They do not make unsupported claims about student aptitude or personal outcomes.
    """
    if merged_df is None or merged_df.empty:
        return []

    recommendations: List[Dict[str, Any]] = []

    for _, row in merged_df.iterrows():
        sid = str(row["student_id"])
        sname = str(row.get("student_name", "Unknown"))
        dept = str(row.get("department", "Unknown"))
        subj = str(row.get("subject", "General"))
        marks = float(row.get("marks", 0.0))
        att = float(row.get("attendance", 0.0))
        asg = float(row.get("assignment_score", 0.0))
        rdate = str(row.get("record_date", ""))

        # Rule 1: Subject-level academic support (marks < 40)
        if marks < marks_threshold:
            recommendations.append({
                "student_id": sid,
                "student_name": sname,
                "department": dept,
                "subject": subj,
                "record_date": rdate,
                "category": "Academic Support",
                "severity": "High",
                "metric_name": "Marks",
                "metric_value": marks,
                "threshold": marks_threshold,
                "reason": f"Subject score ({marks:.1f}/100) is below the minimum threshold ({marks_threshold:.1f}).",
                "actionable_suggestion": "Schedule 1-on-1 tutoring, provide foundational revision sheets, and recommend focused practice problem sets."
            })

        # Rule 2: Attendance review (attendance < 75%)
        if att < attendance_threshold:
            recommendations.append({
                "student_id": sid,
                "student_name": sname,
                "department": dept,
                "subject": subj,
                "record_date": rdate,
                "category": "Attendance Review",
                "severity": "Medium",
                "metric_name": "Attendance",
                "metric_value": att,
                "threshold": attendance_threshold,
                "reason": f"Class attendance ({att:.1f}%) is below the institutional benchmark ({attendance_threshold:.1f}%).",
                "actionable_suggestion": "Issue an attendance advisory notice, initiate student counseling, and monitor weekly lecture attendance."
            })

        # Rule 3: Assignment support (assignment score < 50)
        if asg < assignment_threshold:
            recommendations.append({
                "student_id": sid,
                "student_name": sname,
                "department": dept,
                "subject": subj,
                "record_date": rdate,
                "category": "Assignment Support",
                "severity": "Medium",
                "metric_name": "Assignment Score",
                "metric_value": asg,
                "threshold": assignment_threshold,
                "reason": f"Continuous assignment score ({asg:.1f}/100) is below expected benchmark ({assignment_threshold:.1f}).",
                "actionable_suggestion": "Provide rubrics and detailed written feedback on submissions; organize an assignment walk-through clinic."
            })

        # Rule 4: Strong subject performance (marks >= 75)
        if marks >= high_marks_threshold:
            recommendations.append({
                "student_id": sid,
                "student_name": sname,
                "department": dept,
                "subject": subj,
                "record_date": rdate,
                "category": "High Achievement",
                "severity": "Positive",
                "metric_name": "Marks",
                "metric_value": marks,
                "threshold": high_marks_threshold,
                "reason": f"Demonstrated high academic mastery ({marks:.1f}/100) meeting or exceeding {high_marks_threshold:.1f}.",
                "actionable_suggestion": "Encourage advanced research projects, recommend peer tutoring leadership roles, and evaluate for academic honors."
            })

    return recommendations


def get_recommendation_summary(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Aggregate counts for each recommendation category."""
    counts = {
        "Academic Support": 0,
        "Attendance Review": 0,
        "Assignment Support": 0,
        "High Achievement": 0,
    }
    for rec in recommendations:
        cat = rec.get("category", "")
        if cat in counts:
            counts[cat] += 1
    return counts


# -----------------------------------------------------------------------------
# PLOTLY INTERACTIVE CHART BUILDERS
# -----------------------------------------------------------------------------

CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", "color": "#1F2937"},
    "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
}


def create_marks_by_subject_chart(df: pd.DataFrame) -> go.Figure:
    """Average Marks by Subject with color gradient."""
    if df.empty:
        return go.Figure()

    subj_avg = df.groupby("subject")["marks"].mean().reset_index()
    subj_avg["marks"] = subj_avg["marks"].round(2)
    subj_avg = subj_avg.sort_values(by="marks", ascending=True)

    fig = px.bar(
        subj_avg,
        x="marks",
        y="subject",
        orientation="h",
        text="marks",
        title="Average Marks by Subject",
        labels={"marks": "Average Marks (out of 100)", "subject": "Subject"},
        color="marks",
        color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", marker_line_width=1, marker_line_color="#1E3A8A")
    fig.update_layout(
        **CHART_THEME,
        coloraxis_showscale=False,
        xaxis={"range": [0, 105]},
        height=360,
    )
    return fig


def create_marks_by_department_chart(df: pd.DataFrame) -> go.Figure:
    """Average Marks by Department comparison."""
    if df.empty:
        return go.Figure()

    dept_avg = df.groupby("department")["marks"].mean().reset_index()
    dept_avg["marks"] = dept_avg["marks"].round(2)
    dept_avg = dept_avg.sort_values(by="marks", ascending=False)

    fig = px.bar(
        dept_avg,
        x="department",
        y="marks",
        text="marks",
        title="Average Marks by Department",
        labels={"marks": "Average Marks", "department": "Department"},
        color="department",
        color_discrete_sequence=["#1E3A8A", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"],
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        **CHART_THEME,
        showlegend=False,
        yaxis={"range": [0, 105]},
        height=360,
    )
    return fig


def create_performance_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Histogram with KDE overlay for marks distribution."""
    if df.empty:
        return go.Figure()

    fig = px.histogram(
        df,
        x="marks",
        nbins=20,
        title="Marks Distribution Across Records",
        labels={"marks": "Marks (0 - 100)"},
        color_discrete_sequence=["#2563EB"],
        opacity=0.85,
    )
    # Add vertical line for passing threshold (40)
    fig.add_vline(
        x=40,
        line_width=2,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text="Pass Cutoff (40)",
        annotation_position="top left",
    )
    fig.update_layout(
        **CHART_THEME,
        xaxis={"range": [0, 100]},
        yaxis_title="Record Count",
        height=360,
    )
    return fig


def create_attendance_vs_marks_chart(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: Attendance vs Marks with Department highlighting."""
    if df.empty:
        return go.Figure()

    fig = px.scatter(
        df,
        x="attendance",
        y="marks",
        color="department",
        size="study_hours",
        hover_data=["student_id", "student_name", "subject", "assignment_score"],
        title="Attendance (%) vs Marks (Bubble size: Daily Study Hours)",
        labels={
            "attendance": "Class Attendance (%)",
            "marks": "Marks (out of 100)",
            "study_hours": "Study Hrs/Day",
            "department": "Dept",
        },
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.add_hline(y=40, line_dash="dot", line_color="#DC2626", annotation_text="Pass Benchmark (40)")
    fig.add_vline(x=75, line_dash="dot", line_color="#F59E0B", annotation_text="Min Attendance (75%)")
    fig.update_layout(
        **CHART_THEME,
        xaxis={"range": [0, 105]},
        yaxis={"range": [0, 105]},
        height=380,
    )
    return fig


def create_assignment_by_subject_chart(df: pd.DataFrame) -> go.Figure:
    """Box plot of assignment scores across subjects."""
    if df.empty:
        return go.Figure()

    fig = px.box(
        df,
        x="subject",
        y="assignment_score",
        color="subject",
        title="Assignment Scores Distribution by Subject",
        labels={"assignment_score": "Assignment Score (0-100)", "subject": "Subject"},
        color_discrete_sequence=px.colors.qualitative.Prism,
    )
    fig.update_layout(
        **CHART_THEME,
        showlegend=False,
        yaxis={"range": [0, 105]},
        height=360,
    )
    return fig


def create_semester_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Semester-wise academic performance trend."""
    if df.empty:
        return go.Figure()

    sem_avg = df.groupby("semester").agg(
        avg_marks=("marks", "mean"),
        avg_attendance=("attendance", "mean")
    ).reset_index().sort_values(by="semester")

    sem_avg["avg_marks"] = sem_avg["avg_marks"].round(2)
    sem_avg["avg_attendance"] = sem_avg["avg_attendance"].round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"Sem {s}" for s in sem_avg["semester"]],
        y=sem_avg["avg_marks"],
        name="Average Marks",
        marker_color="#2563EB",
        text=sem_avg["avg_marks"],
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=[f"Sem {s}" for s in sem_avg["semester"]],
        y=sem_avg["avg_attendance"],
        name="Average Attendance (%)",
        mode="lines+markers",
        line={"color": "#10B981", "width": 3},
        marker={"size": 8},
    ))
    fig.update_layout(
        **CHART_THEME,
        title="Semester-wise Performance & Attendance Trends",
        xaxis_title="Semester",
        yaxis={"range": [0, 110], "title": "Score / Percentage"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        height=360,
    )
    return fig
