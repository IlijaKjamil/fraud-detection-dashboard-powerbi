# NovaPay Fraud Intelligence Dashboard

**Power BI · DAX · Python · Rule-Based Scoring**

A two-page fraud detection dashboard built on a synthetic payment dataset of 5,000 transactions. The project covers everything from scoring engine design to pattern detection and executive-level risk reporting.

## Dashboard Pages

### Page 1 Transaction Monitoring

Overview of flagged activity across the full transaction set.

- **KPI row** - Total transactions, Blocked, Under Review, Clean, Amount at Risk
- **Risk distribution donut** - share of Clean / Review / Block
- **Risk Score Histogram** - 10 score bands (0–100), color-coded by flag status
- **Flagged by Category** - bar chart ranked by fraud volume with Risk Level color legend
- **Flagged by Channel** - table with flag count and flag rate per channel
- **Flagged by State** - horizontal bar chart, top 6 high-risk states

### Page 2 Fraud Pattern Watchlist

Breakdown of three injected fraud patterns with a transaction-level drill table.

- **Pattern 01 Card Testing** - Online transactions under $5, +45 score pts
- **Pattern 02 Account Takeover** - Foreign currency to Wire Transfer / Crypto Exchange, +50 score pts
- **Pattern 03 Electronics Burst** - Electronics purchases above $500, +40 score pts
- **Watchlist table** — Transaction ID, timestamp, user, category, channel, amount, risk score, flag badge, pattern label

## Scoring Engine

Each transaction is scored 0–100 using a rule-based engine built in Python at data generation time and surfaced in Power BI via DAX calculated columns.

| Signal Group | Max Points |
|---|---|
| Merchant Category risk | 18 |
| Channel risk | 12 |
| State risk | 9 |
| Amount vs. baseline ratio | 13 |
| Transaction hour | 9 |
| Foreign currency | 5 |
| Weekend flag | 3 |
| Round amount | 6 |
| Card Testing pattern | +45 |
| Account Takeover pattern | +50 |
| Electronics Burst pattern | +40 |

**Thresholds:** Block >= 75 · Review 40–74 · Clean < 40

**Dataset split:** 85.4% Clean · 10.4% Review · 4.2% Block

## DAX Measures

All measures live in the `_Measures` calculated table, organized by display folder.

| Folder | Measures |
|---|---|
| KPIs | Total Transactions, Blocked Transactions, Review Transactions, Clean Transactions, Amount at Risk, Block Rate % |
| Scoring | High Risk Count, Medium Risk Count, Low Risk Count |
| Fraud Patterns | Card Testing Detected, Account Takeover Detected, Electronics Burst Detected, Total Patterns Detected, Card Testing Amount at Risk, Account Takeover Amount at Risk, Electronics Burst Amount at Risk, Account Takeover Trigger Rate, Electronics Burst Trigger Rate, Avg Risk Score (Flagged) |
| Channel | Flagged by Channel, Flag Rate by Channel |
| Geography | Flagged by State |

## Calculated Columns

Added to `fraud_transactions_scored` table:

| Column | Logic |
|---|---|
| `Fraud_Flag` | Block / Review / Clean based on score thresholds |
| `Risk_Level` | Block / Review / Clean (operational label) |
| `Risk_Level_Label` | High / Medium / Low (display label) |
| `Score_Band` | 10-point buckets: 0–9, 10–19, … 90–100 |
| `Score_Band_Sort` | Integer sort key for correct histogram ordering |
| `Fraud_Pattern` | Card Testing / Account Takeover / Electronics Burst / None |

## Repository Structure

```
fraud-detection-dashboard-powerbi/
├── data/
│   ├── fraud_transactions_scored.csv   # Synthetic dataset, 5,000 rows
│   └── fraud_scoring_model.py          # Python scoring engine
├── theme/
│   └── NovaPay_Fraud_Theme.json        # Power BI dark theme
├── dashboard/
│   └── NovaPay_Fraud_Dashboard.pbix    # Power BI report file
├── exports/
│   └── NovaPay_Fraud_Dashboard.pdf     # PDF export, both pages
└── README.md
```

## Tools Used

- **Power BI Desktop** - report and data model
- **DAX** - measures and calculated columns
- **Python** - synthetic dataset generation and scoring engine

## Dataset

Synthetic data generated for portfolio purposes. 5,000 transactions across 2024, covering 8 merchant categories, 5 channels, and 10 US states. Three fraud patterns were injected at controlled rates to produce a realistic flag distribution.

No real transaction data was used.
