import unittest
from core.rag_engine import LegalRAGEngine

class TestLegalRAGEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = LegalRAGEngine()

    def test_corpus_loaded(self):
        self.assertGreater(len(self.engine.statutes), 0)

    def test_cheating_retrieval(self):
        query = "Someone cheated me online by offering a fake job"
        results = self.engine.search_statutes(query, top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]
        # Should match BNS 318 or BNS 316
        self.assertIn(top["section"], ["Section 318", "Section 316"])
        self.assertIn("Cheating", top["title"])

    def test_arrest_rights_retrieval(self):
        query = "Can police detain me for more than 24 hours without magistrate?"
        results = self.engine.search_statutes(query, top_k=3)
        self.assertGreater(len(results), 0)
        sections = [r["section"] for r in results]
        # Should match Section 58 BNSS, Article 22, or Section 47
        matched = any("58" in s or "22" in s or "47" in s for s in sections)
        self.assertTrue(matched, f"Expected arrest safeguard sections, got {sections}")

    def test_code_converter_ipc_420(self):
        res = self.engine.convert_code("420")
        self.assertTrue(res["found"])
        self.assertIn("Section 318", res["current_law"])
        self.assertIn("Section 420", res["legacy_law"])

    def test_code_converter_crpc_154(self):
        res = self.engine.convert_code("154")
        self.assertTrue(res["found"])
        self.assertIn("Section 173", res["current_law"])
        self.assertIn("Zero FIR", res["offence_title"])

    def test_answer_generation_structure(self):
        query = "I bought a defective television and seller refused refund"
        resp = self.engine.answer_query(query)
        self.assertIn("answer", resp)
        self.assertIn("citations", resp)
        self.assertGreater(len(resp["citations"]), 0)
        self.assertIn("Consumer Protection Act", resp["citations"][0]["act"])

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from starlette.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_home_page_renders_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI Justice Department Assistant", response.text)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_convert_endpoint(self):
        response = self.client.get("/api/convert?code=420")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["found"])
        self.assertIn("Section 318", data["current_law"])

if __name__ == "__main__":
    unittest.main()

