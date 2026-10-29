import unittest
from pathlib import Path

from gap_roadmap import build_gap_roadmap
from knowledge_base import load_knowledge_base


ROOT = Path(__file__).resolve().parents[1]


class GapRoadmapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        cls.track = cls.knowledge["tracks"][0]

    def test_empty_profile_has_gaps_and_nonempty_roadmap(self):
        result = build_gap_roadmap(
            self.track["id"], {}, 8, knowledge_base=self.knowledge
        )
        self.assertEqual(result.readiness, 0)
        self.assertFalse(result.meets_junior)
        self.assertTrue(any(phase.items for phase in result.phases))
        self.assertGreaterEqual(len(result.projects), 2)
        self.assertEqual(len(result.skills_dataframe()), len(self.track["junior_requirements"]))

    def test_all_skills_at_maximum_meet_junior(self):
        levels = {skill["id"]: 3 for skill in self.knowledge["skills"]}
        result = build_gap_roadmap(
            self.track["id"], levels, 10, current_level="Estágio", knowledge_base=self.knowledge
        )
        self.assertEqual(result.readiness, 100)
        self.assertTrue(result.meets_junior)
        self.assertTrue(result.next_level_hints)
        self.assertIn("já atende", result.markdown)

    def test_certifications_are_readiness_gated_and_ordered(self):
        levels = {skill["id"]: 3 for skill in self.knowledge["skills"]}
        result = build_gap_roadmap(
            self.track["id"], levels, 10, knowledge_base=self.knowledge
        )
        tier_order = {"entry": 0, "associate": 1, "professional": 2}
        self.assertEqual(
            [tier_order[cert.tier] for cert in result.certifications],
            sorted(tier_order[cert.tier] for cert in result.certifications),
        )

    def test_rejects_invalid_skill_levels_and_budget(self):
        for invalid in (-1, 4, True, 1.5):
            with self.subTest(level=invalid):
                with self.assertRaises(ValueError):
                    build_gap_roadmap(
                        self.track["id"],
                        {self.track["junior_requirements"][0]["skill"]: invalid},
                        5,
                        knowledge_base=self.knowledge,
                    )
        with self.assertRaises(ValueError):
            build_gap_roadmap(self.track["id"], {}, 0, knowledge_base=self.knowledge)
        with self.assertRaises(ValueError):
            build_gap_roadmap(self.track["id"], {"missing": 1}, 5, knowledge_base=self.knowledge)


if __name__ == "__main__":
    unittest.main()
