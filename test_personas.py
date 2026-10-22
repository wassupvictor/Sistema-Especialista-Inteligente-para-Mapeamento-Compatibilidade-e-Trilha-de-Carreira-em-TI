"""Persona-based validation of the career recommendation engine."""

import unittest

from knowledge_engine import recommend_career


PERSONAS = (
    (
        "Analítico",
        {
            "math": "Alta",
            "activity": "data_science",
            "tool": "python",
            "value": "insights",
            "goal": "data_science",
        },
        "data_science",
    ),
    (
        "Infraestrutura e segurança",
        {
            "math": "Média",
            "activity": "cybersecurity",
            "tool": "linux_networks",
            "value": "protection",
            "goal": "cybersecurity",
        },
        "cybersecurity",
    ),
    (
        "Visual e front-end",
        {
            "math": "Baixa",
            "activity": "frontend",
            "tool": "javascript",
            "value": "interfaces",
            "goal": "frontend",
        },
        "frontend",
    ),
    (
        "Negócios e produto",
        {
            "math": "Baixa",
            "activity": "product",
            "tool": "product_tools",
            "value": "product_outcomes",
            "goal": "product",
        },
        "product",
    ),
)


class RecommendationPersonaTests(unittest.TestCase):
    def test_personas_receive_expected_recommendations(self):
        for name, profile, expected in PERSONAS:
            with self.subTest(persona=name):
                recommendation = recommend_career(profile)
                self.assertEqual(recommendation.career_id, expected)
                self.assertTrue(recommendation.reasons)

    def test_each_career_can_be_recommended(self):
        profiles = {
            "backend": ("Média", "backend", "python", "apis", "backend"),
            "frontend": ("Baixa", "frontend", "javascript", "interfaces", "frontend"),
            "data_science": ("Alta", "data_science", "python", "insights", "data_science"),
            "data_engineering": ("Média", "data_engineering", "sql", "data_platform", "data_engineering"),
            "cybersecurity": ("Média", "cybersecurity", "linux_networks", "protection", "cybersecurity"),
            "devops": ("Média", "devops", "git_containers", "automation", "devops"),
            "cloud": ("Média", "cloud", "cloud_platforms", "scalability", "cloud"),
            "mobile": ("Baixa", "mobile", "flutter", "mobile_experience", "mobile"),
            "qa": ("Média", "qa", "testing", "quality", "qa"),
            "product": ("Baixa", "product", "product_tools", "product_outcomes", "product"),
        }
        for expected, answers in profiles.items():
            with self.subTest(career=expected):
                math, activity, tool, value, goal = answers
                recommendation = recommend_career(
                    {
                        "math": math,
                        "activity": activity,
                        "tool": tool,
                        "value": value,
                        "goal": goal,
                    }
                )
                self.assertEqual(recommendation.career_id, expected)

    def test_rejects_invalid_or_missing_answers(self):
        with self.assertRaises(ValueError):
            recommend_career({})
        with self.assertRaises(ValueError):
            recommend_career(
                {
                    "math": "Muito alta",
                    "activity": "backend",
                    "tool": "python",
                    "value": "apis",
                    "goal": "backend",
                }
            )

    def test_incomplete_alignment_still_has_rule_based_explanation(self):
        recommendation = recommend_career(
            {
                "math": "Média",
                "activity": "data_engineering",
                "tool": "beginner",
                "value": "interfaces",
                "goal": "frontend",
            }
        )
        self.assertEqual(recommendation.career_id, "data_engineering")
        self.assertTrue(recommendation.reasons)


if __name__ == "__main__":
    unittest.main()
