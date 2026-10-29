import json
import tempfile
import unittest
from pathlib import Path

from knowledge_base import load_knowledge_base


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeBaseTests(unittest.TestCase):
    def test_loads_complete_base(self):
        knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        self.assertEqual(len(knowledge["tracks"]), 10)
        self.assertGreaterEqual(len(knowledge["skills"]), 25)
        self.assertEqual(len(knowledge["demo_edge_cases"]), 3)

    def test_rejects_broken_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON inválido"):
                load_knowledge_base(path)

    def test_rejects_weight_referencing_missing_question(self):
        knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        knowledge["tracks"][0]["weights"]["missing_question"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(knowledge), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pergunta inexistente"):
                load_knowledge_base(path)

    def test_rejects_missing_track(self):
        knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        knowledge["tracks"].pop()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(knowledge), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exatamente 10 trilhas"):
                load_knowledge_base(path)


if __name__ == "__main__":
    unittest.main()
