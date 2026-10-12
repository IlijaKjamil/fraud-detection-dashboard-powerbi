"""
Fraud Detection Scoring Model
==============================
Portfolio project — NovaPay Payments (fictional)

Pipeline:
  Raw transaction data
  → Feature engineering (velocity, deviation, risk signals)
  → Rule-based fraud scoring (0–100)
  → Flag assignment: Clean / Review / Block
  → Output: fraud_transactions_scored.csv

Scoring logic
-------------
Each transaction receives a Fraud_Risk_Score (0–100) built from
five weighted signal groups:

  1. Merchant Category Risk     (0–20 pts)
     High-risk categories (Crypto Exchange, Wire Transfer, Gambling,
     Electronics) carry elevated base scores.

  2. Channel Risk               (0–15 pts)
     Phone Order and Online channels are higher-risk than Card Present.

  3. Geography Risk             (0–16 pts)
     Per-state fraud multiplier derived from historical loss rates.

  4. Behavioural Signals        (0–33 pts)
     - Amount vs user baseline (>3× baseline = +10 pts)
     - Off-hours transaction (midnight–5am or 11pm+ = +8 pts)
     - Foreign currency = +5 pts
     - Weekend transaction = +3 pts
     - Round-number amount (ending .00) = +7 pts

  5. Pattern Injection          (+35–50 pts, additive)
     Three explicit fraud patterns boost the score directly:
     - Card testing: Online + amount < $5
     - Account takeover: Foreign currency + Wire/Crypto category
     - High-value electronics burst: Electronics + amount > $500

Flag thresholds
---------------
  Fraud_Risk_Score >= 70  →  Block
  Fraud_Risk_Score >= 45  →  Review
  Fraud_Risk_Score <  45  →  Clean

Usage
-----
  python fraud_scoring_model.py

Output
------
  fraud_transactions_scored.csv — one row per transaction with
  all engineered features and Fraud_Risk_Score / Fraud_Flag appended.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# ── constants ────────────────────────────────────────────────────

N            = 5000
N_USERS      = 400
N_MERCHANTS  = 120

MERCHANT_CATEGORIES = {
    "Grocery":         {"risk_pts": 2,  "avg_amount": 85,   "std": 40},
    "Gas Station":     {"risk_pts": 3,  "avg_amount": 55,   "std": 20},
    "Restaurant":      {"risk_pts": 2,  "avg_amount": 45,   "std": 25},
    "Online Retail":   {"risk_pts": 8,  "avg_amount": 120,  "std": 80},
    "Electronics":     {"risk_pts": 14, "avg_amount": 350,  "std": 200},
    "Crypto Exchange": {"risk_pts": 20, "avg_amount": 800,  "std": 500},
    "Wire Transfer":   {"risk_pts": 18, "avg_amount": 1200, "std": 800},
    "Gambling":        {"risk_pts": 16, "avg_amount": 250,  "std": 150},
    "Pharmacy":        {"risk_pts": 3,  "avg_amount": 60,   "std": 30},
    "Travel":          {"risk_pts": 6,  "avg_amount": 450,  "std": 300},
    "Clothing":        {"risk_pts": 5,  "avg_amount": 95,   "std": 55},
    "Subscription":    {"risk_pts": 7,  "avg_amount": 15,   "std": 8},
}

CHANNEL_RISK = {
    "Card Present": 2,
    "Online":       15,
    "Mobile App":   8,
    "ATM":          10,
    "Phone Order":  14,
}

STATES = [
    "CA","TX","NY","FL","IL","PA","OH","GA","NC","MI",
    "NJ","VA","WA","AZ","MA","TN","IN","MO","MD","WI",
    "CO","MN","SC","AL","LA","KY","OR","OK","CT","UT",
]
STATE_RISK = {s: np.random.uniform(1, 8) for s in STATES}
for s in ["NY", "FL", "CA", "NJ"]:
    STATE_RISK[s] = np.random.uniform(10, 16)

CURRENCIES = ["USD"] * 85 + ["EUR"] * 8 + ["GBP"] * 4 + ["CAD"] * 3

FX = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "CAD": 0.74}

# ── build merchant and user rosters ─────────────────────────────

cats = list(MERCHANT_CATEGORIES.keys())
prefixes = ["Swift","Prime","Metro","Apex","Nova","Eagle","Summit","Vertex"]

merchant_names   = [f"{random.choice(prefixes)} {random.choice(cats)} #{i+1:03d}" for i in range(N_MERCHANTS)]
merchant_cats    = [random.choice(cats) for _ in range(N_MERCHANTS)]
merchant_states  = [random.choice(STATES) for _ in range(N_MERCHANTS)]

user_avg_amount  = {u: np.random.uniform(30, 300) for u in range(N_USERS)}
user_home_state  = {u: random.choice(STATES) for u in range(N_USERS)}

# ── generate and score transactions ─────────────────────────────

start_date = datetime(2024, 1, 1)
rows = []
txn_counter = 10000

for _ in range(N):
    txn_id    = f"TXN{txn_counter:06d}"
    txn_counter += 1

    user_id   = random.randint(0, N_USERS - 1)
    m_idx     = random.randint(0, N_MERCHANTS - 1)
    cat       = merchant_cats[m_idx]
    state     = merchant_states[m_idx]
    channel   = random.choice(list(CHANNEL_RISK.keys()))
    currency  = random.choice(CURRENCIES)

    cat_p     = MERCHANT_CATEGORIES[cat]
    amount    = max(1.0, round(np.random.normal(cat_p["avg_amount"], cat_p["std"]), 2))
    amount_usd = round(amount * FX[currency], 2)

    days_offset = random.randint(0, 364)
    txn_date    = start_date + timedelta(days=days_offset)
    hour_w      = np.array([1,1,1,1,1,1,2,4,6,7,8,8,8,8,7,7,6,5,4,4,3,2,2,1], dtype=float)
    hour_w     /= hour_w.sum()
    hour        = int(np.random.choice(range(24), p=hour_w))
    txn_dt      = txn_date.replace(hour=hour, minute=random.randint(0,59), second=random.randint(0,59))
    is_weekend  = 1 if txn_date.weekday() >= 5 else 0

    baseline    = user_avg_amount[user_id]
    amt_ratio   = round(amount / baseline, 2)

    # ── scoring ──────────────────────────────────────────────────

    # 1. merchant category risk (0–20)
    score = cat_p["risk_pts"]

    # 2. channel risk (0–15)
    score += CHANNEL_RISK[channel]

    # 3. geography risk (0–16, normalised)
    score += min(16, STATE_RISK[state])

    # 4. behavioural signals
    if amt_ratio > 3:
        score += 10          # amount vs baseline
    if hour < 5 or hour >= 23:
        score += 8           # off-hours
    if currency != "USD":
        score += 5           # foreign currency
    if is_weekend:
        score += 3           # weekend
    if str(amount).endswith(".00"):
        score += 7           # round number (common in card testing)

    # add noise
    score += np.random.normal(0, 8)
    score  = max(0.0, min(100.0, score))

    # 5. explicit fraud pattern boosts
    if channel == "Online" and amount < 5 and random.random() < 0.6:
        score = min(100, score + 45)   # card testing

    if currency != "USD" and cat in ["Wire Transfer", "Crypto Exchange"] and random.random() < 0.7:
        score = min(100, score + 50)   # account takeover

    if cat == "Electronics" and amount > 500 and random.random() < 0.5:
        score = min(100, score + 40)   # high-value electronics burst

    score = round(score, 1)

    # ── flag ─────────────────────────────────────────────────────
    if score >= 70:
        flag = "Block"
    elif score >= 45:
        flag = "Review"
    else:
        flag = "Clean"

    rows.append({
        "Transaction_ID":     txn_id,
        "Timestamp":          txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "User_ID":            f"USR{user_id:04d}",
        "Merchant_Name":      merchant_names[m_idx],
        "Merchant_Category":  cat,
        "Merchant_State":     state,
        "Channel":            channel,
        "Amount":             amount,
        "Currency":           currency,
        "Amount_USD":         amount_usd,
        "Hour":               hour,
        "Is_Weekend":         is_weekend,
        "User_Avg_Amount":    round(baseline, 2),
        "Amount_vs_Baseline": amt_ratio,
        "Fraud_Risk_Score":   score,
        "Fraud_Flag":         flag,
    })

df = pd.DataFrame(rows).sort_values("Timestamp").reset_index(drop=True)

# ── output ───────────────────────────────────────────────────────

flagged = df[df["Fraud_Flag"] != "Clean"]

print("=" * 50)
print("FRAUD SCORING MODEL — SUMMARY")
print("=" * 50)
print(f"Total transactions scored : {len(df):,}")
print(f"Clean                     : {(df['Fraud_Flag']=='Clean').sum():,}  ({(df['Fraud_Flag']=='Clean').mean():.1%})")
print(f"Review                    : {(df['Fraud_Flag']=='Review').sum():,}  ({(df['Fraud_Flag']=='Review').mean():.1%})")
print(f"Block                     : {(df['Fraud_Flag']=='Block').sum():,}   ({(df['Fraud_Flag']=='Block').mean():.1%})")
print(f"Total amount at risk      : ${flagged['Amount_USD'].sum():,.0f}")
print(f"Avg risk score — Block    : {df[df['Fraud_Flag']=='Block']['Fraud_Risk_Score'].mean():.1f}")
print(f"Avg risk score — Review   : {df[df['Fraud_Flag']=='Review']['Fraud_Risk_Score'].mean():.1f}")
print(f"Avg risk score — Clean    : {df[df['Fraud_Flag']=='Clean']['Fraud_Risk_Score'].mean():.1f}")
print()
print("Top flagged merchant categories:")
print(flagged["Merchant_Category"].value_counts().head(5).to_string())
print()
print("Top flagged channels:")
print(flagged["Channel"].value_counts().to_string())

out = "fraud_transactions_scored.csv"
df.to_csv(out, index=False)
print(f"\nOutput saved: {out}")
