import os
from fastapi import FastAPI
from pydantic import BaseModel
from mn_addition_calculator import calculate_mn_and_cpc_addition
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
# from feedback_storage import save_feedback_csv
# from google_sheet import save_feedback_to_gsheet
from feedback_storage import save_feedback_csv
from google_sheet import save_feedback_to_sheet

from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import Request
from dotenv import load_dotenv
from typing import Optional
load_dotenv()
IS_RENDER = os.getenv("RENDER") == "true"

app = FastAPI(title="Mn + CPC Advisor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackInput(BaseModel):
    grade: str
    metal_qty: float
    section_size: int

    flp_c: float
    flp_mn: float
    flp_si: float
    flp_p: float

    pred_femn: float
    pred_simn: float
    pred_cpc: float
    pred_llp_c: float
    pred_llp_mn: float
    pred_llp_si: float

    actual_femn: float
    actual_simn: float
    actual_cpc: float
    actual_llp_c: float
    actual_llp_mn: float
    actual_llp_si: float
    actual_llp_p: float

    remarks: str = ""
# FEEDBACK_FILE = "feedback.csv"

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



# -----------------------------
# PREDICTION ENDPOINT
# -----------------------------
# @app.post("/predict")
# def predict(data: PredictionInput):
#     result = calculate_mn_and_cpc_addition(
#         grade=data.grade,
#         metal_qty=data.metal_qty,
#         section_size=data.section_size,
#         flp_c=data.flp_c,
#         flp_mn=data.flp_mn,
#         flp_si=data.flp_si,
#         flp_p=data.flp_p,
#         process_risk=data.process_risk
#     )
#     return result
@app.post("/predict")
def predict(data: PredictionInput):
    try:
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
    except Exception as e:
        print("❌ PREDICT ERROR:", e)
        raise

# -----------------------------
# FEEDBACK ENDPOINT
# # -----------------------------
# @app.post("/feedback")
# def feedback(data: FeedbackInput):
#     row = {
#         "timestamp": datetime.now().isoformat(),
#         **data.dict()
#     }

#     try:
#         df = pd.read_csv(FEEDBACK_FILE)
#     except FileNotFoundError:
#         df = pd.DataFrame(columns=row.keys())

#     df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
#     df.to_csv(FEEDBACK_FILE, index=False)

#     return {"status": "saved"}


# @app.post("/feedback")
# def feedback(data: FeedbackData):
#     row = {
#         "timestamp": datetime.now().isoformat(),
#         **data.dict()
#     }

#     # 1️⃣ Always save locally (good for debugging & backup)
#     save_feedback_csv(row)

#     # 2️⃣ Try Google Sheet (optional, safe)
#     save_feedback_to_gsheet(row)

#     return {"status": "saved"}
# @app.post("/feedback")
# def feedback(data: FeedbackData):
#     row = data.dict()

#     # 1️⃣ Save locally (safe fallback)
#     save_feedback_csv(row)

#     # 2️⃣ Save to Google Sheet (cloud learning)
#     try:
#         save_feedback_to_sheet(row)
#     except Exception as e:
#         print("Google Sheet error:", e)

#     return {"status": "saved"}
@app.post("/feedback")
def feedback(data: FeedbackInput):
    row = data.dict()

    if IS_RENDER:
        save_feedback_to_sheet(row)
    else:
        save_feedback_csv(row)

    return {"status": "saved"}

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


