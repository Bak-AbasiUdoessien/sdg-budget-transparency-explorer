-- =====================================================================
-- schema.sql  -  Budget Transparency Explorer (SDG 16: Strong Institutions)
-- Each budget line goes through three stages:
--   allocated (approved in the budget) -> released (cash actually sent) -> spent (actually used)
-- Gaps between those stages are where accountability questions start.
-- =====================================================================

DROP TABLE IF EXISTS budget_lines;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS states;

CREATE TABLE states (
    state_id    INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    population  INTEGER NOT NULL CHECK (population > 0)          -- needed for per-person comparisons
);

CREATE TABLE sectors (
    sector_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,                             -- e.g. 'Health'
    sdg        TEXT NOT NULL                                     -- the SDG the sector mainly serves
);

CREATE TABLE budget_lines (
    year       INTEGER NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    state_id   INTEGER NOT NULL REFERENCES states(state_id),
    sector_id  INTEGER NOT NULL REFERENCES sectors(sector_id),
    allocated  REAL NOT NULL CHECK (allocated >= 0),             -- amounts in millions of naira
    released   REAL NOT NULL CHECK (released >= 0),
    spent      REAL NOT NULL CHECK (spent >= 0),
    PRIMARY KEY (year, state_id, sector_id)                      -- one line per state, sector and year
    -- Note: there is deliberately NO rule "spent <= released". Overspending happens in
    -- real data, and flagging it is one of this project's jobs (see query 3).
);
