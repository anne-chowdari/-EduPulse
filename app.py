"""
EduPulse — Student Performance Analytics Hub
Main Streamlit Application.
Follows the BizPulse architecture with modular database and analytics utilities.
"""

from datetime import date, datetime
import io
import pandas as pd
import streamlit as st

import db
import analytics
import reports


# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="EduPulse — Student Performance Analytics Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for crisp, modern academic aesthetic (White/Light theme with deep blue accents)
st.markdown(
    """
    <style>
    /* Main container clean spacing */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header brand banner */
    .brand-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .brand-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-subtitle {
        font-size: 1rem;
        font-weight: 400;
        color: #E0E7FF;
        margin-top: 0.25rem;
        margin-bottom: 0;
    }
    
    /* Metric KPI Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] p {
        color: #4B5563 !important;
        font-weight: 600;
        font-size: 0.875rem;
    }
    div[data-testid="stMetricValue"] div {
        color: #1E3A8A !important;
        font-weight: 700;
    }
    
    /* Card Container */
    .edu-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    
    /* Badges */
    .badge-support {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-pass {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-distinction {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. APPLICATION HEADER & CONNECTION STATUS
# -----------------------------------------------------------------------------

def render_header():
    """Render the application header with branding and quick status."""
    st.markdown(
        """
        <div class="brand-header">
            <h1 class="brand-title">🎓 EduPulse</h1>
            <p class="brand-subtitle">Student Performance Analytics Hub • Academic Monitoring & Rule-Based Advisory</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def check_db_health():
    """Verify MySQL connectivity and provide diagnostic advice if offline."""
    is_connected, msg = db.test_connection()
    if not is_connected:
        st.error(
            f"⚠️ **Database Offline:** Could not connect to MySQL server.\n\n"
            f"**Error Details:** `{msg}`\n\n"
            f"Please ensure MySQL is running, `.env` contains valid credentials, and `database.sql` has been run."
        )
        with st.expander("🛠️ MySQL Quick Setup Guide"):
            st.markdown(
                """
                1. Make sure your MySQL service is started.
                2. Verify your `.env` configuration in the project root:
                   ```ini
                   MYSQL_HOST=localhost
                   MYSQL_PORT=3306
                   MYSQL_USER=root
                   MYSQL_PASSWORD=your_password
                   MYSQL_DATABASE=edupulse_db
                   ```
                3. Click below to attempt automatic database & schema initialization:
                """
            )
            if st.button("🚀 Attempt Auto-Initialize Database Schema"):
                ok, init_msg = db.init_db()
                if ok:
                    st.success(init_msg)
                    st.rerun()
                else:
                    st.error(init_msg)
        return False
    return True


# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & GLOBAL FILTERS
# -----------------------------------------------------------------------------

render_header()

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Graphical Reports",
        "Add Student",
        "Record Performance",
        "Student Records",
        "Academic Insights",
        "Reports & Data Import",
        "About Project",
    ],
    index=0,
)

st.sidebar.divider()
st.sidebar.caption("System Environment: Python 3 • Streamlit • MySQL • Plotly")

# Check database connection before proceeding with operational pages
db_is_healthy = check_db_health()


# -----------------------------------------------------------------------------
# PAGE 1: DASHBOARD
# -----------------------------------------------------------------------------

if page == "Dashboard":
    st.subheader("📊 Academic Analytics Dashboard")
    st.caption("Live statistical monitoring of student marks, attendance, study hours, and academic support needs.")

    if not db_is_healthy:
        st.info("Please establish MySQL connection to view live dashboard metrics.")
    else:
        # Load raw data for filter options
        students_df = db.get_all_students()
        all_perf_df = db.get_all_performance()

        if students_df.empty:
            st.warning("⚠️ **No student records found in database.**")
            st.info("Get started by registering students on the **Add Student** page or importing records via **Reports & Data Import**.")
        else:
            # Dashboard Filters
            st.markdown("##### 🔍 Global Analytics Filters")
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)

            depts = ["All"] + sorted(list(students_df["department"].dropna().unique()))
            with fcol1:
                sel_dept = st.selectbox("Department", depts, key="dash_dept")

            sems = ["All"] + sorted(list(students_df["semester"].dropna().unique()))
            with fcol2:
                sel_sem = st.selectbox("Semester", sems, key="dash_sem")

            subjects = ["All"]
            if not all_perf_df.empty:
                subjects += sorted(list(all_perf_df["subject"].dropna().unique()))
            with fcol3:
                sel_subj = st.selectbox("Subject", subjects, key="dash_subj")

            with fcol4:
                date_filter = st.selectbox("Time Window", ["All Recorded Dates", "Custom Date Range"], key="dash_date_window")

            date_from = None
            date_to = None
            if date_filter == "Custom Date Range":
                d_c1, d_c2 = st.columns(2)
                with d_c1:
                    date_from = st.date_input("Start Date", date(2026, 1, 1), key="dash_dfrom")
                with d_c2:
                    date_to = st.date_input("End Date", date.today(), key="dash_dto")

            # Fetch joined merged data dynamically using selected filters
            merged_df = db.get_merged_data(
                department=sel_dept if sel_dept != "All" else None,
                semester=sel_sem if sel_sem != "All" else None,
                subject=sel_subj if sel_subj != "All" else None,
                date_from=date_from,
                date_to=date_to,
            )

            # Calculate dynamic KPIs using clearly documented student-level vs subject-level rules
            kpis = analytics.calculate_kpis(merged_df, students_df=students_df)

            st.divider()

            # KPI Cards
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            k1.metric("Total Students", f"{kpis['total_students']}")
            k2.metric("Total Assessments", f"{kpis['total_records']}")
            k3.metric("Average Marks", f"{kpis['avg_marks']:.1f} / 100")
            k4.metric("Avg Attendance", f"{kpis['avg_attendance']:.1f}%")
            k5.metric("Pass Rate (Student)", f"{kpis['pass_percentage']:.1f}%")
            k6.metric("Need Support", f"{kpis['students_needing_support']}")

            st.caption(
                "ℹ️ **Aggregation Methodology:** Pass rate is evaluated at the student level (student's average across subjects ≥ 40). "
                "Students needing support represent unique individuals with any subject score < 40 or overall attendance < 75%."
            )

            if merged_df.empty:
                st.info("No performance assessments match the selected filter criteria. Try broadening your filters or add performance records.")
            else:
                st.divider()

                # Visualizations Row 1: Subject & Department Averages
                r1_col1, r1_col2 = st.columns(2)
                with r1_col1:
                    fig_subj = analytics.create_marks_by_subject_chart(merged_df)
                    st.plotly_chart(fig_subj, use_container_width=True)
                with r1_col2:
                    fig_dept = analytics.create_marks_by_department_chart(merged_df)
                    st.plotly_chart(fig_dept, use_container_width=True)

                # Visualizations Row 2: Distribution & Attendance vs Marks Correlation
                r2_col1, r2_col2 = st.columns(2)
                with r2_col1:
                    fig_dist = analytics.create_performance_distribution_chart(merged_df)
                    st.plotly_chart(fig_dist, use_container_width=True)
                with r2_col2:
                    fig_scat = analytics.create_attendance_vs_marks_chart(merged_df)
                    st.plotly_chart(fig_scat, use_container_width=True)

                # Visualizations Row 3: Assignment Scores & Semester-wise Trends
                r3_col1, r3_col2 = st.columns(2)
                with r3_col1:
                    fig_asg = analytics.create_assignment_by_subject_chart(merged_df)
                    st.plotly_chart(fig_asg, use_container_width=True)
                with r3_col2:
                    fig_sem = analytics.create_semester_performance_chart(merged_df)
                    st.plotly_chart(fig_sem, use_container_width=True)

                # Recent Assessments Table
                with st.expander("📋 View Filtered Performance Data Table", expanded=False):
                    st.dataframe(
                        merged_df[[
                            "student_id", "student_name", "department", "semester",
                            "subject", "marks", "attendance", "study_hours", "assignment_score", "record_date"
                        ]].rename(columns={"study_hours": "daily_study_hrs"}),
                        use_container_width=True,
                    )


# -----------------------------------------------------------------------------
# PAGE: GRAPHICAL REPORTS & VISUAL ANALYTICS
# -----------------------------------------------------------------------------

elif page == "Graphical Reports":
    st.subheader("📈 Graphical Reports & Visual Analytics")
    st.caption("Interactive visual intelligence, subject-level breakdowns, correlation matrices, and downloadable PDF reports.")

    if not db_is_healthy:
        st.error("Database connection required to generate graphical reports.")
    else:
        students_df = db.get_all_students()
        all_perf_df = db.get_all_performance()

        if students_df.empty or all_perf_df.empty:
            st.warning("⚠️ **Insufficient Data for Visual Reports:** No student performance records found in database.")
            st.info("Tip: You can add student assessments via **Record Performance** or batch-import test datasets via **Reports & Data Import**.")
        else:
            # Report Filters
            with st.expander("🔍 Interactive Report Filters", expanded=True):
                fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)

                depts = ["All"] + sorted(list(students_df["department"].dropna().unique()))
                with fcol1:
                    rep_dept = st.selectbox("Department", depts, key="rep_dept")

                sems = ["All"] + sorted(list(students_df["semester"].dropna().unique()))
                with fcol2:
                    rep_sem = st.selectbox("Semester", sems, key="rep_sem")

                subjects = ["All"] + sorted(list(all_perf_df["subject"].dropna().unique()))
                with fcol3:
                    rep_subj = st.selectbox("Subject", subjects, key="rep_subj")

                with fcol4:
                    rep_time = st.selectbox("Date Scope", ["All Recorded Dates", "Custom Range"], key="rep_time")

                student_opts = ["All Students"] + [
                    f"{r['student_id']} - {r['student_name']}" for _, r in students_df.iterrows()
                ]
                with fcol5:
                    rep_student = st.selectbox("Student Focus", student_opts, key="rep_student")

                rep_from = None
                rep_to = None
                if rep_time == "Custom Range":
                    r_c1, r_c2 = st.columns(2)
                    with r_c1:
                        rep_from = st.date_input("Start Date", date(2026, 1, 1), key="rep_dfrom")
                    with r_c2:
                        rep_to = st.date_input("End Date", date.today(), key="rep_dto")

            # Fetch joined filtered data
            merged_df = db.get_merged_data(
                department=rep_dept if rep_dept != "All" else None,
                semester=rep_sem if rep_sem != "All" else None,
                subject=rep_subj if rep_subj != "All" else None,
                date_from=rep_from,
                date_to=rep_to,
            )

            # Further filter by individual student if selected
            if rep_student != "All Students":
                sel_sid = rep_student.split(" - ")[0].strip()
                merged_df = merged_df[merged_df["student_id"] == sel_sid]

            if merged_df.empty:
                st.warning("⚠️ No performance records match the active filter criteria. Try adjusting or resetting your filters.")
            else:
                # Top KPI Summary Bar
                overall_summary = reports.get_overall_academic_summary(merged_df, students_df=students_df)

                k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
                k1.metric("Students", f"{overall_summary['total_students']}")
                k2.metric("Assessments", f"{overall_summary['total_assessments']}")
                k3.metric("Avg Marks", f"{overall_summary['overall_avg_marks']:.1f}")
                k4.metric("Avg Attendance", f"{overall_summary['overall_avg_attendance']:.1f}%")
                k5.metric("Student Pass Rate", f"{overall_summary['student_pass_rate']:.1f}%")
                k6.metric("Exam Pass Rate", f"{overall_summary['assessment_pass_rate']:.1f}%")
                k7.metric("Need Support", f"{overall_summary['students_needing_support']}")

                st.caption(
                    "ℹ️ **Distinction Note:** *Student Pass Rate* evaluates each unique student's overall performance "
                    "(mean across all taken subjects ≥ 40.0), whereas *Exam Pass Rate* evaluates the percentage of all recorded "
                    "subject tests meeting the pass benchmark."
                )

                st.divider()

                # Report Sub-Tabs
                tab_perf, tab_att, tab_subj, tab_study, tab_supp, tab_summary = st.tabs([
                    "📊 Student Performance Report",
                    "📅 Attendance Analysis",
                    "📚 Subject Analysis",
                    "⏱️ Study Hours Analysis",
                    "🚨 Academic Support Report",
                    "📋 Overall Summary & Export",
                ])

                # -------------------------------------------------------------
                # TAB A: Student Performance Report
                # -------------------------------------------------------------
                with tab_perf:
                    st.markdown("#### 📊 Student Performance Analytics")
                    st.caption("Student-level score distributions, subject comparisons, and academic standing rankings.")

                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        fig_smarks = reports.create_student_marks_bar_chart(merged_df)
                        st.plotly_chart(fig_smarks, use_container_width=True)
                    with p_col2:
                        fig_sdist = analytics.create_performance_distribution_chart(merged_df)
                        st.plotly_chart(fig_sdist, use_container_width=True)

                    p_col3, p_col4 = st.columns(2)
                    with p_col3:
                        fig_scomp = reports.create_subject_marks_comparison_chart(merged_df)
                        st.plotly_chart(fig_scomp, use_container_width=True)
                    with p_col4:
                        fig_sdept = analytics.create_marks_by_department_chart(merged_df)
                        st.plotly_chart(fig_sdept, use_container_width=True)

                    p_col5, _ = st.columns([2, 1])
                    with p_col5:
                        fig_ssem = analytics.create_semester_performance_chart(merged_df)
                        st.plotly_chart(fig_ssem, use_container_width=True)

                    st.markdown("##### 🏆 Top-Performing Students (Student-Level Aggregation)")
                    top_df = reports.get_top_performing_students(merged_df, top_n=10)
                    st.dataframe(top_df, use_container_width=True)

                # -------------------------------------------------------------
                # TAB B: Attendance Analysis Report
                # -------------------------------------------------------------
                with tab_att:
                    st.markdown("#### 📅 Attendance & Academic Engagement")
                    st.caption("Department attendance compliance, frequency distribution, and attendance vs score correlation.")

                    a_col1, a_col2 = st.columns(2)
                    with a_col1:
                        fig_adept = reports.create_attendance_by_dept_chart(merged_df)
                        st.plotly_chart(fig_adept, use_container_width=True)
                    with a_col2:
                        fig_adist = reports.create_attendance_distribution_chart(merged_df)
                        st.plotly_chart(fig_adist, use_container_width=True)

                    fig_ascat = analytics.create_attendance_vs_marks_chart(merged_df)
                    st.plotly_chart(fig_ascat, use_container_width=True)

                    # Attendance Quadrants & Low Attendance Table
                    dept_att_df, low_att_df, quadrants = reports.get_attendance_analysis_data(merged_df, threshold=75.0)

                    st.markdown("##### 🧭 Attendance & Academic Quadrant Distribution")
                    q1, q2, q3, q4 = st.columns(4)
                    q1.metric("High Att (≥75%) & Pass", quadrants["High Att & Pass"])
                    q2.metric("High Att (≥75%) & Need Support", quadrants["High Att & Need Support"])
                    q3.metric("Low Att (<75%) & Pass", quadrants["Low Att & Pass"])
                    q4.metric("Low Att (<75%) & Need Support", quadrants["Low Att & Need Support"])

                    st.markdown("##### ⚠️ Students with Attendance Below Institutional Threshold (< 75%)")
                    if low_att_df.empty:
                        st.success("🎉 All evaluated students currently meet the minimum 75% institutional attendance requirement.")
                    else:
                        st.dataframe(low_att_df, use_container_width=True)

                # -------------------------------------------------------------
                # TAB C: Subject Analysis Report
                # -------------------------------------------------------------
                with tab_subj:
                    st.markdown("#### 📚 Subject-Level Performance & Assessment Breakdown")
                    st.caption("Evaluation of subject difficulty, pass percentages, and continuous assignment completion.")

                    subj_perf_df = reports.get_subject_performance_analysis(merged_df, pass_threshold=40.0)

                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        fig_subpass = reports.create_subject_pass_rate_chart(subj_perf_df)
                        st.plotly_chart(fig_subpass, use_container_width=True)
                    with s_col2:
                        fig_subavg = analytics.create_marks_by_subject_chart(merged_df)
                        st.plotly_chart(fig_subavg, use_container_width=True)

                    fig_subasg = analytics.create_assignment_by_subject_chart(merged_df)
                    st.plotly_chart(fig_subasg, use_container_width=True)

                    # Highlight lower average subjects
                    low_subjs = subj_perf_df[subj_perf_df["status"] == "Needs Attention"]
                    if not low_subjs.empty:
                        st.warning(
                            f"⚠️ **Curriculum Review Alert:** The following course(s) recorded average marks below 50.0 or pass rates below 70%: "
                            f"**{', '.join(low_subjs['subject'].tolist())}**."
                        )

                    st.markdown("##### 📋 Complete Subject Assessment Statistics")
                    st.dataframe(subj_perf_df, use_container_width=True)

                # -------------------------------------------------------------
                # TAB D: Study Hours Analysis
                # -------------------------------------------------------------
                with tab_study:
                    st.markdown("#### ⏱️ Study Hours & Academic Outcome Associations")
                    st.caption("Analysis of daily study preparation hours and academic score distributions.")

                    st.info(
                        "💡 **Pedagogical Insight:** Visualizations demonstrate statistical associations within the collected data "
                        "and do not constitute proof of causation. Academic mastery is influenced by course complexity, teaching quality, "
                        "and active learning methodologies."
                    )

                    binned_study_df, dept_study_df, corr_coef = reports.get_study_hours_analysis(merged_df)

                    h_col1, h_col2 = st.columns(2)
                    with h_col1:
                        fig_hscat = reports.create_study_hours_vs_marks_chart(merged_df)
                        st.plotly_chart(fig_hscat, use_container_width=True)
                    with h_col2:
                        fig_hbin = reports.create_study_hours_binned_chart(binned_study_df)
                        st.plotly_chart(fig_hbin, use_container_width=True)

                    h_col3, h_col4 = st.columns([1, 1])
                    with h_col3:
                        fig_hdept = reports.create_dept_study_hours_chart(dept_study_df)
                        st.plotly_chart(fig_hdept, use_container_width=True)
                    with h_col4:
                        st.markdown("##### 📊 Study-Hour Bracket Statistics")
                        st.dataframe(binned_study_df, use_container_width=True)
                        st.metric("Correlation (Study Hours vs Marks)", f"r = {corr_coef:+.3f}")

                # -------------------------------------------------------------
                # TAB E: Academic Support Report
                # -------------------------------------------------------------
                with tab_supp:
                    st.markdown("#### 🚨 Academic Support & Mentoring Advisory")
                    st.caption("Identification of students needing targeted intervention, remedial sessions, or attendance review.")

                    recs_list = analytics.generate_recommendations(merged_df)
                    rec_counts = analytics.get_recommendation_summary(recs_list)

                    # Avoid double-counting students: compute unique students with at least 1 support trigger
                    support_student_ids = {
                        r["student_id"] for r in recs_list if r["category"] in ["Academic Support", "Attendance Review", "Assignment Support"]
                    }

                    sup_c1, sup_c2, sup_c3, sup_c4 = st.columns(4)
                    sup_c1.metric("Unique Students Needing Support", len(support_student_ids), help="Distinct students with at least 1 critical indicator")
                    sup_c2.metric("Academic Support Triggers", rec_counts["Academic Support"], help="Subject scores < 40")
                    sup_c3.metric("Attendance Review Triggers", rec_counts["Attendance Review"], help="Attendance < 75%")
                    sup_c4.metric("Assignment Coaching Triggers", rec_counts["Assignment Support"], help="Assignment score < 50")

                    fig_reccat = reports.create_recommendation_category_chart(rec_counts)
                    st.plotly_chart(fig_reccat, use_container_width=True)

                    st.markdown("##### 📋 Detailed Mentoring Registry")
                    rec_cat_sel = st.selectbox(
                        "Filter Registry by Category",
                        ["All Categories", "Academic Support", "Attendance Review", "Assignment Support", "High Achievement"],
                        key="rep_rec_cat_filter"
                    )

                    shown_recs = [
                        r for r in recs_list
                        if rec_cat_sel == "All Categories" or r["category"] == rec_cat_sel
                    ]

                    if not shown_recs:
                        st.success("No advisory entries match the selected category.")
                    else:
                        st.dataframe(
                            pd.DataFrame(shown_recs)[[
                                "student_id", "student_name", "department", "subject",
                                "category", "metric_name", "metric_value", "reason", "actionable_suggestion"
                            ]],
                            use_container_width=True,
                        )

                # -------------------------------------------------------------
                # TAB F: Overall Academic Summary & Downloads
                # -------------------------------------------------------------
                with tab_summary:
                    st.markdown("#### 📋 Overall Institutional Summary & Export")
                    st.caption("Synthesized observations and multi-format export capabilities.")

                    st.markdown("##### 📌 Key Data-Driven Observations")
                    key_obs = reports.generate_key_observations(merged_df, pass_threshold=40.0)
                    for obs in key_obs:
                        st.write(f"• {obs}")

                    st.divider()

                    st.markdown("##### 🏢 Department-wise Academic Comparison")
                    st.dataframe(overall_summary["dept_comparison"], use_container_width=True)

                    st.markdown("##### 🎓 Semester-wise Performance Comparison")
                    st.dataframe(overall_summary["sem_comparison"], use_container_width=True)

                    st.divider()

                    st.markdown("### 📥 Download Institutional Reports")
                    d_col1, d_col2 = st.columns(2)

                    with d_col1:
                        st.markdown("##### 1. Formatted Academic PDF Report")
                        st.caption("Comprehensive multi-page PDF document with embedded Plotly charts, KPI summary, and observation registry.")

                        # Generate PDF
                        filter_summary_dict = {
                            "department": rep_dept,
                            "semester": rep_sem,
                            "subject": rep_subj,
                            "date_scope": rep_time if rep_time != "Custom Range" else f"{rep_from} to {rep_to}",
                        }
                        try:
                            pdf_data = reports.generate_pdf_academic_report(
                                merged_df,
                                students_df=students_df,
                                filters_dict=filter_summary_dict,
                                pass_threshold=40.0,
                                attendance_threshold=75.0,
                            )
                            st.download_button(
                                "📄 Download Complete Graphical PDF Report",
                                pdf_data,
                                f"edupulse_academic_report_{date.today()}.pdf",
                                "application/pdf",
                                type="primary",
                                key="btn_dl_graph_pdf",
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF report: {e}")

                        st.markdown("##### 2. Raw Filtered Performance Data (CSV)")
                        csv_raw = merged_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "📊 Download Filtered Records (CSV)",
                            csv_raw,
                            f"edupulse_filtered_data_{date.today()}.csv",
                            "text/csv",
                            key="btn_dl_graph_raw_csv",
                        )

                    with d_col2:
                        st.markdown("##### 3. Top-Performing Students Summary (CSV)")
                        csv_top = top_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "🏆 Download Top Students Report (CSV)",
                            csv_top,
                            f"edupulse_top_students_{date.today()}.csv",
                            "text/csv",
                            key="btn_dl_graph_top_csv",
                        )

                        st.markdown("##### 4. Subject Assessment Breakdown (CSV)")
                        csv_subj = subj_perf_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "📚 Download Subject Analysis (CSV)",
                            csv_subj,
                            f"edupulse_subject_breakdown_{date.today()}.csv",
                            "text/csv",
                            key="btn_dl_graph_subj_csv",
                        )


# -----------------------------------------------------------------------------
# PAGE 2: ADD STUDENT
# -----------------------------------------------------------------------------

elif page == "Add Student":
    st.subheader("👤 Register New Student")
    st.caption("Enroll a student profile with department and semester details into the database.")

    if not db_is_healthy:
        st.error("Database connection required to register students.")
    else:
        with st.form("add_student_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                student_id = st.text_input("Student ID *", placeholder="e.g. STU101", help="Must be unique across the institution.")
                department = st.selectbox(
                    "Department *",
                    [
                        "Computer Science",
                        "Information Technology",
                        "Electronics",
                        "Mechanical",
                        "Civil",
                        "Electrical",
                    ]
                )
            with col2:
                student_name = st.text_input("Full Student Name *", placeholder="e.g. Aarav Sharma")
                semester = st.number_input("Current Semester *", min_value=1, max_value=12, value=1, step=1)

            submitted = st.form_submit_button("➕ Save Student Profile", type="primary")

            if submitted:
                # Validate inputs
                is_valid, val_msg = analytics.validate_student_inputs(student_id, student_name, department, semester)
                if not is_valid:
                    st.error(val_msg)
                else:
                    success, db_msg = db.add_student(student_id, student_name, department, int(semester))
                    if success:
                        st.success(db_msg)
                    else:
                        st.error(db_msg)

        st.divider()
        st.markdown("##### 👥 Existing Registered Students")
        existing_students = db.get_all_students()
        if existing_students.empty:
            st.info("No students enrolled yet.")
        else:
            st.dataframe(
                existing_students[["student_id", "student_name", "department", "semester", "created_at"]],
                use_container_width=True,
            )


# -----------------------------------------------------------------------------
# PAGE 3: RECORD PERFORMANCE
# -----------------------------------------------------------------------------

elif page == "Record Performance":
    st.subheader("📝 Record Subject Performance")
    st.caption("Enter subject assessment scores, class attendance, and daily study hours for an enrolled student.")

    if not db_is_healthy:
        st.error("Database connection required to record performance.")
    else:
        students_df = db.get_all_students()
        if students_df.empty:
            st.warning("⚠️ No students available. Please register students on the **Add Student** page first.")
        else:
            student_options = {
                f"{row['student_id']} — {row['student_name']} ({row['department']}, Sem {row['semester']})": row["student_id"]
                for _, row in students_df.iterrows()
            }
            selected_label = st.selectbox("Select Student *", list(student_options.keys()))
            selected_id = student_options[selected_label]

            # Display selected student info
            curr_student = students_df[students_df["student_id"] == selected_id].iloc[0]

            with st.form("record_performance_form", clear_on_submit=False):
                col1, col2 = st.columns(2)

                common_subjects = [
                    "Data Structures",
                    "Database Systems",
                    "Computer Networks",
                    "Operating Systems",
                    "Software Engineering",
                    "Discrete Mathematics",
                    "Web Technologies",
                    "Artificial Intelligence",
                    "Digital Signal Processing",
                    "Thermodynamics",
                    "Fluid Mechanics",
                    "Other (Custom Subject)",
                ]

                with col1:
                    chosen_subj = st.selectbox("Subject *", common_subjects)
                    custom_subj = ""
                    if chosen_subj == "Other (Custom Subject)":
                        custom_subj = st.text_input("Enter Subject Name *", placeholder="e.g. Cloud Computing")
                    
                    final_subject = custom_subj if chosen_subj == "Other (Custom Subject)" else chosen_subj

                    marks = st.number_input(
                        "Marks Obtained (out of 100) *",
                        min_value=0.0,
                        max_value=100.0,
                        value=75.0,
                        step=0.5,
                        help="Institutional passing benchmark is 40.0"
                    )

                    attendance = st.number_input(
                        "Attendance Percentage (%) *",
                        min_value=0.0,
                        max_value=100.0,
                        value=85.0,
                        step=0.5,
                        help="Institutional minimum attendance guideline is 75.0%"
                    )

                with col2:
                    # Accurately and consistently labeled as Daily Study Hours
                    study_hours = st.number_input(
                        "Daily Study Hours (hrs/day) *",
                        min_value=0.0,
                        max_value=24.0,
                        value=3.0,
                        step=0.5,
                        help="Average daily study hours dedicated to academics."
                    )

                    assignment_score = st.number_input(
                        "Continuous Assignment Score (out of 100) *",
                        min_value=0.0,
                        max_value=100.0,
                        value=80.0,
                        step=0.5,
                        help="Internal lab or homework assignment score."
                    )

                    record_date = st.date_input(
                        "Assessment / Record Date *",
                        value=date.today(),
                        help="Date when the assessment was conducted or recorded."
                    )

                save_perf = st.form_submit_button("💾 Save Performance Record", type="primary")

                if save_perf:
                    is_valid, vmsg = analytics.validate_performance_inputs(
                        selected_id, final_subject, marks, attendance, study_hours, assignment_score, record_date
                    )
                    if not is_valid:
                        st.error(vmsg)
                    else:
                        succ, dmsg = db.add_performance_record(
                            selected_id, final_subject, marks, attendance, study_hours, assignment_score, record_date
                        )
                        if succ:
                            st.success(dmsg)
                        else:
                            st.error(dmsg)

            st.divider()
            st.markdown(f"##### 📜 Academic History for {curr_student['student_name']} ({selected_id})")
            student_perf = db.get_performance_by_student(selected_id)
            if student_perf.empty:
                st.info("No prior performance records entered for this student.")
            else:
                st.dataframe(
                    student_perf[[
                        "record_id", "subject", "marks", "attendance", 
                        "study_hours", "assignment_score", "record_date"
                    ]].rename(columns={"study_hours": "daily_study_hrs"}),
                    use_container_width=True,
                )


# -----------------------------------------------------------------------------
# PAGE 4: STUDENT RECORDS
# -----------------------------------------------------------------------------

elif page == "Student Records":
    st.subheader("📁 Student & Performance Record Management")
    st.caption("Search, filter, edit, or delete enrolled student profiles and individual assessment records.")

    if not db_is_healthy:
        st.error("Database connection required to manage student records.")
    else:
        # Search and filtering row
        scol1, scol2, scol3 = st.columns([2, 1, 1])
        with scol1:
            search_query = st.text_input("🔍 Search by Student ID or Name", placeholder="Type ID or Name...")
        with scol2:
            all_students = db.get_all_students()
            dept_opts = ["All"] + (sorted(list(all_students["department"].unique())) if not all_students.empty else [])
            f_dept = st.selectbox("Filter Department", dept_opts)
        with scol3:
            sem_opts = ["All"] + (sorted(list(all_students["semester"].unique())) if not all_students.empty else [])
            f_sem = st.selectbox("Filter Semester", sem_opts)

        filtered_students = db.get_all_students(
            search_term=search_query,
            department=f_dept if f_dept != "All" else None,
            semester=f_sem if f_sem != "All" else None,
        )

        if filtered_students.empty:
            st.warning("No students matched your search criteria.")
        else:
            st.markdown(f"**Found {len(filtered_students)} Student Profile(s):**")
            st.dataframe(
                filtered_students[["student_id", "student_name", "department", "semester", "created_at"]],
                use_container_width=True,
            )

            st.divider()
            st.markdown("#### ⚙️ Manage Individual Student & Assessments")
            student_choices = {
                f"{row['student_id']} - {row['student_name']}": row["student_id"]
                for _, row in filtered_students.iterrows()
            }
            managed_label = st.selectbox("Select Student to Manage / Edit / View Records", list(student_choices.keys()))
            managed_id = student_choices[managed_label]
            managed_row = filtered_students[filtered_students["student_id"] == managed_id].iloc[0]

            tab_view, tab_edit, tab_del = st.tabs(["📋 View Performance Records", "✏️ Edit Student Profile", "🗑️ Delete Student"])

            with tab_view:
                st.markdown(f"##### Performance Records for `{managed_id}`")
                perf_records = db.get_performance_by_student(managed_id)

                if perf_records.empty:
                    st.info(f"No performance entries recorded yet for {managed_row['student_name']}.")
                else:
                    st.dataframe(
                        perf_records[[
                            "record_id", "subject", "marks", "attendance", 
                            "study_hours", "assignment_score", "record_date"
                        ]].rename(columns={"study_hours": "daily_study_hrs"}),
                        use_container_width=True,
                    )

                    # Manage individual assessment record
                    st.markdown("###### Edit or Delete a Specific Assessment")
                    rec_options = {
                        f"Record #{r['record_id']} — {r['subject']} ({r['record_date']})": r["record_id"]
                        for _, r in perf_records.iterrows()
                    }
                    chosen_rec_label = st.selectbox("Select Assessment Record", list(rec_options.keys()))
                    chosen_rec_id = rec_options[chosen_rec_label]
                    chosen_rec = perf_records[perf_records["record_id"] == chosen_rec_id].iloc[0]

                    with st.expander("✏️ Update this Assessment Record"):
                        with st.form(f"edit_rec_form_{chosen_rec_id}"):
                            ecol1, ecol2 = st.columns(2)
                            with ecol1:
                                edit_subj = st.text_input("Subject", value=chosen_rec["subject"])
                                edit_marks = st.number_input("Marks", min_value=0.0, max_value=100.0, value=float(chosen_rec["marks"]))
                                edit_att = st.number_input("Attendance (%)", min_value=0.0, max_value=100.0, value=float(chosen_rec["attendance"]))
                            with ecol2:
                                edit_hrs = st.number_input("Daily Study Hours", min_value=0.0, max_value=24.0, value=float(chosen_rec["study_hours"]))
                                edit_asg = st.number_input("Assignment Score", min_value=0.0, max_value=100.0, value=float(chosen_rec["assignment_score"]))
                                edit_date = st.date_input("Record Date", value=pd.to_datetime(chosen_rec["record_date"]).date())

                            upd_rec_btn = st.form_submit_button("Update Assessment", type="primary")
                            if upd_rec_btn:
                                uok, umsg = db.update_performance_record(
                                    chosen_rec_id, edit_subj, edit_marks, edit_att, edit_hrs, edit_asg, edit_date
                                )
                                if uok:
                                    st.success(umsg)
                                    st.rerun()
                                else:
                                    st.error(umsg)

                    with st.expander("🗑️ Delete this Assessment Record"):
                        st.warning(f"Are you sure you want to delete Record #{chosen_rec_id} ({chosen_rec['subject']})?")
                        confirm_del_rec = st.checkbox(f"Confirm deletion of Record #{chosen_rec_id}", key=f"chk_del_rec_{chosen_rec_id}")
                        if st.button("Delete Record", type="secondary", key=f"btn_del_rec_{chosen_rec_id}"):
                            if not confirm_del_rec:
                                st.error("Please check the confirmation box before deleting.")
                            else:
                                dok, dmsg = db.delete_performance_record(chosen_rec_id)
                                if dok:
                                    st.success(dmsg)
                                    st.rerun()
                                else:
                                    st.error(dmsg)

            with tab_edit:
                st.markdown(f"##### Update Student Profile (`{managed_id}`)")
                with st.form("edit_student_form"):
                    e_name = st.text_input("Full Name", value=managed_row["student_name"])
                    e_dept = st.selectbox(
                        "Department",
                        ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"],
                        index=["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"].index(
                            managed_row["department"]
                        ) if managed_row["department"] in ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"] else 0
                    )
                    e_sem = st.number_input("Semester", min_value=1, max_value=12, value=int(managed_row["semester"]))

                    update_stu_btn = st.form_submit_button("💾 Save Profile Changes", type="primary")
                    if update_stu_btn:
                        ok_up, msg_up = db.update_student(managed_id, e_name, e_dept, int(e_sem))
                        if ok_up:
                            st.success(msg_up)
                            st.rerun()
                        else:
                            st.error(msg_up)

            with tab_del:
                st.markdown(f"##### Delete Student Profile (`{managed_id}`)")
                st.error("⚠️ **Warning:** Deleting a student will permanently remove their profile AND all associated performance records (cascading delete).")
                confirm_del_student = st.checkbox(f"I confirm that I want to permanently delete student '{managed_id}' and all their records.")
                if st.button("🚨 Permanently Delete Student", type="primary"):
                    if not confirm_del_student:
                        st.error("Action aborted: You must check the confirmation checkbox first.")
                    else:
                        d_ok, d_msg = db.delete_student(managed_id)
                        if d_ok:
                            st.success(d_msg)
                            st.rerun()
                        else:
                            st.error(d_msg)


# -----------------------------------------------------------------------------
# PAGE 5: ACADEMIC INSIGHTS & RECOMMENDATIONS
# -----------------------------------------------------------------------------

elif page == "Academic Insights":
    st.subheader("💡 Rule-Based Academic Insights & Recommendations")
    st.caption("Transparent, rule-based academic advisory indicators to support faculty mentoring and targeted intervention.")

    # Educational & Pedagogical Disclaimer
    st.info(
        "⚖️ **Decision Support Notice:** EduPulse recommendations are rule-based academic indicators meant solely "
        "to assist professors, academic counselors, and mentors. They do not predict student intelligence or future career outcomes."
    )

    if not db_is_healthy:
        st.error("Database connection required to generate academic insights.")
    else:
        merged_df = db.get_merged_data()

        if merged_df.empty:
            st.warning("⚠️ No performance records available in the database. Please add or import performance data to generate recommendations.")
        else:
            st.markdown("##### ⚙️ Configurable Institutional Benchmarks")
            with st.expander("Adjust Recommendation Thresholds", expanded=False):
                th_col1, th_col2, th_col3, th_col4 = st.columns(4)
                with th_col1:
                    th_marks = st.slider("Academic Support Cutoff (Marks <)", 20.0, 60.0, 40.0, step=1.0)
                with th_col2:
                    th_att = st.slider("Attendance Review Cutoff (< %)", 50.0, 85.0, 75.0, step=1.0)
                with th_col3:
                    th_asg = st.slider("Assignment Support Cutoff (<)", 30.0, 70.0, 50.0, step=1.0)
                with th_col4:
                    th_high = st.slider("High Achievement Benchmark (≥)", 65.0, 95.0, 75.0, step=1.0)

            # Generate recommendations dynamically
            recommendations = analytics.generate_recommendations(
                merged_df,
                marks_threshold=th_marks,
                attendance_threshold=th_att,
                assignment_threshold=th_asg,
                high_marks_threshold=th_high,
            )
            rec_summary = analytics.get_recommendation_summary(recommendations)

            # Summary Metrics Cards
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🚨 Academic Support", rec_summary["Academic Support"], help="Assessments with marks below threshold")
            m2.metric("📅 Attendance Review", rec_summary["Attendance Review"], help="Assessments with attendance below benchmark")
            m3.metric("📝 Assignment Coaching", rec_summary["Assignment Support"], help="Assessments with low assignment scores")
            m4.metric("🌟 High Performers", rec_summary["High Achievement"], help="Assessments demonstrating subject mastery")

            st.divider()

            # Filter recommendations by category
            st.markdown("##### 📋 Actionable Mentoring Recommendations")
            cat_filter = st.selectbox(
                "Filter Advisory Category",
                ["All Recommendations", "Academic Support", "Attendance Review", "Assignment Support", "High Achievement"]
            )

            filtered_recs = [
                r for r in recommendations
                if cat_filter == "All Recommendations" or r["category"] == cat_filter
            ]

            if not filtered_recs:
                st.success("🎉 No records currently require action under the selected benchmark category.")
            else:
                rec_df = pd.DataFrame(filtered_recs)
                st.dataframe(
                    rec_df[[
                        "student_id", "student_name", "department", "subject",
                        "category", "metric_name", "metric_value", "reason", "actionable_suggestion"
                    ]],
                    use_container_width=True,
                )

            st.divider()
            st.markdown("##### 🎓 Consolidated Student-Level Academic Summary")
            student_summary_df = analytics.get_student_summary(merged_df)
            st.dataframe(student_summary_df, use_container_width=True)


# -----------------------------------------------------------------------------
# PAGE 6: REPORTS & DATA IMPORT
# -----------------------------------------------------------------------------

elif page == "Reports & Data Import":
    st.subheader("📑 Reports & Batch Data Management")
    st.caption("Upload institutional CSV files with transaction safety or export filtered data reports.")

    tab_import, tab_export = st.tabs(["📥 Batch CSV Import", "📤 Export Reports"])

    with tab_import:
        st.markdown("#### 1. Import Student Profiles (CSV)")
        st.caption("Required format: `student_id`, `student_name`, `department`, `semester`")

        # Download Template Button for Students
        sample_stu_csv = "student_id,student_name,department,semester\nSTU201,Karan Johar,Computer Science,4\nSTU202,Priya Nair,Electronics,2\n"
        st.download_button(
            "⬇️ Download Student CSV Template",
            sample_stu_csv,
            "sample_students_template.csv",
            "text/csv",
            key="dl_stu_tpl",
        )

        stu_file = st.file_uploader("Upload Student Profiles CSV", type=["csv"], key="upload_students_csv")
        if stu_file is not None:
            try:
                stu_raw_df = pd.read_csv(stu_file)
                st.markdown("**Uploaded File Preview:**")
                st.dataframe(stu_raw_df.head(), use_container_width=True)

                is_valid, val_msg, valid_stu_list = analytics.validate_student_csv(stu_raw_df)
                if not is_valid:
                    st.error(f"❌ Validation Failed: {val_msg}")
                else:
                    st.success(f"✅ {val_msg}")
                    if st.button("🚀 Confirm & Import Students to MySQL", type="primary", key="btn_import_stu"):
                        ins, rej, errs = db.bulk_insert_students(valid_stu_list)
                        st.success(f"Successfully enrolled {ins} student(s) into database.")
                        if rej > 0:
                            st.warning(f"{rej} record(s) could not be imported due to conflicts or database errors.")
                            with st.expander("Review Rejected Student Rows"):
                                for e in errs:
                                    st.write(f"- {e}")
            except Exception as e:
                st.error(f"Failed to process CSV file: {e}")

        st.divider()

        st.markdown("#### 2. Import Subject Performance Records (CSV)")
        st.caption("Required format: `student_id`, `subject`, `marks`, `attendance`, `study_hours`, `assignment_score`, `record_date`")

        sample_perf_csv = "student_id,subject,marks,attendance,study_hours,assignment_score,record_date\nSTU101,Database Systems,85.0,90.0,3.0,88.0,2026-03-01\nSTU102,Data Structures,92.0,95.0,4.0,90.0,2026-03-01\n"
        st.download_button(
            "⬇️ Download Performance CSV Template",
            sample_perf_csv,
            "sample_performance_template.csv",
            "text/csv",
            key="dl_perf_tpl",
        )

        perf_file = st.file_uploader("Upload Performance Records CSV", type=["csv"], key="upload_perf_csv")
        if perf_file is not None:
            try:
                perf_raw_df = pd.read_csv(perf_file)
                st.markdown("**Uploaded File Preview:**")
                st.dataframe(perf_raw_df.head(), use_container_width=True)

                existing_students = db.get_all_students()
                existing_ids = set(existing_students["student_id"].unique()) if not existing_students.empty else set()

                is_valid, val_msg, valid_perf_list = analytics.validate_performance_csv(perf_raw_df, existing_student_ids=existing_ids)
                if not is_valid:
                    st.error(f"❌ Validation Failed: {val_msg}")
                else:
                    st.success(f"✅ {val_msg}")
                    if st.button("🚀 Confirm & Import Performance Records", type="primary", key="btn_import_perf"):
                        pins, prej, perrs = db.bulk_insert_performance(valid_perf_list)
                        st.success(f"Successfully recorded {pins} performance assessment(s).")
                        if prej > 0:
                            st.warning(f"{prej} record(s) could not be inserted due to foreign key or validation issues.")
                            with st.expander("Review Rejected Assessment Rows"):
                                for pe in perrs:
                                    st.write(f"- {pe}")
            except Exception as e:
                st.error(f"Failed to process performance CSV file: {e}")

    with tab_export:
        st.markdown("#### 📤 Export Institutional Analytics Reports")
        st.caption("Generate downloadable CSV reports for academic records, dashboard metrics, and mentoring recommendations.")

        if not db_is_healthy:
            st.error("Database connection required to export data.")
        else:
            merged_df = db.get_merged_data()
            students_df = db.get_all_students()

            exp_col1, exp_col2 = st.columns(2)

            with exp_col1:
                st.markdown("##### 1. Registered Student Directory")
                if not students_df.empty:
                    stu_csv = students_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download Student Directory (CSV)",
                        stu_csv,
                        f"edupulse_students_{date.today()}.csv",
                        "text/csv",
                    )
                else:
                    st.info("No student data available to export.")

                st.markdown("##### 2. Raw Subject Assessment Records")
                if not merged_df.empty:
                    perf_csv = merged_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download All Performance Records (CSV)",
                        perf_csv,
                        f"edupulse_performance_records_{date.today()}.csv",
                        "text/csv",
                    )
                else:
                    st.info("No performance data available to export.")

            with exp_col2:
                st.markdown("##### 3. Student-Level Aggregated Summary")
                if not merged_df.empty:
                    summary_df = analytics.get_student_summary(merged_df)
                    summary_csv = summary_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download Student Performance Summary (CSV)",
                        summary_csv,
                        f"edupulse_student_summary_{date.today()}.csv",
                        "text/csv",
                    )
                else:
                    st.info("No summary data available.")

                st.markdown("##### 4. Rule-Based Mentoring Recommendations")
                if not merged_df.empty:
                    recs = analytics.generate_recommendations(merged_df)
                    recs_df = pd.DataFrame(recs)
                    recs_csv = recs_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download Recommendations Report (CSV)",
                        recs_csv,
                        f"edupulse_academic_recommendations_{date.today()}.csv",
                        "text/csv",
                    )
                else:
                    st.info("No recommendations data available.")


# -----------------------------------------------------------------------------
# PAGE 7: ABOUT PROJECT
# -----------------------------------------------------------------------------

elif page == "About Project":
    st.subheader("ℹ️ About EduPulse — Student Performance Analytics Hub")

    st.markdown(
        """
        ### 🎯 Project Overview
        **EduPulse** is an academic intelligence application designed for colleges and universities to monitor 
        student academic trajectory, attendance compliance, assignment submissions, and daily study hours.
        
        The hub calculates institutional KPIs dynamically from persistent MySQL tables and generates 
        transparent, rule-based recommendations to help faculty identify students who need academic 
        assistance or mentoring early.
        
        ---
        
        ### 🏗️ Architecture & Implementation
        EduPulse follows the clean, maintainable architecture demonstrated in the BizPulse reference project:
        - **Frontend UI:** Built using **Streamlit** with a light theme and deep blue visual hierarchy.
        - **Data Visualizations:** Interactive, responsive charts powered by **Plotly**.
        - **Data Processing:** Robust filtering and metric calculation with **Pandas**.
        - **Database Storage:** Relational persistence with **MySQL Server** via `mysql-connector-python`.
        - **Configuration:** Environment-based credentials via `python-dotenv` without hardcoded secrets.
        
        ---
        
        ### 📐 Relational Database Schema
        ```sql
        students (
            student_id VARCHAR(50) PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            department VARCHAR(50) NOT NULL,
            semester INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        performance (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL,
            subject VARCHAR(100) NOT NULL,
            marks DECIMAL(5,2) NOT NULL CHECK (marks BETWEEN 0 AND 100),
            attendance DECIMAL(5,2) NOT NULL CHECK (attendance BETWEEN 0 AND 100),
            study_hours DECIMAL(4,1) NOT NULL CHECK (study_hours >= 0),
            assignment_score DECIMAL(5,2) NOT NULL CHECK (assignment_score BETWEEN 0 AND 100),
            record_date DATE NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );
        ```
        
        ---
        
        ### 📋 Dynamic Aggregation & Recommendation Logic
        1. **Student vs Subject-Level Distinction:**
           - Student pass percentage is computed at the student level (average across all subjects enrolled), preventing multiple subject entries from biassing the statistic.
        2. **Transparent Advisory Rules:**
           - **Marks < 40:** Flags subject for remedial review and 1-on-1 tutoring.
           - **Attendance < 75%:** Prompts an attendance advisory and student counseling notice.
           - **Assignment Score < 50:** Triggers assignment clinic suggestions.
           - **Marks ≥ 75:** Highlights high academic performance and honors eligibility.
        
        ---
        
        ### 🔒 Security & Reliability Principles
        - Zero hardcoded passwords; configurations stored safely in `.env`.
        - All database queries strictly use parameterized statements (`%s`) preventing SQL injection.
        - Foreign key constraints ensure student deletion safely removes associated records without orphan data.
        - CSV batch imports run inside atomic transactions with complete rollback on unexpected database errors.
        """
    )
