import pandas as pd

# =============================
# LOAD GRADE MASTER
# =============================
grade_df = pd.read_csv("data/heatsSafa - Grade_Master.csv")
grade_df["Grade"] = grade_df["Grade"].astype(str).str.strip().str.upper()

GRADE_MASTER = {}

for _, row in grade_df.iterrows():
    grade = row["Grade"]

    GRADE_MASTER[grade] = {
        "C_Min": float(row["C_Min"]),
        "C_Max": float(row["C_Max"]),
        "Target_C": float(row["C_Aim"]),

        "Mn_Min": float(row["Mn_Min"]),
        "Mn_Max": float(row["Mn_Max"]),
        "Mn_Aim": float(row["Mn_Aim"]),

        "Si_Min": float(row["Si_Min"]),
        "Si_Max": float(row["Si_Max"]),
    }

# =============================
# LOAD ALLOY MASTER (UNIT SAFE)
# =============================
alloy_df = pd.read_csv("data/heatsSafa - Alloy Master.csv")

ALLOY_MASTER = {}

def norm(x):
    x = float(x)
    return x / 100 if x > 1 else x

for _, row in alloy_df.iterrows():
    material = row["MATERIAL"].strip().upper()

    ALLOY_MASTER[material] = {
        "Mn": norm(row["Mn%"]),
        "Si": norm(row["Si%"]),
        "C": norm(row["C%"]),
        "P": norm(row["P%"])
    }

# =============================
# LOAD CPC MASTER
# =============================
cpc_df = pd.read_csv("data/heatsSafa - CPC Master.csv")

CPC_MASTER = {}

for _, row in cpc_df.iterrows():
    material = row["MATERIAL"].strip().upper()

    CPC_MASTER[material] = {
        "C": norm(row["Fixed C%"]),
        "recovery": norm(row["Typical Recovery"])
    }
