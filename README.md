### Inclusifi

** Student Activity Inclusion Dashboard
**

A small Streamlit dashboard for helping college clubs and coordinators understand participation, inclusiveness, discouragement, and publicity gaps in student activities.

#### Run

```powershell
.\run_app.ps1
```

The script creates/uses `.venv`, installs dependencies, reads `Responses.csv`, cleans the survey data in memory, and opens the interactive dashboard.

If dependencies are already installed, you can also run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

#### Project Structure

```text
.
├── app.py                         # One-step Streamlit entry point
├── run_app.ps1                    # One-command local runner
├── Responses.csv                 # Raw survey responses
├── requirements.txt               # Python dependencies
├── src/
│   └── participation_app/
│       ├── data.py                # Load, clean, and explore activity data
│       ├── dashboard.py           # Streamlit UI and charts
│       └── insights.py            # Coordinator-focused recommendations
```

#### What Coordinators Can Use It For

- Spot low-participation activities.
- Compare participation across gender, department, and year.
- Review year-wise and department-wise action insights.
- Identify discouragement signals.
- Process qualitative feedback with keyword extraction, sentiment signals, and a word cloud.
- Review actionable recommendations for publicity, timing, and beginner support.
- Filter responses for a specific activity or department.
