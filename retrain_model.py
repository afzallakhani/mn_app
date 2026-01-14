import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# Old training data
old = pd.read_csv("mn_training_clean.csv")

# New feedback
fb = pd.read_csv("feedback.csv")

# Merge safely (you can improve matching later)
new = fb.rename(columns={
    "llp_mn": "LLP%Mn",
    "actual_femn": "FeMn Used",
    "actual_simn": "Si Mn Used"
})

df = pd.concat([old, new], ignore_index=True)

# Filter junk
df = df[df["LLP%Mn"].between(0.3, 1.2)]

features = [
    "FLP_C","FLP_Mn","FLP_Si","Carbon_Gap",
    "Surface_to_Volume_Index","Metal_Qty"
]

X = df[features]
y = df["LLP%Mn"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = GradientBoostingRegressor(
    n_estimators=400,
    learning_rate=0.04,
    max_depth=3
)

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("New MAE:", mean_absolute_error(y_test, pred))

joblib.dump(model, "mn_recovery_model_v3.pkl")
