import html

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from .data import RAW_FILE, load_dataset
from .insights import (
    build_action_insights,
    feedback_keyword_counts,
    feedback_records,
    feedback_sentiment_summary,
)

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None


GENDER_PALETTE = {"Female": "#E05263", "Male": "#2F80ED", "Other": "#8F62D8"}
FREQ_ORDER = ["Regularly", "Sometimes", "Rarely", "Never"]
FREQ_COLORS = ["#2F9E73", "#F2C94C", "#E05263", "#9CA3AF"]


def main() -> None:
    st.set_page_config(
        page_title="Inclusifi",
        page_icon="📊",
        layout="wide",
    )
    inject_css()

    try:
        student_df, activity_df = load_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    with st.sidebar:
        st.header("Filters")
        st.caption(f"Source: {RAW_FILE.name}")

        genders = sorted(activity_df["gender"].dropna().unique())
        depts = sorted(activity_df["dept"].dropna().unique())
        years = sorted(activity_df["year"].dropna().unique())
        activities = sorted(activity_df["activity"].dropna().unique())

        sel_gender = st.multiselect("Gender", genders, default=genders)
        sel_dept = st.multiselect("Department", depts, default=depts)
        sel_year = st.multiselect("Year", years, default=years)
        sel_activity = st.multiselect("Activity", activities, default=activities)

    filtered_activity = activity_df[
        activity_df["gender"].isin(sel_gender)
        & activity_df["dept"].isin(sel_dept)
        & activity_df["year"].isin(sel_year)
        & activity_df["activity"].isin(sel_activity)
    ].copy()
    filtered_students = student_df[
        student_df["usn"].isin(filtered_activity["usn"].unique())
    ].copy()

    st.title("Inclusifi")
    st.markdown(
        '<p class="intro-text">A dashboard to analyze student participation in college activities, with a focus on identifying barriers and opportunities for inclusion.</p>',
        unsafe_allow_html=True,
    )

    if filtered_activity.empty:
        st.warning("No responses match these filters.")
        st.stop()

    render_metrics(filtered_students, filtered_activity)
    render_insights(filtered_students, filtered_activity)
    render_charts(filtered_students, filtered_activity)
    render_feedback_insights(filtered_students)
    render_table(filtered_activity)


def inject_css() -> None:
    st.markdown(
        """
        <style>
            .stApp { background: #F8F7F4; }
            [data-testid="stSidebar"] { background: #20242C; }
            [data-testid="stSidebar"] * { color: #F3F4F6 !important; }
            h1, h2, h3 { color: #1F2937 !important; letter-spacing: 0; }
            .intro-text {
                color: #374151 !important;
                font-size: 15px;
                font-weight: 600;
                margin-top: -0.5rem;
                margin-bottom: 1rem;
            }
            .block-container { padding-top: 2rem; }
            .metric-panel {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 16px 18px;
                min-height: 104px;
            }
            .metric-label {
                color: #6B7280;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .metric-value {
                color: #111827;
                font-size: 28px;
                font-weight: 700;
                margin-top: 6px;
            }
            .metric-note { color: #6B7280; font-size: 12px; margin-top: 4px; }
            .insight {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-left: 4px solid #2F80ED;
                border-radius: 8px;
                padding: 12px 14px;
                margin-bottom: 10px;
            }
            .insight strong { color: #111827; }
            .insight span { color: #4B5563; }
            [data-testid="stExpander"] {
                background: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
            }
            [data-testid="stExpander"] details summary {
                color: #111827 !important;
                font-weight: 700;
            }
            [data-testid="stExpander"] details summary * {
                color: #111827 !important;
            }
            [data-testid="stExpander"] details summary svg {
                color: #111827 !important;
                fill: #111827 !important;
                stroke: #111827 !important;
            }
            [data-testid="stExpander"] details summary:hover {
                background: #EEF2F7;
            }
            [data-testid="stExpander"] details[open] summary {
                background: #F3F4F6;
                border-radius: 8px 8px 0 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> None:
    total_students = student_df["usn"].nunique()
    low_participation = student_df["frequency"].isin(["Rarely", "Never"]).mean() * 100
    discouraged_pct = student_df["discouraged"].isin(["Yes", "Maybe"]).mean() * 100
    avg_openness = student_df["openness_score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Students", f"{total_students}", f"{len(activity_df)} activity entries"),
        ("Low Participation", f"{low_participation:.0f}%", "Rarely or never participate"),
        ("Discouraged", f"{discouraged_pct:.0f}%", "Answered Yes or Maybe"),
        ("Avg Openness", f"{avg_openness:.1f}/5", "Higher means more inclusive"),
    ]
    for col, (label, value, note) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-panel">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_insights(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> None:
    st.subheader("Actionable Insights")
    st.markdown(
        '<p class="intro-text">Key issues identified from the data, with recommended actions to improve participation and inclusion.</p>',
        unsafe_allow_html=True,
    )
    for item in build_action_insights(student_df, activity_df):
        priority = html.escape(item["priority"])
        issue = html.escape(item["issue"])
        action = html.escape(item["action"])
        st.markdown(
            f"""
            <div class="insight">
                <strong>{priority}: {issue}</strong><br>
                <span>{action}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_charts(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> None:
    st.subheader("Participation Patterns")

    left, right = st.columns([2, 3])

    with left:
        fig, ax = plt.subplots(figsize=(5, 4))
        gender_counts = student_df["gender"].value_counts()
        colors = [GENDER_PALETTE.get(gender, "#9CA3AF") for gender in gender_counts.index]
        ax.pie(
            gender_counts,
            labels=gender_counts.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
            textprops={"color": "#1F2937", "fontsize": 10},
        )
        ax.set_title("Overall gender distribution", loc="left", fontweight="bold", color="#1F2937")
        st.pyplot(fig)
        plt.close(fig)

    with right:
        fig, ax = plt.subplots(figsize=(8, 4))
        activity_gender = activity_df.groupby(["activity", "gender"]).size().unstack(fill_value=0)
        activity_gender = activity_gender.reindex(columns=["Female", "Male", "Other"], fill_value=0)
        activity_gender.plot(
            kind="bar",
            ax=ax,
            color=[GENDER_PALETTE["Female"], GENDER_PALETTE["Male"], GENDER_PALETTE["Other"]],
            width=0.75,
        )
        style_axis(ax, "Activity participation by gender", "Count")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        st.pyplot(fig)
        plt.close(fig)

    left, right = st.columns([2, 3])
    with left:
        fig, ax = plt.subplots(figsize=(5, 4))
        frequency_gender = student_df.groupby(["gender", "frequency"]).size().unstack(fill_value=0)
        frequency_gender = frequency_gender.reindex(columns=FREQ_ORDER, fill_value=0)
        frequency_pct = frequency_gender.div(frequency_gender.sum(axis=1), axis=0).fillna(0) * 100
        frequency_pct.plot(kind="bar", stacked=True, ax=ax, color=FREQ_COLORS)
        style_axis(ax, "Participation frequency", "Percent")
        ax.set_xlabel("")
        ax.set_ylim(0, 100)
        st.pyplot(fig)
        plt.close(fig)

    with right:
        fig, ax = plt.subplots(figsize=(8, 4))
        heatmap = activity_df.groupby(["dept", "activity"]).size().unstack(fill_value=0)
        sns.heatmap(heatmap, ax=ax, cmap="YlGnBu", annot=True, fmt="d", linewidths=0.5)
        ax.set_title("Activity by department", loc="left", fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("")
        st.pyplot(fig)
        plt.close(fig)

    left, right = st.columns([3, 2])
    with left:
        fig, ax = plt.subplots(figsize=(8, 4))
        year_gender = student_df.groupby(["year", "gender"]).size().unstack(fill_value=0)
        year_order = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        year_gender = year_gender.reindex(index=[y for y in year_order if y in year_gender.index])
        year_gender = year_gender.reindex(columns=["Female", "Male", "Other"], fill_value=0)
        year_gender.plot(
            kind="bar",
            ax=ax,
            color=[GENDER_PALETTE["Female"], GENDER_PALETTE["Male"], GENDER_PALETTE["Other"]],
            width=0.75,
        )
        style_axis(ax, "Year-wise gender distribution", "Count")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
        st.pyplot(fig)
        plt.close(fig)

    with right:
        fig, ax = plt.subplots(figsize=(5, 4))
        order = [gender for gender in ["Female", "Male", "Other"] if gender in student_df["gender"].values]
        palette = {gender: GENDER_PALETTE.get(gender, "#9CA3AF") for gender in order}
        sns.boxplot(
            data=student_df,
            x="gender",
            y="openness_score",
            hue="gender",
            order=order,
            palette=palette,
            ax=ax,
            legend=False,
            linewidth=1.2,
            fliersize=0,
        )
        sns.stripplot(
            data=student_df,
            x="gender",
            y="openness_score",
            hue="gender",
            order=order,
            palette=palette,
            ax=ax,
            legend=False,
            jitter=True,
            size=5,
            alpha=0.75,
        )
        style_axis(ax, "Openness score by gender", "Score")
        ax.set_xlabel("")
        ax.set_ylim(0.5, 5.5)
        st.pyplot(fig)
        plt.close(fig)


def render_feedback_insights(student_df: pd.DataFrame) -> None:
    st.subheader("Feedback Insights")

    records = feedback_records(student_df)
    sentiment = feedback_sentiment_summary(student_df)
    keywords = feedback_keyword_counts(student_df, limit=20)

    c1, c2, c3, c4 = st.columns(4)
    feedback_metrics = [
        ("Feedback Responses", f"{sentiment['responses']}", "Non-empty qualitative comments"),
        ("Dominant Sentiment", str(sentiment["dominant"]), "Lexicon-based NLP signal"),
        ("Positive", f"{sentiment['positive']}", "Comments with positive keywords"),
        ("Negative", f"{sentiment['negative']}", "Comments with barrier keywords"),
    ]
    for col, (label, value, note) in zip([c1, c2, c3, c4], feedback_metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-panel">
                    <div class="metric-label">{html.escape(label)}</div>
                    <div class="metric-value">{html.escape(value)}</div>
                    <div class="metric-note">{html.escape(note)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left, right = st.columns([3, 2])
    with left:
        if keywords and WordCloud is not None:
            wordcloud = WordCloud(
                width=900,
                height=420,
                background_color="white",
                colormap="viridis",
                prefer_horizontal=0.9,
                collocations=False,
                min_font_size=10,
            ).generate_from_frequencies(dict(keywords))
            fig, ax = plt.subplots(figsize=(9, 4.2))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.set_title("Feedback keyword word cloud", loc="left", fontweight="bold", color="#1F2937")
            ax.axis("off")
            st.pyplot(fig)
            plt.close(fig)
        elif not records:
            st.info("No open-ended feedback is available for the current filters.")
        else:
            st.warning("Install the wordcloud package to render the feedback word cloud.")

    with right:
        if keywords:
            keyword_df = pd.DataFrame(keywords, columns=["Keyword", "Mentions"])
            fig, ax = plt.subplots(figsize=(5, 4.2))
            sns.barplot(data=keyword_df.head(10), y="Keyword", x="Mentions", ax=ax, color="#2F80ED")
            style_axis(ax, "Top feedback keywords", "Mentions")
            ax.set_xlabel("Mentions")
            ax.set_ylabel("")
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("No meaningful feedback keywords found for the current filters.")

    with st.expander("Read qualitative feedback"):
        if records:
            st.dataframe(pd.DataFrame({"feedback": records}), use_container_width=True)
        else:
            st.write("No feedback comments to show.")


def render_table(activity_df: pd.DataFrame) -> None:
    with st.expander("View filtered responses"):
        cols = ["name", "usn", "dept", "year", "gender", "activity", "frequency", "discouraged", "openness_score", "feedback"]
        st.dataframe(activity_df[cols].reset_index(drop=True), use_container_width=True)


def style_axis(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontweight="bold", color="#1F2937")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#E5E7EB", linestyle="--", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
