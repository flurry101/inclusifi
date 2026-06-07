import re
from collections import Counter

import pandas as pd


STOPWORDS = {
    "a",
    "about",
    "all",
    "also",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "do",
    "for",
    "from",
    "had",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "its",
    "just",
    "more",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "should",
    "so",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "to",
    "too",
    "us",
    "was",
    "we",
    "were",
    "with",
    "would",
    "yes",
}

EMPTY_FEEDBACK = {"", "-", "na", "n/a", "nil", "no", "nope", "none", "nothing"}
POSITIVE_WORDS = {
    "accessible",
    "amazing",
    "balanced",
    "better",
    "comfortable",
    "encourage",
    "encouraging",
    "equal",
    "fair",
    "friendly",
    "good",
    "great",
    "helpful",
    "inclusive",
    "interesting",
    "nice",
    "open",
    "support",
    "supportive",
    "welcoming",
}
NEGATIVE_WORDS = {
    "bad",
    "bias",
    "biased",
    "boring",
    "clash",
    "discourage",
    "discouraged",
    "difficult",
    "excluded",
    "fear",
    "hard",
    "hesitate",
    "ignored",
    "issue",
    "less",
    "problem",
    "rarely",
    "scared",
    "timing",
    "uncomfortable",
    "unfair",
}
YEAR_ORDER = ["1st Year", "2nd Year", "3rd Year", "4th Year"]


def build_action_insights(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> list[dict[str, str]]:
    insights = []

    low_frequency = student_df["frequency"].isin(["Rarely", "Never"]).mean() * 100
    if low_frequency >= 35:
        insights.append(
            {
                "priority": "High",
                "issue": "Many students participate rarely or never",
                "action": "Improve event publicity through class groups, posters, CR announcements, and reminders 2-3 days before events.",
            }
        )

    discouraged = student_df[student_df["discouraged"].isin(["Yes", "Maybe"])]
    if not discouraged.empty:
        top_group = discouraged["gender"].value_counts().idxmax()
        insights.append(
            {
                "priority": "High",
                "issue": f"{len(discouraged)} students reported or hinted at discouragement; most are {top_group}",
                "action": "Review event rules, team selection, communication tone, and beginner support for possible exclusion points.",
            }
        )

    if not activity_df.empty:
        activity_counts = activity_df["activity"].value_counts()
        least_activity = activity_counts.idxmin()
        insights.append(
            {
                "priority": "Medium",
                "issue": f"Lowest participation activity: {least_activity}",
                "action": "Ask that club to run a beginner-friendly intro session and advertise what students will gain by joining.",
            }
        )

    insights.extend(build_department_insights(student_df, activity_df))
    insights.extend(build_year_insights(student_df, activity_df))

    feedback_text = " ".join(student_df["feedback"].fillna("").str.lower())
    if any(term in feedback_text for term in ["timing", "time", "clash", "classes", "class"]):
        insights.append(
            {
                "priority": "Medium",
                "issue": "Feedback suggests timing or class clashes",
                "action": "Publish schedules earlier and prefer lunch breaks, club hours, or weekends for larger events.",
            }
        )

    if any(term in feedback_text for term in ["online", "introvert", "game"]):
        insights.append(
            {
                "priority": "Low",
                "issue": "Some students may prefer low-pressure or online formats",
                "action": "Add occasional online, individual, or beginner-friendly events for students hesitant to join in person.",
            }
        )

    if not insights:
        insights.append(
            {
                "priority": "Low",
                "issue": "No major barrier stands out in the current data",
                "action": "Keep collecting responses after each event to track whether participation stays balanced.",
            }
        )

    return insights


def build_department_insights(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> list[dict[str, str]]:
    if student_df.empty or "dept" not in student_df:
        return []

    insights = []
    dept_summary = (
        student_df.assign(
            low_participation=student_df["frequency"].isin(["Rarely", "Never"]),
            discouraged_flag=student_df["discouraged"].isin(["Yes", "Maybe"]),
        )
        .groupby("dept")
        .agg(
            students=("usn", "nunique"),
            low_participation=("low_participation", "mean"),
            discouraged=("discouraged_flag", "mean"),
            openness=("openness_score", "mean"),
        )
    )
    dept_summary = dept_summary[dept_summary["students"] >= 2]

    if not dept_summary.empty:
        low_dept = dept_summary["low_participation"].idxmax()
        low_rate = dept_summary.loc[low_dept, "low_participation"] * 100
        if low_rate >= 35:
            insights.append(
                {
                    "priority": "High",
                    "issue": f"{low_dept} has the highest low-participation rate ({low_rate:.0f}%)",
                    "action": "Run department-targeted publicity through class representatives and invite that department into mixed teams.",
                }
            )

        openness_dept = dept_summary["openness"].idxmin()
        openness_score = dept_summary.loc[openness_dept, "openness"]
        if openness_score <= 3.8:
            insights.append(
                {
                    "priority": "Medium",
                    "issue": f"{openness_dept} reports the lowest openness score ({openness_score:.1f}/5)",
                    "action": "Collect short follow-up comments from that department and check whether event rules, timing, or communication are creating barriers.",
                }
            )

    if not activity_df.empty:
        dept_activity = activity_df.groupby("dept")["activity"].nunique()
        least_varied_dept = dept_activity.idxmin()
        if dept_activity.loc[least_varied_dept] <= max(1, activity_df["activity"].nunique() // 2):
            insights.append(
                {
                    "priority": "Medium",
                    "issue": f"{least_varied_dept} responses are concentrated in fewer activity types",
                    "action": "Promote at least two non-technical and two technical options to that department so students see more entry points.",
                }
            )

    return insights[:2]


def build_year_insights(student_df: pd.DataFrame, activity_df: pd.DataFrame) -> list[dict[str, str]]:
    if student_df.empty or "year" not in student_df:
        return []

    insights = []
    year_summary = (
        student_df.assign(
            low_participation=student_df["frequency"].isin(["Rarely", "Never"]),
            discouraged_flag=student_df["discouraged"].isin(["Yes", "Maybe"]),
        )
        .groupby("year")
        .agg(
            students=("usn", "nunique"),
            low_participation=("low_participation", "mean"),
            discouraged=("discouraged_flag", "mean"),
            openness=("openness_score", "mean"),
        )
    )
    year_summary = year_summary[year_summary["students"] >= 2]

    if not year_summary.empty:
        low_year = year_summary["low_participation"].idxmax()
        low_rate = year_summary.loc[low_year, "low_participation"] * 100
        if low_rate >= 35:
            insights.append(
                {
                    "priority": "High",
                    "issue": f"{low_year} students show the highest low participation ({low_rate:.0f}%)",
                    "action": "Create year-specific outreach: orientation-style sessions for juniors and leadership/project roles for seniors.",
                }
            )

        discouraged_year = year_summary["discouraged"].idxmax()
        discouraged_rate = year_summary.loc[discouraged_year, "discouraged"] * 100
        if discouraged_rate >= 25:
            insights.append(
                {
                    "priority": "Medium",
                    "issue": f"{discouraged_year} has the strongest discouragement signal ({discouraged_rate:.0f}%)",
                    "action": "Ask mentors from that year to review selection practices and make beginner expectations clearer before events.",
                }
            )

    if not activity_df.empty:
        activity_by_year = activity_df.groupby("year")["activity"].nunique()
        ordered = activity_by_year.reindex([year for year in YEAR_ORDER if year in activity_by_year.index]).dropna()
        if len(ordered) >= 2 and ordered.iloc[0] < ordered.max():
            insights.append(
                {
                    "priority": "Low",
                    "issue": "First-year activity variety is lower than other years",
                    "action": "Bundle events into a first-year sampler week so new students can try multiple clubs without committing early.",
                }
            )

    return insights[:2]


def feedback_records(student_df: pd.DataFrame) -> list[str]:
    if "feedback" not in student_df:
        return []
    records = []
    for value in student_df["feedback"].fillna(""):
        text = str(value).strip()
        if text.lower() not in EMPTY_FEEDBACK:
            records.append(text)
    return records


def tokenize_feedback(records: list[str]) -> list[str]:
    tokens = []
    for record in records:
        words = re.findall(r"[a-zA-Z][a-zA-Z&'-]{2,}", record.lower())
        tokens.extend(word.strip("'") for word in words if word not in STOPWORDS)
    return tokens


def feedback_keyword_counts(student_df: pd.DataFrame, limit: int = 30) -> Counter:
    tokens = tokenize_feedback(feedback_records(student_df))
    return Counter(tokens).most_common(limit)


def feedback_sentiment_summary(student_df: pd.DataFrame) -> dict[str, float | int | str]:
    records = feedback_records(student_df)
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    total_score = 0

    for record in records:
        tokens = tokenize_feedback([record])
        score = sum(token in POSITIVE_WORDS for token in tokens) - sum(token in NEGATIVE_WORDS for token in tokens)
        total_score += score
        if score > 0:
            counts["Positive"] += 1
        elif score < 0:
            counts["Negative"] += 1
        else:
            counts["Neutral"] += 1

    dominant = max(counts, key=counts.get) if records else "Neutral"
    return {
        "responses": len(records),
        "positive": counts["Positive"],
        "neutral": counts["Neutral"],
        "negative": counts["Negative"],
        "average_score": total_score / len(records) if records else 0,
        "dominant": dominant,
    }
