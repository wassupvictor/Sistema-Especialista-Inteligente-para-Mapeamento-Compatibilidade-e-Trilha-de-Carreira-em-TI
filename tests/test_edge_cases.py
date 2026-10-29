import copy
import json
import tempfile
import unittest
from pathlib import Path

from inference_engine import recommend_tracks
from knowledge_base import load_knowledge_base


ROOT = Path(__file__).resolve().parents[1]


class EdgeCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge = load_knowledge_base(ROOT / "regras_carreiras.json")
        cls.question_ids = [question["id"] for question in cls.knowledge["questions"]]
        cls.unknown_label = cls.knowledge["metadata"]["likert"]["unknown_label"]

    def answers_with(self, default, overrides=None):
        return {
            **{question_id: default for question_id in self.question_ids},
            **(overrides or {}),
        }

    def test_ambiguous_profiles_keep_both_expected_tracks_in_top_three(self):
        for case in self.knowledge["demo_edge_cases"]:
            with self.subTest(case=case["label"]):
                answers = self.answers_with(case["default_response"], case["answers"])
                result = recommend_tracks(answers, knowledge_base=self.knowledge)
                ranked_ids = [item.track_id for item in result.top_three]
                self.assertTrue(set(case["expected_tracks"]).issubset(ranked_ids))
                self.assertEqual(result.partial_tie, case["expected_partial_tie"])
                if case.get("check_joint_explanation"):
                    names = {
                        track["id"]: track["name"]
                        for track in self.knowledge["tracks"]
                    }
                    self.assertTrue(
                        any(
                            all(names[track_id] in explanation for track_id in case["expected_tracks"])
                            for explanation in result.tie_explanations
                        )
                    )

    def test_neutral_low_high_and_unknown_profiles_are_bounded(self):
        profiles = (
            (3, "Baixa"),
            (1, "Baixa"),
            (5, None),
            (self.unknown_label, "Baixa"),
        )
        for answer, confidence in profiles:
            with self.subTest(answer=answer):
                result = recommend_tracks(
                    self.answers_with(answer), knowledge_base=self.knowledge
                )
                self.assertEqual(len(result.ranking), 10)
                self.assertTrue(all(0 <= item.adherence_pct <= 100 for item in result.ranking))
                if confidence is not None:
                    self.assertEqual(result.confidence_level, confidence)

    def test_penalty_reduces_adherence_and_explanation_is_visible(self):
        track = next(item for item in self.knowledge["tracks"] if item["penalties"])
        penalty = track["penalties"][0]
        condition = penalty["when"][0]
        low_value = condition["value"]
        baseline = self.answers_with(3)
        penalized_answers = dict(baseline)
        penalized_answers[condition["question"]] = low_value
        result_at_baseline = recommend_tracks(baseline, knowledge_base=self.knowledge)
        result_with_conflict = recommend_tracks(penalized_answers, knowledge_base=self.knowledge)
        baseline_item = next(item for item in result_at_baseline.ranking if item.track_id == track["id"])
        conflict_item = next(item for item in result_with_conflict.ranking if item.track_id == track["id"])
        self.assertLess(conflict_item.adherence_pct, baseline_item.adherence_pct)
        self.assertIn(penalty["explanation"], conflict_item.penalties)

    def test_changing_only_json_weight_changes_ranking(self):
        changed = False
        for question_id in self.question_ids:
            answers = self.answers_with(self.unknown_label, {question_id: 5})
            original = recommend_tracks(answers, knowledge_base=self.knowledge)
            for track in self.knowledge["tracks"]:
                if track["weights"].get(question_id, 0) > 0:
                    continue
                modified_knowledge = copy.deepcopy(self.knowledge)
                modified_track = next(
                    item
                    for item in modified_knowledge["tracks"]
                    if item["id"] == track["id"]
                )
                modified_track["weights"][question_id] = 3
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "modified.json"
                    path.write_text(
                        json.dumps(modified_knowledge, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    loaded = load_knowledge_base(path)
                altered = recommend_tracks(answers, knowledge_base=loaded)
                if altered.ranking[0].track_id != original.ranking[0].track_id:
                    changed = True
                    break
            if changed:
                break
        self.assertTrue(changed, "alterar um peso carregado do JSON deve alterar o ranking")


if __name__ == "__main__":
    unittest.main()
