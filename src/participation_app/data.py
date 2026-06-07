from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_FILE = ROOT_DIR / "Responses.csv"

COLUMN_MAP = {
    "Timestamp": "timestamp",
    "1.What is your name?": "name",
    "2.What is your USN?": "usn",
    "3.Which deparment?": "dept",
    "4.Which year of study?": "year",
    "5.What is your Gender?": "gender",
    "6.Which activites have you participated in?": "activities",
    "7.How frequently do you participate?": "frequency",
    "8.Have you felt discouraged from joining an activity due to your gender?": "discouraged",
    "9.If yes, Which activity?": "discouraged_activity",
    "10.Are Activites are equally open to every gender?": "openness_score",
    "11.Any other feedback?": "feedback",
}


def load_raw(path: Path = RAW_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path.name} in {path.parent}")
    return pd.read_csv(path)


def clean_responses(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.rename(columns=COLUMN_MAP).copy()

    required_cols = [
        "name",
        "usn",
        "dept",
        "year",
        "gender",
        "activities",
        "frequency",
        "discouraged",
        "openness_score",
    ]
    df["discouraged_activity"] = df["discouraged_activity"].fillna("Not applicable")
    df["feedback"] = df["feedback"].fillna("")
    df = df.dropna(subset=required_cols)
    df = df.drop_duplicates(subset=["usn"], keep="first")

    for col in ["name", "usn", "dept", "year", "gender", "activities", "frequency", "discouraged"]:
        df[col] = df[col].astype(str).str.strip()

    df["gender"] = df["gender"].str.lower().replace(
        {
            "male": "Male",
            "female": "Female",
            "non-binary / other": "Other",
            "prefer not to say": "Other",
            "non-binary": "Other",
            "other": "Other",
        }
    )
    df["gender"] = df["gender"].where(df["gender"].isin(["Male", "Female", "Other"]), "Other")

    dept_map = {
        "cse": "CSE",
        "ise": "ISE",
        "ece": "ECE",
        "eee": "EEE",
        "me": "ME",
        "cv": "CV",
        "civil": "CV",
        "ai&ml": "AI&ML",
        "aiml": "AI&ML",
        "ai & ml": "AI&ML",
        "ai and ml": "AI&ML",
        "mechanical": "ME",
        "electronics": "ECE",
        "cyber security": "Cyber Security",
    }
    df["dept"] = df["dept"].str.lower().replace(dept_map)
    df["dept"] = df["dept"].apply(lambda value: value if value in set(dept_map.values()) else value.upper())

    year_map = {
        "1st year": "1st Year",
        "1": "1st Year",
        "first": "1st Year",
        "2nd year": "2nd Year",
        "2": "2nd Year",
        "second": "2nd Year",
        "3rd year": "3rd Year",
        "3": "3rd Year",
        "third": "3rd Year",
        "4th year": "4th Year",
        "4": "4th Year",
        "fourth": "4th Year",
    }
    df["year"] = df["year"].str.lower().replace(year_map)

    freq_map = {
        "never": "Never",
        "rarely (once a year)": "Rarely",
        "rarely": "Rarely",
        "sometimes (a few times a year)": "Sometimes",
        "sometimes": "Sometimes",
        "regularly (every semester)": "Regularly",
        "regularly": "Regularly",
        "often": "Regularly",
        "always": "Regularly",
    }
    df["frequency"] = df["frequency"].str.lower().replace(freq_map)

    disc_map = {
        "yes": "Yes",
        "no": "No",
        "maybe": "Maybe",
        "maybe / not sure": "Maybe",
        "not sure": "Maybe",
    }
    df["discouraged"] = df["discouraged"].str.lower().replace(disc_map)

    df["openness_score"] = pd.to_numeric(df["openness_score"], errors="coerce")
    df["openness_score"] = df["openness_score"].fillna(df["openness_score"].median()).astype(int)

    return df


def explode_activities(clean_df: pd.DataFrame) -> pd.DataFrame:
    df = clean_df.copy()
    df["activities"] = df["activities"].astype(str).str.strip()
    df = df.assign(activity=df["activities"].str.split(",")).explode("activity")
    df["activity"] = df["activity"].astype(str).str.strip()
    no_activity = {"", "none", "no", "nil", "n/a", "na", "not participated"}
    df = df[~df["activity"].str.lower().isin(no_activity)]
    return df.drop_duplicates(subset=["usn", "activity"])


def load_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    clean_df = clean_responses(load_raw())
    activity_df = explode_activities(clean_df)
    return clean_df, activity_df
