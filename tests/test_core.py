import unittest
from datetime import datetime, timezone
from radar.core import daily_stars, growth, metrics
from radar.store import connect, ranking, upsert

class TestCore(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
        # Sunday Oct 4
        self.week = {"week": 1791072000, "total": 28, "days": [1,2,3,4,5,6,7]}

    def test_daily_mapping(self):
        stars = daily_stars([self.week])
        self.assertEqual(stars["2026-10-04"], 1)
        self.assertEqual(stars["2026-10-09"], 6)

    def test_window_boundaries(self):
        days={"2026-10-09": 9,"2026-10-03": 3,"2026-10-02": 2,"2026-09-09": 1}
        self.assertEqual(growth(days,7,self.now),12)
        self.assertEqual(growth(days,30,self.now),14)

    def test_metrics(self):
        values=metrics([self.week],100,self.now)
        self.assertEqual(values["7d"]["added"],21)
        self.assertEqual(values["1y"]["added"],21)
        self.assertAlmostEqual(values["1y"]["rate"],26.58)

    def test_bad_week_rejected(self):
        with self.assertRaises(ValueError):
            daily_stars([{"week":0,"days":[1,2]}])

    def test_ranking(self):
        db=connect(":memory:")
        for name, val in [("a/a",12),("b/b",21)]:
            item={"full_name":name,"stargazers_count":100,"html_url":"https://github.com/"+name}
            data={k:{"added":val,"rate":10} for k in ["7d","30d","90d","6m","1y"]}
            upsert(db,item,data,"2026-10-09")
        self.assertEqual(ranking(db)[0]["full_name"],"b/b")
        with self.assertRaises(ValueError): ranking(db,"bad")
        db.close()

if __name__ == '__main__': unittest.main()
