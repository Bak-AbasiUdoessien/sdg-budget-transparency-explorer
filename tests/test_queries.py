"""Tests for the SQL queries. Run:  python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import main  # noqa: E402


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.conn = main.connect(":memory:")
        self.conn.executescript((main.ROOT / "sql" / "schema.sql").read_text())
        self.conn.executescript("""
            INSERT INTO states VALUES (1, 'S1', 1000000);
            INSERT INTO sectors VALUES (1, 'Health', 'SDG 3'), (2, 'Education', 'SDG 4');
            INSERT INTO budget_lines VALUES
                (2024, 1, 1, 100, 80, 60),       -- normal
                (2024, 1, 2, 100, 50, 70),       -- spent more than released -> red flag
                (2025, 1, 1, 150, 90, 80),
                (2025, 1, 2, 100, 10, 9);        -- cash not released
        """)
        self.queries = dict(main.split_queries((main.ROOT / "sql" / "queries.sql").read_text()))

    def run_query(self, prefix):
        """Run the query whose title starts with e.g. '3.'."""
        sql = next(q for t, q in self.queries.items() if t.startswith(prefix))   # next() = first match
        return self.conn.execute(sql).fetchall()

    def test_all_queries_run(self):
        self.assertEqual(len(self.queries), 6)
        for sql in self.queries.values():
            self.conn.execute(sql).fetchall()         # must not raise

    def test_execution_rate(self):
        rows = self.run_query("1.")
        health_2024 = [r for r in rows if r[0] == "Health" and r[1] == 2024][0]
        self.assertEqual(health_2024[4], 60.0)       # 60 spent / 100 allocated

    def test_red_flag(self):
        rows = self.run_query("3.")
        self.assertEqual([(r[0], r[2], r[6]) for r in rows], [(2024, "Education", "spent > released")])

    def test_bottleneck(self):
        rows = self.run_query("2.")
        self.assertEqual([(r[1], r[4]) for r in rows], [("Education", "cash not released")])

    def test_yoy_change(self):
        rows = self.run_query("4.")
        self.assertEqual(rows[1][3], 25.0)            # 200 -> 250 allocated = +25%

    def tearDown(self):
        self.conn.close()


if __name__ == "__main__":
    unittest.main()
