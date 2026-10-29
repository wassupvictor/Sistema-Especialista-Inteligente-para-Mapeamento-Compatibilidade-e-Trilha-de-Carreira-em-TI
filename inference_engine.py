"""Motor de inferência ponderada e explicável, independente da interface."""

from dataclasses import dataclass
from operator import eq, ge, gt, le, lt
from typing import Any, Mapping

from knowledge_base import load_knowledge_base


_COMPARATORS = {"<": lt, "<=": le, "==": eq, ">=": ge, ">": gt}


@dataclass(frozen=True)
class TrackResult:
    track_id: str
    name: str
    description: str
    score: float
    adherence_pct: float
    contributions: tuple[str, ...]
    penalties: tuple[str, ...]
    conflicts: tuple[str, ...]
    declared_goal_bonus: float


@dataclass(frozen=True)
class InferenceResult:
    ranking: tuple[TrackResult, ...]
    top_three: tuple[TrackResult, ...]
    confidence: float
    confidence_level: str
    coverage: float
    partial_tie: bool
    tie_explanations: tuple[str, ...]
    declared_goal_id: str | None

    def to_dataframe(self):
        """Exporta o ranking integral para um DataFrame Pandas."""
        import pandas as pd

        return pd.DataFrame(
            [
                {
                    "id": item.track_id,
                    "trilha": item.name,
                    "aderencia_percentual": item.adherence_pct,
                    "score": item.score,
                }
                for item in self.ranking
            ]
        )


def _validate_answers(
    answers: Mapping[str, Any],
    questions: list[dict[str, Any]],
    likert: dict[str, Any],
    unknown_label: str,
) -> dict[str, int | str]:
    if not isinstance(answers, Mapping):
        raise ValueError("As respostas devem ser fornecidas em um dicionário.")
    question_ids = {question["id"] for question in questions}
    unknown_ids = set(answers) - question_ids
    if unknown_ids:
        raise ValueError(f"Pergunta inexistente: {', '.join(sorted(map(str, unknown_ids)))}.")
    missing = question_ids - set(answers)
    if missing:
        raise ValueError(
            f"Respostas ausentes (use {likert['min']} a {likert['max']} ou "
            f"'{unknown_label}'): {', '.join(sorted(missing))}."
        )
    validated: dict[str, int | str] = {}
    for question_id, answer in answers.items():
        if answer == unknown_label:
            validated[question_id] = answer
        elif (
            isinstance(answer, int)
            and not isinstance(answer, bool)
            and likert["min"] <= answer <= likert["max"]
        ):
            validated[question_id] = answer
        else:
            raise ValueError(
                f"Resposta inválida para '{question_id}': use um inteiro de "
                f"{likert['min']} a {likert['max']} ou '{unknown_label}'."
            )
    return validated


def _condition_matches(
    condition: dict[str, Any],
    answers: Mapping[str, int | str],
    unknown_label: str,
) -> bool:
    answer = answers[condition["question"]]
    if answer == unknown_label:
        return False
    return _COMPARATORS[condition["op"]](answer, condition["value"])


def _is_strong_signal(answer: int | str, likert: dict[str, Any]) -> bool:
    if not isinstance(answer, int) or isinstance(answer, bool):
        return False
    return (answer - likert["min"]) / (likert["max"] - likert["min"]) >= 0.75


def _explain_tie(
    first: TrackResult,
    second: TrackResult,
    tracks_by_id: Mapping[str, dict[str, Any]],
    questions_by_id: Mapping[str, dict[str, Any]],
    answers: Mapping[str, int | str],
    likert_max: int,
    unknown_label: str,
) -> str:
    first_track = tracks_by_id[first.track_id]
    second_track = tracks_by_id[second.track_id]
    shared = [
        question_id
        for question_id in set(first_track["weights"]) & set(second_track["weights"])
        if first_track["weights"][question_id] > 0
        and second_track["weights"][question_id] > 0
        and answers[question_id] != unknown_label
    ]
    shared.sort(
        key=lambda question_id: (
            min(first_track["weights"][question_id], second_track["weights"][question_id]),
            answers[question_id],
        ),
        reverse=True,
    )
    common_text = ""
    if shared:
        item = questions_by_id[shared[0]]
        common_text = (
            f" As aproxima, por exemplo, '{item['text']}' "
            f"(resposta {answers[shared[0]]}/{likert_max})."
        )

    divergent = sorted(
        set(first_track["weights"]) | set(second_track["weights"]),
        key=lambda question_id: (
            abs(first_track["weights"].get(question_id, 0) - second_track["weights"].get(question_id, 0)),
            question_id,
        ),
        reverse=True,
    )
    distinctions = []
    for question_id in divergent:
        first_weight = first_track["weights"].get(question_id, 0)
        second_weight = second_track["weights"].get(question_id, 0)
        if first_weight == second_weight or answers[question_id] == unknown_label:
            continue
        question = questions_by_id[question_id]
        distinctions.append(
            f"'{question['text']}' ({answers[question_id]}/{likert_max}; "
            f"pesos {first_weight:g} e {second_weight:g})"
        )
        if len(distinctions) == 2:
            break
    distinction_text = (
        " As respostas que mais as distinguem são " + " e ".join(distinctions) + "."
        if distinctions
        else " Não houve resposta conhecida em perguntas com pesos diferentes; suas evidências disponíveis são semelhantes."
    )
    return (
        f"{first.name} e {second.name} têm aderência próxima."
        f"{common_text}{distinction_text}"
    )


def recommend_tracks(
    answers: Mapping[str, Any],
    declared_goal: str | None = None,
    knowledge_base: dict[str, Any] | None = None,
) -> InferenceResult:
    """Calcula o ranking completo, desempates, confiança e explicações."""
    data = knowledge_base if knowledge_base is not None else load_knowledge_base()
    if not isinstance(data, dict) or "questions" not in data or "tracks" not in data:
        raise ValueError("Base de conhecimento inválida para o motor de inferência.")
    likert = data["metadata"]["likert"]
    unknown_label = likert["unknown_label"]
    validated = _validate_answers(
        answers,
        data["questions"],
        likert,
        unknown_label,
    )
    tracks = data["tracks"]
    tracks_by_id = {track["id"]: track for track in tracks}
    questions_by_id = {question["id"]: question for question in data["questions"]}
    if declared_goal not in (None, "") and declared_goal not in tracks_by_id:
        raise ValueError(f"Trilha desejada inexistente: '{declared_goal}'.")
    declared_goal = declared_goal or None

    total_positive_weight = sum(
        weight
        for track in tracks
        for weight in track["weights"].values()
        if weight > 0
    )
    answered_positive_weight = sum(
        weight
        for track in tracks
        for question_id, weight in track["weights"].items()
        if weight > 0 and validated[question_id] != unknown_label
    )
    coverage = answered_positive_weight / total_positive_weight if total_positive_weight else 0.0
    scored: list[tuple[int, TrackResult, int]] = []
    for order, track in enumerate(tracks):
        available_denominator = sum(
            weight
            for question_id, weight in track["weights"].items()
            if weight > 0 and validated[question_id] != unknown_label
        )
        raw_score = 0.0
        contributions: list[tuple[float, str]] = []
        conflicts: list[str] = []
        for question_id, weight in track["weights"].items():
            answer = validated[question_id]
            if answer == unknown_label:
                continue
            if not isinstance(answer, int):
                raise ValueError(f"Resposta inválida para '{question_id}'.")
            affinity = (answer - likert["min"]) / (likert["max"] - likert["min"])
            question = questions_by_id[question_id]
            if weight > 0:
                contribution = affinity * weight
                raw_score += contribution
                if contribution > 0:
                    contributions.append(
                        (
                            contribution,
                            f"{question['text']}: sua resposta {answer}/{likert['max']} contribui positivamente para esta trilha.",
                        )
                    )
            elif affinity > 0:
                raw_score -= affinity * abs(weight)
                conflicts.append(
                    f"{question['text']}: esta preferência conflita parcialmente com o perfil desta trilha."
                )
        fired_penalties = []
        for penalty in track["penalties"]:
            if all(
                _condition_matches(condition, validated, unknown_label)
                for condition in penalty["when"]
            ):
                raw_score -= penalty["points"]
                fired_penalties.append(penalty["explanation"])
        bonus = (
            available_denominator * data["metadata"]["declared_goal_bonus"]
            if declared_goal == track["id"] and available_denominator
            else 0.0
        )
        raw_score += bonus
        adherence = (
            min(100.0, max(0.0, raw_score / available_denominator * 100))
            if available_denominator
            else 0.0
        )
        signal_count = sum(
            1
            for question_id, weight in track["weights"].items()
            if weight >= 2
            and _is_strong_signal(validated[question_id], likert)
        )
        result = TrackResult(
            track_id=track["id"],
            name=track["name"],
            description=track["description"],
            score=round(raw_score, 4),
            adherence_pct=round(adherence, 1),
            contributions=tuple(text for _, text in sorted(contributions, reverse=True)[:3]),
            penalties=tuple(fired_penalties),
            conflicts=tuple(conflicts),
            declared_goal_bonus=round(bonus, 4),
        )
        scored.append((order, result, signal_count))

    scored.sort(key=lambda item: (-item[1].adherence_pct, -item[2], item[0]))
    ranking = tuple(item[1] for item in scored)
    top_three = ranking[:3]
    margin = max(0.0, top_three[0].adherence_pct - top_three[1].adherence_pct)
    confidence = coverage * (0.25 + 0.75 * min(margin / 20.0, 1.0))
    confidence = round(confidence, 3)
    confidence_level = "Alta" if confidence >= 0.7 else "Média" if confidence >= 0.4 else "Baixa"
    threshold = data["metadata"]["tie_threshold_pp"]
    tie_explanations = tuple(
        _explain_tie(
            first,
            second,
            tracks_by_id,
            questions_by_id,
            validated,
            likert["max"],
            unknown_label,
        )
        for first, second in zip(top_three, top_three[1:])
        if first.adherence_pct - second.adherence_pct < threshold
    )
    return InferenceResult(
        ranking=ranking,
        top_three=top_three,
        confidence=confidence,
        confidence_level=confidence_level,
        coverage=round(coverage, 3),
        partial_tie=bool(tie_explanations),
        tie_explanations=tie_explanations,
        declared_goal_id=declared_goal,
    )
