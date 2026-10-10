-- =====================================================================
-- queries.sql  -  Each query starts with "-- name: <title>"; main.py runs them in order.
-- Amounts are in millions of naira.
-- =====================================================================

-- name: 1. Budget execution rate by sector and year
-- Execution rate = spent / allocated. Low rates mean approved money never reached people.
SELECT
    s.name                                                 AS sector,
    b.year,
    ROUND(SUM(b.allocated), 1)                             AS allocated,
    ROUND(SUM(b.spent), 1)                                 AS spent,
    ROUND(100.0 * SUM(b.spent) / NULLIF(SUM(b.allocated), 0), 1) AS execution_pct  -- NULLIF avoids dividing by 0
FROM budget_lines b
JOIN sectors s ON s.sector_id = b.sector_id
GROUP BY s.sector_id, b.year
ORDER BY s.name, b.year;

-- name: 2. Where does the money get stuck? (release vs spending gap, latest year)
-- Low release = the treasury didn't send the cash. Low spend-of-release = the agency didn't use it.
SELECT
    st.name                                                         AS state,
    s.name                                                          AS sector,
    ROUND(100.0 * b.released / NULLIF(b.allocated, 0), 0)           AS released_pct,
    ROUND(100.0 * b.spent / NULLIF(b.released, 0), 0)               AS spent_of_released_pct,
    CASE WHEN b.released < 0.6 * b.allocated THEN 'cash not released'
         WHEN b.spent    < 0.6 * b.released  THEN 'released but not spent'
         ELSE 'ok' END                                              AS bottleneck
FROM budget_lines b
JOIN states  st ON st.state_id = b.state_id
JOIN sectors s  ON s.sector_id = b.sector_id
WHERE b.year = (SELECT MAX(year) FROM budget_lines)                 -- subquery: the most recent year
  AND (b.released < 0.6 * b.allocated OR b.spent < 0.6 * b.released)
ORDER BY bottleneck, state, sector;

-- name: 3. Red flags: spent more than released or allocated
SELECT
    b.year, st.name AS state, s.name AS sector,
    b.allocated, b.released, b.spent,
    CASE WHEN b.spent > b.allocated THEN 'spent > allocated'
         ELSE 'spent > released' END                                AS flag
FROM budget_lines b
JOIN states  st ON st.state_id = b.state_id
JOIN sectors s  ON s.sector_id = b.sector_id
WHERE b.spent > b.released OR b.spent > b.allocated
ORDER BY b.year, state;

-- name: 4. Year-on-year change in health + education allocations (LAG)
WITH yearly AS (
    SELECT st.name AS state, b.year, SUM(b.allocated) AS social_alloc
    FROM budget_lines b
    JOIN states  st ON st.state_id = b.state_id
    JOIN sectors s  ON s.sector_id = b.sector_id
    WHERE s.name IN ('Health', 'Education')                         -- SDG 3 and SDG 4 sectors
    GROUP BY st.state_id, b.year
)
SELECT
    state, year, ROUND(social_alloc, 1) AS allocated,
    ROUND(100.0 * (social_alloc - LAG(social_alloc) OVER w)
                / LAG(social_alloc) OVER w, 1)                      AS change_pct
FROM yearly
WINDOW w AS (PARTITION BY state ORDER BY year)                      -- named window, reused twice above
ORDER BY state, year;

-- name: 5. Health and education SPENT per person (latest year)
SELECT
    st.name                                                                   AS state,
    st.population,
    ROUND(1e6 * SUM(CASE WHEN s.name = 'Health'    THEN b.spent END) / st.population, 0) AS health_naira_pp,
    ROUND(1e6 * SUM(CASE WHEN s.name = 'Education' THEN b.spent END) / st.population, 0) AS education_naira_pp
    -- 1e6 converts millions of naira to naira; "pp" = per person
FROM budget_lines b
JOIN states  st ON st.state_id = b.state_id
JOIN sectors s  ON s.sector_id = b.sector_id
WHERE b.year = (SELECT MAX(year) FROM budget_lines)
GROUP BY st.state_id
ORDER BY health_naira_pp;

-- name: 6. Statistical outliers: execution rate far from the sector's norm (z-score)
-- SQLite has no STDDEV function, so we compute it from averages:
--   variance = AVG(x²) - AVG(x)²   and   stddev = sqrt(variance)
-- sqrt() is registered from Python in main.py (not every SQLite build includes it).
WITH rates AS (
    SELECT b.year, st.name AS state, s.name AS sector,
           1.0 * b.spent / NULLIF(b.allocated, 0) AS rate
    FROM budget_lines b
    JOIN states  st ON st.state_id = b.state_id
    JOIN sectors s  ON s.sector_id = b.sector_id
),
stats AS (
    SELECT *,
           AVG(rate)        OVER (PARTITION BY sector) AS mean_rate,      -- the sector's average
           AVG(rate * rate) OVER (PARTITION BY sector) AS mean_sq         -- average of the squares
    FROM rates
)
SELECT year, state, sector,
       ROUND(100 * rate, 1)                                        AS execution_pct,
       ROUND(100 * mean_rate, 1)                                   AS sector_avg_pct,
       ROUND((rate - mean_rate) / sqrt(mean_sq - mean_rate * mean_rate), 2) AS z_score
FROM stats
WHERE ABS((rate - mean_rate) / sqrt(mean_sq - mean_rate * mean_rate)) > 2   -- more than 2 std devs away
ORDER BY ABS(z_score) DESC;
