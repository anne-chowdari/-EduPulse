"""
EduPulse — Graphical Reports & Visual Analytics Module.
Provides advanced analytics calculations, specialized Plotly chart builders,
and comprehensive formatted PDF academic report generation using ReportLab.
"""

from datetime import datetime, date
import io
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
)


CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", "color": "#1F2937"},
    "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
}


# =============================================================================
# 1. ADVANCED ANALYTICAL CALCULATIONS
# =============================================================================

def get_top_performing_students(merged_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Identify top-performing students based on average marks across all subjects enrolled.
    Aggregation method: Group by student_id, calculate mean marks, min marks, max marks,
    mean attendance, and total subjects. Ranked by avg_marks descending.
    """
    if merged_df is None or merged_df.empty:
        return pd.DataFrame(columns=[
            "rank", "student_id", "student_name", "department", "semester",
            "subjects_taken", "avg_marks", "min_marks", "max_marks", "avg_attendance", "standing"
        ])

    grouped = merged_df.groupby(["student_id", "student_name", "department", "semester"]).agg(
        subjects_taken=("subject", "count"),
        avg_marks=("marks", "mean"),
        min_marks=("marks", "min"),
        max_marks=("marks", "max"),
        avg_attendance=("attendance", "mean"),
    ).reset_index()

    grouped["avg_marks"] = grouped["avg_marks"].round(2)
    grouped["min_marks"] = grouped["min_marks"].round(2)
    grouped["max_marks"] = grouped["max_marks"].round(2)
    grouped["avg_attendance"] = grouped["avg_attendance"].round(2)

    # Sort descending by average marks
    sorted_df = grouped.sort_values(by=["avg_marks", "avg_attendance"], ascending=[False, False]).reset_index(drop=True)
    sorted_df.insert(0, "rank", range(1, len(sorted_df) + 1))

    def assign_standing(score: float) -> str:
        if score >= 85.0:
            return "🌟 High Distinction"
        elif score >= 75.0:
            return "🎖️ Distinction"
        elif score >= 60.0:
            return "📘 First Class"
        elif score >= 40.0:
            return "📗 Pass Class"
        return "🚨 Academic Support"

    sorted_df["standing"] = sorted_df["avg_marks"].apply(assign_standing)
    return sorted_df.head(top_n)


def get_subject_performance_analysis(merged_df: pd.DataFrame, pass_threshold: float = 40.0) -> pd.DataFrame:
    """
    Compute subject-level performance metrics, assessment counts, and pass rates.
    Subject pass rate = (Count of subject assessments with marks >= pass_threshold / Total assessments in subject) * 100
    """
    if merged_df is None or merged_df.empty:
        return pd.DataFrame(columns=[
            "subject", "total_assessments", "avg_marks", "min_marks", "max_marks",
            "pass_percentage", "avg_attendance", "avg_assignment", "status"
        ])

    records: List[Dict[str, Any]] = []
    for subj, group in merged_df.groupby("subject"):
        total = len(group)
        avg_m = float(group["marks"].mean())
        min_m = float(group["marks"].min())
        max_m = float(group["marks"].max())
        passes = (group["marks"] >= pass_threshold).sum()
        pass_pct = (passes / total) * 100.0 if total > 0 else 0.0
        avg_att = float(group["attendance"].mean())
        avg_asg = float(group["assignment_score"].mean())

        status = "Needs Attention" if (avg_m < 50.0 or pass_pct < 70.0) else "Satisfactory"

        records.append({
            "subject": subj,
            "total_assessments": total,
            "avg_marks": round(avg_m, 2),
            "min_marks": round(min_m, 2),
            "max_marks": round(max_m, 2),
            "pass_percentage": round(pass_pct, 1),
            "avg_attendance": round(avg_att, 1),
            "avg_assignment": round(avg_asg, 1),
            "status": status,
        })

    df = pd.DataFrame(records)
    # Sort ascending by avg_marks so subjects needing most academic attention appear first
    return df.sort_values(by="avg_marks", ascending=True).reset_index(drop=True)


def get_study_hours_analysis(merged_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Analyze correlation and associations between daily study hours and academic marks.
    Returns:
    1. Binned study hours breakdown DataFrame (< 2h, 2-4h, 4-6h, > 6h)
    2. Department-wise average study hours DataFrame
    3. Correlation coefficient (Pearson r)
    """
    empty_binned = pd.DataFrame(columns=["study_hour_range", "record_count", "avg_marks", "avg_attendance", "avg_assignment"])
    empty_dept = pd.DataFrame(columns=["department", "avg_study_hours"])

    if merged_df is None or merged_df.empty:
        return empty_binned, empty_dept, 0.0

    df = merged_df.copy()

    # Define bins
    bins = [-0.1, 2.0, 4.0, 6.0, 24.0]
    labels = ["< 2 hrs/day", "2 – 4 hrs/day", "4 – 6 hrs/day", "> 6 hrs/day"]
    df["study_hour_range"] = pd.cut(df["study_hours"], bins=bins, labels=labels)

    binned = df.groupby("study_hour_range", observed=False).agg(
        record_count=("marks", "count"),
        avg_marks=("marks", "mean"),
        avg_attendance=("attendance", "mean"),
        avg_assignment=("assignment_score", "mean")
    ).reset_index()

    binned["avg_marks"] = binned["avg_marks"].fillna(0.0).round(2)
    binned["avg_attendance"] = binned["avg_attendance"].fillna(0.0).round(2)
    binned["avg_assignment"] = binned["avg_assignment"].fillna(0.0).round(2)

    # Department average study hours
    dept_study = df.groupby("department").agg(
        avg_study_hours=("study_hours", "mean"),
        student_count=("student_id", "nunique")
    ).reset_index()
    dept_study["avg_study_hours"] = dept_study["avg_study_hours"].round(1)

    # Correlation calculation
    correlation = 0.0
    if len(df) > 1 and df["study_hours"].std() > 0 and df["marks"].std() > 0:
        corr_val = df["study_hours"].corr(df["marks"])
        correlation = round(float(corr_val), 3) if not pd.isna(corr_val) else 0.0

    return binned, dept_study, correlation


def get_attendance_analysis_data(merged_df: pd.DataFrame, threshold: float = 75.0) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    """
    Analyze attendance records, identify students with low attendance, and compute quadrant distribution.
    """
    empty_dept = pd.DataFrame(columns=["department", "avg_attendance", "student_count"])
    empty_low = pd.DataFrame(columns=["student_id", "student_name", "department", "semester", "avg_attendance", "min_attendance"])
    quadrants = {"High Att & Pass": 0, "High Att & Need Support": 0, "Low Att & Pass": 0, "Low Att & Need Support": 0}

    if merged_df is None or merged_df.empty:
        return empty_dept, empty_low, quadrants

    # Dept attendance
    dept_att = merged_df.groupby("department").agg(
        avg_attendance=("attendance", "mean"),
        student_count=("student_id", "nunique")
    ).reset_index()
    dept_att["avg_attendance"] = dept_att["avg_attendance"].round(2)

    # Students with low attendance
    student_att = merged_df.groupby(["student_id", "student_name", "department", "semester"]).agg(
        avg_attendance=("attendance", "mean"),
        min_attendance=("attendance", "min"),
        avg_marks=("marks", "mean")
    ).reset_index()

    student_att["avg_attendance"] = student_att["avg_attendance"].round(2)
    student_att["min_attendance"] = student_att["min_attendance"].round(2)
    student_att["avg_marks"] = student_att["avg_marks"].round(2)

    low_att_students = student_att[student_att["avg_attendance"] < threshold].copy()
    low_att_students = low_att_students.sort_values(by="avg_attendance", ascending=True)

    # Quadrants
    for _, row in student_att.iterrows():
        att_high = row["avg_attendance"] >= threshold
        marks_pass = row["avg_marks"] >= 40.0

        if att_high and marks_pass:
            quadrants["High Att & Pass"] += 1
        elif att_high and not marks_pass:
            quadrants["High Att & Need Support"] += 1
        elif not att_high and marks_pass:
            quadrants["Low Att & Pass"] += 1
        else:
            quadrants["Low Att & Need Support"] += 1

    return dept_att, low_att_students, quadrants


def get_overall_academic_summary(
    merged_df: pd.DataFrame,
    students_df: Optional[pd.DataFrame] = None,
    pass_threshold: float = 40.0,
    support_attendance_threshold: float = 75.0,
) -> Dict[str, Any]:
    """
    Compute comprehensive institutional summary metrics.
    Clearly distinguishes student-level pass percentage from assessment-level pass percentage.
    """
    if merged_df is None or merged_df.empty:
        total_st = len(students_df) if students_df is not None and not students_df.empty else 0
        return {
            "total_students": total_st,
            "total_assessments": 0,
            "overall_avg_marks": 0.0,
            "overall_avg_attendance": 0.0,
            "overall_avg_study_hours": 0.0,
            "overall_avg_assignment": 0.0,
            "student_pass_rate": 0.0,
            "assessment_pass_rate": 0.0,
            "students_needing_support": 0,
            "dept_comparison": pd.DataFrame(),
            "sem_comparison": pd.DataFrame(),
            "has_data": False,
        }

    total_students = merged_df["student_id"].nunique()
    total_assessments = len(merged_df)
    avg_marks = float(merged_df["marks"].mean())
    avg_attendance = float(merged_df["attendance"].mean())
    avg_study_hours = float(merged_df["study_hours"].mean())
    avg_assignment = float(merged_df["assignment_score"].mean())

    # 1. Assessment-Level Pass Rate: percentage of all recorded subject exams >= pass_threshold
    passing_assessments = (merged_df["marks"] >= pass_threshold).sum()
    assessment_pass_rate = (passing_assessments / total_assessments) * 100.0 if total_assessments > 0 else 0.0

    # 2. Student-Level Pass Rate: percentage of students whose overall mean marks >= pass_threshold
    student_grp = merged_df.groupby("student_id").agg(
        student_avg_marks=("marks", "mean"),
        student_min_marks=("marks", "min"),
        student_avg_att=("attendance", "mean")
    ).reset_index()

    passing_students = (student_grp["student_avg_marks"] >= pass_threshold).sum()
    student_pass_rate = (passing_students / len(student_grp)) * 100.0 if len(student_grp) > 0 else 0.0

    # Students Needing Support: min marks < 40 OR avg attendance < 75%
    support_mask = (
        (student_grp["student_min_marks"] < pass_threshold) |
        (student_grp["student_avg_att"] < support_attendance_threshold)
    )
    students_needing_support = int(support_mask.sum())

    # Department comparison
    dept_comp = merged_df.groupby("department").agg(
        students=("student_id", "nunique"),
        assessments=("record_id", "count"),
        avg_marks=("marks", "mean"),
        avg_attendance=("attendance", "mean"),
        avg_study_hours=("study_hours", "mean"),
    ).reset_index()
    dept_comp["avg_marks"] = dept_comp["avg_marks"].round(2)
    dept_comp["avg_attendance"] = dept_comp["avg_attendance"].round(2)
    dept_comp["avg_study_hours"] = dept_comp["avg_study_hours"].round(1)

    # Semester comparison
    sem_comp = merged_df.groupby("semester").agg(
        students=("student_id", "nunique"),
        assessments=("record_id", "count"),
        avg_marks=("marks", "mean"),
        avg_attendance=("attendance", "mean"),
    ).reset_index().sort_values(by="semester")
    sem_comp["avg_marks"] = sem_comp["avg_marks"].round(2)
    sem_comp["avg_attendance"] = sem_comp["avg_attendance"].round(2)

    return {
        "total_students": total_students,
        "total_assessments": total_assessments,
        "overall_avg_marks": round(avg_marks, 2),
        "overall_avg_attendance": round(avg_attendance, 2),
        "overall_avg_study_hours": round(avg_study_hours, 1),
        "overall_avg_assignment": round(avg_assignment, 2),
        "student_pass_rate": round(student_pass_rate, 1),
        "assessment_pass_rate": round(assessment_pass_rate, 1),
        "students_needing_support": students_needing_support,
        "dept_comparison": dept_comp,
        "sem_comparison": sem_comp,
        "has_data": True,
    }


def generate_key_observations(merged_df: pd.DataFrame, pass_threshold: float = 40.0) -> List[str]:
    """
    Synthesize factual, data-driven key academic observations from the filtered dataset.
    """
    if merged_df is None or merged_df.empty:
        return ["No academic records are available for the current filter selection."]

    observations = []

    # Overall volume
    total_st = merged_df["student_id"].nunique()
    total_rec = len(merged_df)
    avg_m = merged_df["marks"].mean()
    observations.append(
        f"Analyzed {total_rec} performance assessment(s) across {total_st} unique student(s), with an institutional mean mark of {avg_m:.1f}/100."
    )

    # Subject insights
    subj_avg = merged_df.groupby("subject")["marks"].mean()
    if not subj_avg.empty:
        best_subj = subj_avg.idxmax()
        worst_subj = subj_avg.idxmin()
        observations.append(
            f"Highest-performing course is '{best_subj}' (mean: {subj_avg[best_subj]:.1f}/100), while '{worst_subj}' recorded the lowest average mark ({subj_avg[worst_subj]:.1f}/100)."
        )

    # Department insights
    dept_avg = merged_df.groupby("department")["marks"].mean()
    if len(dept_avg) > 1:
        top_dept = dept_avg.idxmax()
        observations.append(
            f"Department '{top_dept}' achieved the leading academic average at {dept_avg[top_dept]:.1f}/100."
        )

    # Attendance insights
    low_att_cnt = (merged_df["attendance"] < 75.0).sum()
    if low_att_cnt > 0:
        observations.append(
            f"Identified {low_att_cnt} subject assessment(s) where attendance fell below the 75% institutional compliance requirement."
        )
    else:
        observations.append("Class attendance remains above the 75% institutional compliance benchmark across all evaluated records.")

    # Study hours association
    if len(merged_df) > 1 and merged_df["study_hours"].std() > 0:
        corr = merged_df["study_hours"].corr(merged_df["marks"])
        if not pd.isna(corr):
            direction = "positive" if corr > 0.2 else ("negative" if corr < -0.2 else "mild / neutral")
            observations.append(
                f"Data indicates a {direction} statistical correlation (r = {corr:.2f}) between logged daily study hours and examination scores."
            )

    return observations


# =============================================================================
# 2. SPECIALIZED PLOTLY CHART BUILDERS FOR GRAPHICAL REPORTS
# =============================================================================

def create_student_marks_bar_chart(merged_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Bar chart showing marks by student."""
    if merged_df is None or merged_df.empty:
        return go.Figure()

    stu_avg = merged_df.groupby(["student_id", "student_name"])["marks"].mean().reset_index()
    stu_avg["marks"] = stu_avg["marks"].round(2)
    stu_avg["label"] = stu_avg["student_name"] + " (" + stu_avg["student_id"] + ")"
    stu_avg = stu_avg.sort_values(by="marks", ascending=True).tail(top_n)

    # Colors: green if >= 75, blue if >= 40, red if < 40
    colors_list = [
        "#10B981" if m >= 75 else ("#2563EB" if m >= 40 else "#EF4444")
        for m in stu_avg["marks"]
    ]

    fig = px.bar(
        stu_avg,
        x="marks",
        y="label",
        orientation="h",
        text="marks",
        title=f"Average Marks by Student (Top {len(stu_avg)})",
        labels={"marks": "Average Marks (out of 100)", "label": "Student"},
    )
    fig.update_traces(
        marker_color=colors_list,
        texttemplate="%{text:.1f}",
        textposition="outside",
    )
    fig.add_vline(x=40, line_dash="dash", line_color="#EF4444", annotation_text="Pass Benchmark (40)")
    fig.update_layout(**CHART_THEME, xaxis={"range": [0, 105]}, height=380)
    return fig


def create_subject_marks_comparison_chart(merged_df: pd.DataFrame) -> go.Figure:
    """Grouped marks comparison across subjects."""
    if merged_df is None or merged_df.empty:
        return go.Figure()

    subj_stats = merged_df.groupby("subject").agg(
        avg_marks=("marks", "mean"),
        min_marks=("marks", "min"),
        max_marks=("marks", "max"),
    ).reset_index()

    subj_stats["avg_marks"] = subj_stats["avg_marks"].round(2)
    subj_stats["min_marks"] = subj_stats["min_marks"].round(2)
    subj_stats["max_marks"] = subj_stats["max_marks"].round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Min Score",
        x=subj_stats["subject"],
        y=subj_stats["min_marks"],
        marker_color="#93C5FD",
    ))
    fig.add_trace(go.Bar(
        name="Average Score",
        x=subj_stats["subject"],
        y=subj_stats["avg_marks"],
        marker_color="#2563EB",
    ))
    fig.add_trace(go.Bar(
        name="Max Score",
        x=subj_stats["subject"],
        y=subj_stats["max_marks"],
        marker_color="#1E3A8A",
    ))

    fig.add_hline(y=40, line_dash="dash", line_color="#EF4444", annotation_text="Pass Line (40)")
    fig.update_layout(
        **CHART_THEME,
        barmode="group",
        title="Subject Score Comparison (Min / Avg / Max)",
        yaxis={"range": [0, 110], "title": "Marks"},
        height=380,
    )
    return fig


def create_attendance_by_dept_chart(merged_df: pd.DataFrame) -> go.Figure:
    """Bar chart showing average attendance by department."""
    if merged_df is None or merged_df.empty:
        return go.Figure()

    dept_att = merged_df.groupby("department")["attendance"].mean().reset_index()
    dept_att["attendance"] = dept_att["attendance"].round(2)
    dept_att = dept_att.sort_values(by="attendance", ascending=False)

    fig = px.bar(
        dept_att,
        x="department",
        y="attendance",
        text="attendance",
        title="Average Attendance by Department (%)",
        labels={"attendance": "Average Attendance (%)", "department": "Department"},
        color="attendance",
        color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=75, line_dash="dash", line_color="#F59E0B", annotation_text="Min Benchmark (75%)")
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False, yaxis={"range": [0, 110]}, height=360)
    return fig


def create_attendance_distribution_chart(merged_df: pd.DataFrame) -> go.Figure:
    """Histogram of student attendance distribution."""
    if merged_df is None or merged_df.empty:
        return go.Figure()

    fig = px.histogram(
        merged_df,
        x="attendance",
        nbins=15,
        title="Attendance Distribution Frequency",
        labels={"attendance": "Attendance Percentage (%)"},
        color_discrete_sequence=["#3B82F6"],
        opacity=0.85,
    )
    fig.add_vline(x=75, line_dash="dash", line_color="#DC2626", annotation_text="75% Requirement", annotation_position="top left")
    fig.update_layout(**CHART_THEME, xaxis={"range": [0, 105]}, yaxis_title="Record Count", height=360)
    return fig


def create_subject_pass_rate_chart(subj_df: pd.DataFrame) -> go.Figure:
    """Bar chart showing pass percentage per subject."""
    if subj_df is None or subj_df.empty:
        return go.Figure()

    fig = px.bar(
        subj_df,
        x="subject",
        y="pass_percentage",
        text="pass_percentage",
        title="Pass Percentage by Subject (%)",
        labels={"pass_percentage": "Pass Rate (%)", "subject": "Subject"},
        color="pass_percentage",
        color_continuous_scale="Tealgrn",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=70, line_dash="dot", line_color="#F59E0B", annotation_text="Target Rate (70%)")
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False, yaxis={"range": [0, 115]}, height=360)
    return fig


def create_study_hours_vs_marks_chart(merged_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Daily Study Hours vs Marks."""
    if merged_df is None or merged_df.empty:
        return go.Figure()

    fig = px.scatter(
        merged_df,
        x="study_hours",
        y="marks",
        color="department",
        trendline="ols",
        hover_data=["student_id", "student_name", "subject", "attendance"],
        title="Study Hours (hrs/day) vs Marks (with Linear Fit)",
        labels={"study_hours": "Daily Study Hours (hrs/day)", "marks": "Marks (0-100)"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.add_hline(y=40, line_dash="dot", line_color="#EF4444", annotation_text="Pass Cutoff (40)")
    fig.update_layout(**CHART_THEME, yaxis={"range": [0, 105]}, height=380)
    return fig


def create_study_hours_binned_chart(binned_df: pd.DataFrame) -> go.Figure:
    """Bar chart of average marks by study hour ranges."""
    if binned_df is None or binned_df.empty:
        return go.Figure()

    fig = px.bar(
        binned_df,
        x="study_hour_range",
        y="avg_marks",
        text="avg_marks",
        title="Average Marks Grouped by Daily Study Hours",
        labels={"study_hour_range": "Daily Study Hour Bracket", "avg_marks": "Average Marks"},
        color="avg_marks",
        color_continuous_scale="Purples",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.add_hline(y=40, line_dash="dash", line_color="#EF4444")
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False, yaxis={"range": [0, 105]}, height=360)
    return fig


def create_dept_study_hours_chart(dept_study_df: pd.DataFrame) -> go.Figure:
    """Department-wise average study hours."""
    if dept_study_df is None or dept_study_df.empty:
        return go.Figure()

    fig = px.bar(
        dept_study_df,
        x="department",
        y="avg_study_hours",
        text="avg_study_hours",
        title="Department-wise Average Daily Study Hours",
        labels={"department": "Department", "avg_study_hours": "Average Study Hours (hrs/day)"},
        color="avg_study_hours",
        color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="%{text:.1f} hrs", textposition="outside")
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False, yaxis={"range": [0, max(8.0, dept_study_df['avg_study_hours'].max() * 1.3)]}, height=360)
    return fig


def create_recommendation_category_chart(rec_summary: Dict[str, int]) -> go.Figure:
    """Bar chart comparing counts of recommendation categories."""
    df = pd.DataFrame([
        {"Category": k, "Count": v}
        for k, v in rec_summary.items()
    ])

    color_map = {
        "Academic Support": "#EF4444",
        "Attendance Review": "#F59E0B",
        "Assignment Support": "#6366F1",
        "High Achievement": "#10B981",
    }

    fig = px.bar(
        df,
        x="Category",
        y="Count",
        text="Count",
        color="Category",
        color_discrete_map=color_map,
        title="Distribution of Academic Advisory Recommendations",
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(**CHART_THEME, showlegend=False, yaxis={"range": [0, max(5, df['Count'].max() * 1.3)]}, height=360)
    return fig


# =============================================================================
# 3. REPORTLAB FORMATTED PDF ACADEMIC REPORT GENERATION
# =============================================================================

def generate_pdf_academic_report(
    merged_df: pd.DataFrame,
    students_df: Optional[pd.DataFrame] = None,
    filters_dict: Optional[Dict[str, Any]] = None,
    pass_threshold: float = 40.0,
    attendance_threshold: float = 75.0,
) -> bytes:
    """
    Generate a formatted academic analytics PDF report using ReportLab.
    Embeds Plotly chart PNG images, summary KPIs, key observations, and supporting tables.
    """
    buffer = io.BytesIO()

    # Document setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1F2937"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1F2937"),
    )

    story: List[Any] = []

    # 1. Header & Metadata
    story.append(Paragraph("🎓 EduPulse — Institutional Academic & Visual Analytics Report", title_style))
    current_time_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"<b>Generated:</b> {current_time_str} &nbsp;|&nbsp; <b>Evaluation Engine:</b> EduPulse Analytics v2.0", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=2, spaceAfter=8))

    # 2. Filter Summary Block
    filters = filters_dict or {}
    filter_desc = (
        f"<b>Active Filters:</b> Department: <i>{filters.get('department', 'All')}</i> &nbsp;|&nbsp; "
        f"Semester: <i>{filters.get('semester', 'All')}</i> &nbsp;|&nbsp; "
        f"Subject: <i>{filters.get('subject', 'All')}</i> &nbsp;|&nbsp; "
        f"Date Scope: <i>{filters.get('date_scope', 'All Dates')}</i>"
    )
    story.append(Paragraph(filter_desc, body_style))
    story.append(Spacer(1, 8))

    # 3. Overall KPI Metrics Table
    summary = get_overall_academic_summary(merged_df, students_df=students_df, pass_threshold=pass_threshold)

    kpi_data = [
        [
            Paragraph("<b>Total Students</b>", table_cell_style),
            Paragraph(f"<b>{summary['total_students']}</b>", table_cell_style),
            Paragraph("<b>Total Assessments</b>", table_cell_style),
            Paragraph(f"<b>{summary['total_assessments']}</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Overall Average Marks</b>", table_cell_style),
            Paragraph(f"<b>{summary['overall_avg_marks']:.1f} / 100</b>", table_cell_style),
            Paragraph("<b>Overall Average Attendance</b>", table_cell_style),
            Paragraph(f"<b>{summary['overall_avg_attendance']:.1f}%</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Student-Level Pass Rate</b>", table_cell_style),
            Paragraph(f"<b>{summary['student_pass_rate']:.1f}%</b>", table_cell_style),
            Paragraph("<b>Assessment-Level Pass Rate</b>", table_cell_style),
            Paragraph(f"<b>{summary['assessment_pass_rate']:.1f}%</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Students Flagged for Support</b>", table_cell_style),
            Paragraph(f"<font color='#DC2626'><b>{summary['students_needing_support']} student(s)</b></font>", table_cell_style),
            Paragraph("<b>Daily Study Hours (Avg)</b>", table_cell_style),
            Paragraph(f"<b>{summary['overall_avg_study_hours']:.1f} hrs/day</b>", table_cell_style),
        ],
    ]

    kpi_table = Table(kpi_data, colWidths=[150, 120, 150, 120])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 4. Key Academic Observations
    story.append(Paragraph("📌 Key Academic Observations", section_heading))
    observations = generate_key_observations(merged_df, pass_threshold=pass_threshold)
    for obs in observations:
        story.append(Paragraph(f"• {obs}", body_style))
        story.append(Spacer(1, 2))
    story.append(Spacer(1, 8))

    # 5. Embedded Graphical Charts (rendered via Plotly + kaleido)
    if not merged_df.empty:
        story.append(Paragraph("📊 Graphical Performance Visualizations", section_heading))

        def safe_plotly_img(fig: go.Figure, width: int = 530, height: int = 240) -> Optional[Image]:
            try:
                img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
                stream = io.BytesIO(img_bytes)
                return Image(stream, width=width, height=height)
            except Exception:
                return None

        # Chart 1: Subject pass rates
        subj_df = get_subject_performance_analysis(merged_df, pass_threshold=pass_threshold)
        fig1 = create_subject_pass_rate_chart(subj_df)
        img1 = safe_plotly_img(fig1, 520, 220)
        if img1:
            story.append(Paragraph("<b>Figure 1:</b> Subject Pass Percentages (%)", body_style))
            story.append(Spacer(1, 3))
            story.append(img1)
            story.append(Spacer(1, 10))

        # Chart 2: Attendance vs Marks
        fig2 = create_study_hours_vs_marks_chart(merged_df)
        img2 = safe_plotly_img(fig2, 520, 220)
        if img2:
            story.append(Paragraph("<b>Figure 2:</b> Daily Study Hours vs Marks Scored (Association Analysis)", body_style))
            story.append(Spacer(1, 3))
            story.append(img2)
            story.append(Spacer(1, 10))

    # 6. Top Performing Students Table
    story.append(Paragraph("🏆 Top Performing Students (Student-Level Aggregation)", section_heading))
    top_students = get_top_performing_students(merged_df, top_n=6)
    if top_students.empty:
        story.append(Paragraph("No student records available.", body_style))
    else:
        top_data = [
            [
                Paragraph("<b>Rank</b>", table_header_style),
                Paragraph("<b>ID</b>", table_header_style),
                Paragraph("<b>Name</b>", table_header_style),
                Paragraph("<b>Dept / Sem</b>", table_header_style),
                Paragraph("<b>Avg Marks</b>", table_header_style),
                Paragraph("<b>Avg Att %</b>", table_header_style),
                Paragraph("<b>Academic Standing</b>", table_header_style),
            ]
        ]
        for _, row in top_students.iterrows():
            top_data.append([
                Paragraph(str(row["rank"]), table_cell_style),
                Paragraph(str(row["student_id"]), table_cell_style),
                Paragraph(str(row["student_name"]), table_cell_style),
                Paragraph(f"{row['department']} (S{row['semester']})", table_cell_style),
                Paragraph(f"{row['avg_marks']:.1f}", table_cell_style),
                Paragraph(f"{row['avg_attendance']:.1f}%", table_cell_style),
                Paragraph(str(row["standing"]), table_cell_style),
            ])

        t_top = Table(top_data, colWidths=[35, 55, 120, 110, 60, 60, 100])
        t_top.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(t_top)

    story.append(Spacer(1, 10))

    # 7. Subject Performance Breakdown Table
    story.append(Paragraph("📚 Subject Assessment & Pass Rate Breakdown", section_heading))
    subj_analysis = get_subject_performance_analysis(merged_df, pass_threshold=pass_threshold)
    if subj_analysis.empty:
        story.append(Paragraph("No subject data available.", body_style))
    else:
        subj_table_data = [
            [
                Paragraph("<b>Subject Title</b>", table_header_style),
                Paragraph("<b>Assessments</b>", table_header_style),
                Paragraph("<b>Avg Marks</b>", table_header_style),
                Paragraph("<b>Pass Rate %</b>", table_header_style),
                Paragraph("<b>Avg Att %</b>", table_header_style),
                Paragraph("<b>Status</b>", table_header_style),
            ]
        ]
        for _, r in subj_analysis.iterrows():
            subj_table_data.append([
                Paragraph(str(r["subject"]), table_cell_style),
                Paragraph(str(r["total_assessments"]), table_cell_style),
                Paragraph(f"{r['avg_marks']:.1f}", table_cell_style),
                Paragraph(f"{r['pass_percentage']:.1f}%", table_cell_style),
                Paragraph(f"{r['avg_attendance']:.1f}%", table_cell_style),
                Paragraph(f"<font color='{'#DC2626' if r['status'] == 'Needs Attention' else '#166534'}'><b>{r['status']}</b></font>", table_cell_style),
            ])

        t_subj = Table(subj_table_data, colWidths=[150, 75, 75, 75, 75, 90])
        t_subj.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(t_subj)

    story.append(Spacer(1, 14))

    # 8. Disclaimer & Academic Integrity Note
    disclaimer_text = (
        "<i><b>Pedagogical Notice:</b> This automated report is generated by EduPulse as an academic decision-support "
        "instrument for faculty counseling and tutoring interventions. Statistical associations between study hours, "
        "attendance, and examination marks do not imply strict personal causation.</i>"
    )
    story.append(Paragraph(disclaimer_text, body_style))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
