import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from inference_engine import InferenceResult, recommend_tracks
from knowledge_base import load_knowledge_base


ROOT = Path(__file__).resolve().parents[1]


class InferenceEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        cls.question_ids = [question["id"] for question in cls.knowledge["questions"]]
        cls.unknown_label = cls.knowledge["metadata"]["likert"]["unknown_label"]

    def test_dynamic_canonical_persona_for_each_track(self):
        for track in self.knowledge["tracks"]:
            with self.subTest(track=track["name"]):
                answers = {question_id: 1 for question_id in self.question_ids}
                exclusive_weights = []
                for question_id, weight in track["weights"].items():
                    if weight <= 0:
                        continue
                    strongest_rival = max(
                        (
                            other["weights"].get(question_id, 0)
                            for other in self.knowledge["tracks"]
                            if other["id"] != track["id"]
                        ),
                        default=0,
                    )
                    if weight > strongest_rival:
                        exclusive_weights.append((weight - strongest_rival, question_id))
                if exclusive_weights:
                    strongest_signal = max(difference for difference, _ in exclusive_weights)
                    for difference, question_id in exclusive_weights:
                        if difference == strongest_signal:
                            answers[question_id] = 5
                result = recommend_tracks(answers, knowledge_base=self.knowledge)
                self.assertEqual(result.ranking[0].track_id, track["id"])
                self.assertTrue(result.ranking[0].contributions)

    def test_ranking_is_complete_deterministic_and_exportable(self):
        answers = {question_id: self.unknown_label for question_id in self.question_ids}
        first = recommend_tracks(answers, knowledge_base=self.knowledge)
        second = recommend_tracks(answers, knowledge_base=self.knowledge)
        self.assertIsInstance(first, InferenceResult)
        self.assertEqual(first, second)
        self.assertEqual(len(first.ranking), 10)
        self.assertEqual(len(first.top_three), 3)
        self.assertEqual(len({item.track_id for item in first.top_three}), 3)
        self.assertEqual(first.to_dataframe().shape[0], 10)
        self.assertEqual(first.confidence_level, "Baixa")
        with self.assertRaises(FrozenInstanceError):
            setattr(first, "confidence", 1)

    def test_declared_goal_bonus_is_explicit(self):
        answers = {question_id: 1 for question_id in self.question_ids}
        target = self.knowledge["tracks"][-1]
        result = recommend_tracks(answers, target["id"], self.knowledge)
        target_result = next(item for item in result.ranking if item.track_id == target["id"])
        self.assertGreater(target_result.declared_goal_bonus, 0)
        self.assertEqual(
            target_result.declared_goal_bonus,
            round(
                sum(weight for weight in target["weights"].values() if weight > 0)
                * self.knowledge["metadata"]["declared_goal_bonus"],
                4,
            ),
        )

    def test_rejects_invalid_and_missing_answers(self):
        answers = {question_id: 3 for question_id in self.question_ids}
        for invalid in (0, 6, True, 2.5, None):
            with self.subTest(answer=invalid):
                with self.assertRaises(ValueError):
                    recommend_tracks({**answers, self.question_ids[0]: invalid}, knowledge_base=self.knowledge)
        missing = dict(answers)
        missing.pop(self.question_ids[0])
        with self.assertRaisesRegex(ValueError, "Respostas ausentes"):
            recommend_tracks(missing, knowledge_base=self.knowledge)
        with self.assertRaisesRegex(ValueError, "Pergunta inexistente"):
            recommend_tracks({**answers, "unknown": 3}, knowledge_base=self.knowledge)


if __name__ == "__main__":
    unittest.main()
