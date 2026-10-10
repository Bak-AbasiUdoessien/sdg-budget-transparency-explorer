"""
generate_sample_data.py
SYNTHETIC budgets for 6 fictional states, 6 sectors and 4 years (millions of naira).
A few anomalies are planted on purpose so the queries have something to find. NOT real data.
"""

import csv
import random
from pathlib import Path

DATA = Path(__file__).parent / "data"
random.seed(16)

STATES = [("State A", 4_200_000), ("State B", 6_800_000), ("State C", 3_100_000),
          ("State D", 9_500_000), ("State E", 2_400_000), ("State F", 5_600_000)]
SECTORS = [("Health", "SDG 3"), ("Education", "SDG 4"), ("Agriculture", "SDG 2"),
           ("Water & Sanitation", "SDG 6"), ("Roads", "SDG 9"), ("Administration", "SDG 16")]
YEARS = [2022, 2023, 2024, 2025]


def main():
    DATA.mkdir(exist_ok=True)
    with open(DATA / "states.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state_id", "name", "population"])
        w.writerows((i, n, p) for i, (n, p) in enumerate(STATES, start=1))
    with open(DATA / "sectors.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sector_id", "name", "sdg"])
        w.writerows((i, n, g) for i, (n, g) in enumerate(SECTORS, start=1))

    rows = []
    for sid, (_n, pop) in enumerate(STATES, start=1):
        for secid, (sector, _g) in enumerate(SECTORS, start=1):
            alloc = pop / 1e6 * random.uniform(800, 3000)                    # bigger states get bigger budgets
            if sector == "Administration":
                alloc *= 1.5                                                 # admin often gets the largest share
            for year in YEARS:
                alloc *= random.uniform(0.95, 1.20)                          # yearly change
                release_rate = random.uniform(0.55, 0.95)                    # share of the budget actually released
                spend_rate = random.uniform(0.70, 0.98)                      # share of releases actually spent
                if sector == "Administration":
                    release_rate = min(1.0, release_rate + 0.2)              # admin tends to be paid in full
                released = alloc * release_rate
                spent = released * spend_rate
                rows.append([year, sid, secid, round(alloc, 1), round(released, 1), round(spent, 1)])

    # Planted anomalies (so you can check the queries catch them):
    rows[5][5] = round(rows[5][4] * 1.3, 1)          # one line spends 30% more than was released
    rows[40][4] = round(rows[40][3] * 0.15, 1)       # one line gets only 15% of its budget released...
    rows[40][5] = round(rows[40][4] * 0.9, 1)        # ...so very little is spent
    with open(DATA / "budget_lines.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "state_id", "sector_id", "allocated", "released", "spent"])
        w.writerows(rows)
    print(f"wrote SYNTHETIC data: {len(STATES)} states, {len(SECTORS)} sectors, {len(rows)} budget lines")


if __name__ == "__main__":
    main()
