import unittest
import app

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.initialize()
    def test_metrics(self):
        r=app.metrics("Atlas","2026-02")
        self.assertEqual((r["total"],r["late"],r["on_time_pct"]),(20,7,65.0))
    def test_version_filters(self):
        feb={d["id"] for d in app.retrieve("Atlas delivery SLA","Atlas","2026-02")}
        jan={d["id"] for d in app.retrieve("Atlas delivery SLA","Atlas","2026-01")}
        self.assertIn("SLA-ATLAS-V2",feb)
        self.assertNotIn("SLA-ATLAS-V1",feb)
        self.assertIn("SLA-ATLAS-V1",jan)
        self.assertNotIn("SLA-ATLAS-V2",jan)
    def test_decline(self):
        r=app.answer("Why did Atlas delivery performance decline in 2026-02?")
        self.assertIn("-25.00 percentage points",r["answer"])
        self.assertTrue(r["citations"])
    def test_clarification(self):
        self.assertEqual(app.answer("Why did performance decline?")["status"],"clarification")
        self.assertEqual(app.answer("Atlas and Cedar performance")["status"],"clarification")
    def test_no_data(self):
        self.assertEqual(app.answer("Atlas delivery performance 2026-03")["status"],"insufficient_evidence")
    def test_invalid_month(self):
        self.assertEqual(app.answer("Atlas delivery 2026-13")["status"],"clarification")
    def test_policy_only(self):
        r=app.answer("Beacon SLA policy 2026-02")
        self.assertEqual(r["metrics"],[])
        self.assertNotIn("SLA-ATLAS-V2",[d["id"] for d in r["citations"]])
    def test_sql_parameters(self):
        self.assertEqual(app.metrics("Atlas' OR 1=1 --","2026-02")["total"],0)

if __name__=="__main__":
    unittest.main()

