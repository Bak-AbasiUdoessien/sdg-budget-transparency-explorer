# Budget Transparency Explorer (SDG 16: Strong Institutions)

[![tests](https://github.com/Bak-AbasiUdoessien/sdg-budget-transparency-explorer/actions/workflows/tests.yml/badge.svg)](https://github.com/Bak-AbasiUdoessien/sdg-budget-transparency-explorer/actions/workflows/tests.yml)

A budget only helps people if the money is **released** and then **spent**. This project loads state budget data into SQLite and uses SQL to ask the questions that budget-tracking groups such as BudgIT ask:

| # | Question | SQL techniques |
|---|---|---|
| 1 | What share of each sector's budget was actually spent? | `GROUP BY`, `NULLIF` for safe division |
| 2 | Where does money get stuck: not released, or released but not spent? | Subquery for the latest year, `CASE` |
| 3 | Red flags: spending above what was released or allocated | Multi-condition `WHERE` |
| 4 | Did health and education allocations rise or fall year on year? | `LAG()` with a **named `WINDOW`** |
| 5 | Health and education spending **per person** by state | Conditional aggregation (`SUM(CASE …)`) |
| 6 | Statistical outliers: execution rates more than 2 standard deviations from the sector norm | Window `AVG`, **z-scores**, and a **Python function registered in SQLite** (`sqrt`) |

**SDG targets covered:** 16.5 (reduce corruption), 16.6 (accountable institutions) and 17.1 (domestic resource mobilisation).

## Run it
```bash
python generate_sample_data.py      # SYNTHETIC budgets with 2 planted anomalies
python main.py                      # builds budget.db and runs all 6 queries
python -m unittest discover tests
```
Everything uses the Python standard library. Both planted anomalies are caught: one by query 3 and query 6, the other by query 6.

## Use real data
- **Open Treasury Portal** (opentreasury.gov.ng) publishes daily federal payments.
- **BudgIT** and **GovSpend** have state budget and implementation data.
- State budget implementation reports (quarterly, published by state Ministries of Budget) include the allocated, released and spent figures.

Map them to `data/budget_lines.csv` (`year,state_id,sector_id,allocated,released,spent`, in millions of naira).

## Interpreting results responsibly
A red flag is **a question, not proof of wrongdoing**. Overspending can come from supplementary budgets, and low releases can come from revenue shortfalls. The value of the tool is that it shows *where to ask*.

## ⚠️ Data note
The states are **fictional** (State A–F), and every number is invented.
