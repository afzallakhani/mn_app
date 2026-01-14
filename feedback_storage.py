import pandas as pd
from pathlib import Path
from datetime import datetime

CSV_FILE = Path("feedback.csv")

def save_feedback_csv(data: dict):
    data = data.copy()
    data["timestamp"] = datetime.now().isoformat()

    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])

    df.to_csv(CSV_FILE, index=False)
