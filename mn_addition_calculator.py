import pandas as pd
import joblib
from masters import GRADE_MASTER, ALLOY_MASTER, CPC_MASTER

# =============================
# LOAD Mn RECOVERY MODEL
# =============================
mn_recovery_model = joblib.load("mn_recovery_model_v2.pkl")

# =============================
# HELPERS
# =============================
def get_surface_to_volume_index(section_size_mm):
    return round(4 / section_size_mm, 4)

def calculate_mn_cushion(grade, section_size, process_risk):
    base_map = {
        "MS": 0.04,
        "A105": 0.03,
        "EN8D": 0.02,
        "CK45": 0.02
    }

    base = base_map.get(grade, 0.03)

    section_adj = 0.01 if section_size <= 75 else -0.01 if section_size >= 130 else 0.0

    risk_adj = {
        "normal": 0.00,
        "slow_cast": 0.01,
        "long_hold": 0.01,
        "purging_issue": 0.01,
        "multiple": 0.02
    }.get(process_risk.lower(), 0.00)

    return round(min(max(base + section_adj + risk_adj, 0.01), 0.07), 3)

def decide_mn_strategy(flp_c, flp_si, grade_data):
    si_headroom = grade_data["Si_Max"] - flp_si
    carbon_gap = grade_data["Target_C"] - flp_c

    if si_headroom < 0.12:
        return "FEMN"
    if carbon_gap > 0.03 and si_headroom > 0.15:
        return "SIMN"
    return "MIX"

# =============================
# MAIN CALCULATOR
# =============================
def calculate_mn_and_cpc_addition(
    grade,
    metal_qty,
    section_size,
    flp_c,
    flp_mn,
    flp_si,
    flp_p,
    process_risk="normal"
):
    grade = grade.strip().upper()
    gm = GRADE_MASTER[grade]

    # -----------------------------
    # LIMITS
    # -----------------------------
    C_MIN, C_MAX = gm["C_Min"], gm["C_Max"]
    MN_MIN, MN_MAX = gm["Mn_Min"], gm["Mn_Max"]
    SI_MIN, SI_MAX = gm["Si_Min"], gm["Si_Max"]

    # -----------------------------
    # AUTO DERIVED
    # -----------------------------
    sv_index = get_surface_to_volume_index(section_size)
    target_c = gm["Target_C"]
    carbon_gap_pct = target_c - flp_c

    mn_strategy = decide_mn_strategy(flp_c, flp_si, gm)

    # -----------------------------
    # TARGET LLP Mn
    # -----------------------------
    cushion = calculate_mn_cushion(grade, section_size, process_risk)
    target_llp_mn = min(gm["Mn_Aim"] + cushion, MN_MAX - 0.01)

    # -----------------------------
    # ML INPUT
    # -----------------------------
    X = pd.DataFrame([{
        "Grade": grade,
        "FLP_Mn": flp_mn,
        "FLP_C": flp_c,
        "FLP_Si": flp_si,
        "FLP_P": flp_p,
        "Carbon_Gap": carbon_gap_pct,
        "CPC_kg_per_ton": 0.0,
        "Metal_Qty": metal_qty,
        "Surface_to_Volume_Index": sv_index,
        "Mn_Addition_Strategy": mn_strategy
    }])

    predicted_recovery = float(mn_recovery_model.predict(X)[0])
    predicted_recovery = min(max(predicted_recovery, 0.60), 0.90)

    # -----------------------------
    # Mn REQUIRED
    # -----------------------------
    mn_gap = max(0, target_llp_mn - flp_mn)
    pure_mn_required = mn_gap * metal_qty * 10
    pure_mn_to_add = pure_mn_required / predicted_recovery

    # -----------------------------
    # INITIAL ALLOY SPLIT
    # -----------------------------
    femn_kg = simn_kg = 0.0

    if mn_strategy == "MIX":
        femn_kg = (pure_mn_to_add / 2) / ALLOY_MASTER["FEMN"]["Mn"]
        simn_kg = (pure_mn_to_add / 2) / ALLOY_MASTER["SIMN"]["Mn"]
    elif mn_strategy == "FEMN":
        femn_kg = pure_mn_to_add / ALLOY_MASTER["FEMN"]["Mn"]
    else:
        simn_kg = pure_mn_to_add / ALLOY_MASTER["SIMN"]["Mn"]

    # -----------------------------
    # 🔒 Si MIN ENFORCEMENT
    # -----------------------------
    si_pickup = (simn_kg * ALLOY_MASTER["SIMN"]["Si"]) / (metal_qty * 10)
    final_si_est = flp_si + si_pickup

    if final_si_est < SI_MIN:
        si_gap_pct = SI_MIN - final_si_est
        si_required_kg = si_gap_pct * metal_qty * 10
        extra_simn_kg = si_required_kg / ALLOY_MASTER["SIMN"]["Si"]

        simn_kg += extra_simn_kg

        # deduct Mn equivalent from FeMn if possible
        mn_from_extra_simn = extra_simn_kg * ALLOY_MASTER["SIMN"]["Mn"]
        if femn_kg > 0:
            femn_kg -= mn_from_extra_simn / ALLOY_MASTER["FEMN"]["Mn"]
            femn_kg = max(femn_kg, 0)

    # -----------------------------
    # FINAL CHEM ESTIMATION
    # -----------------------------
    final_mn_est = flp_mn + (
        (femn_kg * ALLOY_MASTER["FEMN"]["Mn"] +
         simn_kg * ALLOY_MASTER["SIMN"]["Mn"]) * predicted_recovery
        / (metal_qty * 10)
    )

    final_si_est = flp_si + (
        simn_kg * ALLOY_MASTER["SIMN"]["Si"] / (metal_qty * 10)
    )

    final_c_est = flp_c + (
        femn_kg * ALLOY_MASTER["FEMN"]["C"] +
        simn_kg * ALLOY_MASTER["SIMN"]["C"] + 
        cpc_kg *  CPC_MASTER["CPC"]["recovery"]
    ) / (metal_qty * 10)

    # -----------------------------
    # 🔥 HARD SAFETY CHECKS
    # -----------------------------
    errors = []

    if final_mn_est > MN_MAX:
        errors.append(f"Mn exceeds max ({final_mn_est:.3f} > {MN_MAX})")

    if final_si_est > SI_MAX:
        errors.append(f"Si exceeds max ({final_si_est:.3f} > {SI_MAX})")

    if final_c_est > C_MAX:
        errors.append(f"C exceeds max ({final_c_est:.3f} > {C_MAX})")

    if final_si_est < SI_MIN:
        errors.append(f"Si below min ({final_si_est:.3f} < {SI_MIN})")

    if errors:
        return {
            "STATUS": "ERROR",
            "MESSAGE": " / ".join(errors),
            "SUGGESTION": "Adjust strategy (more FeMn / lower target Mn / reduce Si_Min)"
        }

    # -----------------------------
    # CPC (FINAL)
    # -----------------------------
    target_c_pickup = max(0, (target_c - flp_c) * metal_qty * 10)
    carbon_from_alloys = (
        femn_kg * ALLOY_MASTER["FEMN"]["C"] +
        simn_kg * ALLOY_MASTER["SIMN"]["C"]
    )

    net_c_required = target_c_pickup - carbon_from_alloys
    cpc_kg = 0.0 if net_c_required <= 0 else round(
        net_c_required / CPC_MASTER["CPC"]["recovery"], 1
    )

    # -----------------------------
    # OUTPUT
    # -----------------------------
    # return {
    #     "STATUS": "OK",
    #     "Surface_to_Volume_Index": sv_index,
    #     "Mn_Strategy": mn_strategy,
    #     "Target_LLP_Mn": round(target_llp_mn, 3),
    #     "Predicted_Mn_Recovery": round(predicted_recovery, 3),
    #     "FeMn_kg": round(femn_kg, 1),
    #     "SiMn_kg": round(simn_kg, 1),
    #     "Final_Mn_Est_%": round(final_mn_est, 3),
    #     "Final_Si_Est_%": round(final_si_est, 3),
    #     "Final_C_Est_%": round(final_c_est, 3),
    #     "CPC_kg": cpc_kg
    # }
    return {
    "STATUS": "OK",
    "FeMn_kg": round(femn_kg, 1),
    "SiMn_kg": round(simn_kg, 1),
    "CPC_kg": cpc_kg,

    # 👇 Predicted LLP chemistry
    "Pred_LLP_C": round(final_c_est, 3),
    "Pred_LLP_Mn": round(final_mn_est, 3),
    "Pred_LLP_Si": round(final_si_est, 3),
    "Pred_LLP_P": round(flp_p, 3)
}
