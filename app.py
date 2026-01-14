from fastapi import FastAPI
from pydantic import BaseModel
from mn_addition_calculator import calculate_mn_and_cpc_addition
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mn + CPC Advisor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
FEEDBACK_FILE = "feedback.csv"

# -----------------------------
# INPUT SCHEMA
# -----------------------------
class PredictionInput(BaseModel):
    grade: str
    metal_qty: float
    section_size: int
    flp_c: float
    flp_mn: float
    flp_si: float
    flp_p: float
    process_risk: str = "normal"

class FeedbackInput(BaseModel):
    heat_id: str
    actual_femn: float
    actual_simn: float
    actual_cpc: float
    llp_c: float
    llp_mn: float
    llp_si: float
    llp_p: float

# -----------------------------
# PREDICTION ENDPOINT
# -----------------------------
@app.post("/predict")
def predict(data: PredictionInput):
    result = calculate_mn_and_cpc_addition(
        grade=data.grade,
        metal_qty=data.metal_qty,
        section_size=data.section_size,
        flp_c=data.flp_c,
        flp_mn=data.flp_mn,
        flp_si=data.flp_si,
        flp_p=data.flp_p,
        process_risk=data.process_risk
    )
    return result

# -----------------------------
# FEEDBACK ENDPOINT
# -----------------------------
@app.post("/feedback")
def feedback(data: FeedbackInput):
    row = {
        "timestamp": datetime.now().isoformat(),
        **data.dict()
    }

    try:
        df = pd.read_csv(FEEDBACK_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=row.keys())

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)

    return {"status": "saved"}
