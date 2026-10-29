"""Carregamento e validação da base de conhecimento JSON."""

import json
from pathlib import Path
from typing import Any, NoReturn


DEFAULT_PATH = Path(__file__).with_name("regras_carreiras.json")
EXPECTED_TRACK_COUNT = 10
PRIORITIES = {"essential", "important", "desirable"}
CERTIFICATION_TIERS = {"entry", "associate", "professional"}
OPERATORS = {"<", "<=", "==", ">=", ">"}


def _fail(message: str) -> NoReturn:
    raise ValueError(f"Base de conhecimento inválida: {message}")


def _unique_ids(items: Any, section: str) -> set[str]:
    if not isinstance(items, list):
        _fail(f"a seção '{section}' deve ser uma lista.")
    ids: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            _fail(f"item {index + 1} da seção '{section}' precisa ter um id textual.")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        _fail(f"há IDs duplicados na seção '{section}'.")
    return set(ids)


def _require_list(data: dict[str, Any], section: str) -> list[dict[str, Any]]:
    value = data.get(section)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        _fail(f"a seção '{section}' deve ser uma lista de objetos.")
    return value


def _validate_condition(
    condition: Any,
    question_ids: set[str],
    context: str,
    likert: dict[str, Any],
) -> None:
    if not isinstance(condition, dict):
        _fail(f"{context}: condição de penalidade inválida.")
    if condition.get("question") not in question_ids:
        _fail(f"{context}: penalidade referencia pergunta inexistente '{condition.get('question')}'.")
    if condition.get("op") not in OPERATORS:
        _fail(f"{context}: operador de penalidade inválido.")
    value = condition.get("value")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not likert["min"] <= value <= likert["max"]
    ):
        _fail(f"{context}: valor da condição deve estar no intervalo da escala.")


def _validate_data(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        _fail("o conteúdo raiz deve ser um objeto JSON.")
    for section in ("metadata", "dimensions", "profile_questions", "questions", "skills", "tracks", "certifications", "projects"):
        if section not in data:
            _fail(f"seção obrigatória ausente: '{section}'.")

    metadata = data["metadata"]
    if (
        not isinstance(metadata, dict)
        or not isinstance(metadata.get("likert"), dict)
        or not isinstance(metadata.get("skill_level"), dict)
        or not isinstance(metadata.get("target_seniority"), str)
        or not metadata.get("target_seniority")
    ):
        _fail("metadados da escala Likert ausentes ou inválidos.")
    likert = metadata["likert"]
    if likert.get("min") != 1 or likert.get("max") != 5:
        _fail("a escala Likert deve ter mínimo 1 e máximo 5.")
    if (
        not isinstance(likert.get("unknown_label"), str)
        or not likert.get("unknown_label")
        or not isinstance(likert.get("labels"), dict)
        or metadata["skill_level"].get("min") != 0
        or metadata["skill_level"].get("max") != 3
        or not isinstance(metadata["skill_level"].get("labels"), dict)
    ):
        _fail("os rótulos da escala Likert ou de skills estão ausentes ou inválidos.")
    priority_weights = metadata.get("priority_weights")
    priority_labels = metadata.get("priority_labels")
    roadmap_phases = metadata.get("roadmap_phases")
    if (
        not isinstance(priority_weights, dict)
        or set(priority_weights) != PRIORITIES
        or not isinstance(priority_labels, dict)
        or set(priority_labels) != PRIORITIES
        or not all(isinstance(label, str) and label for label in priority_labels.values())
        or any(
            isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0
            for weight in priority_weights.values()
        )
        or not isinstance(roadmap_phases, list)
        or len(roadmap_phases) != len(PRIORITIES)
        or not all(
            isinstance(phase, dict)
            and isinstance(phase.get("title"), str)
            and phase.get("priority") in PRIORITIES
            for phase in roadmap_phases
        )
        or {phase["priority"] for phase in roadmap_phases} != PRIORITIES
    ):
        _fail("pesos de prioridade ou fases do roadmap ausentes ou inválidos.")
    tier_order = metadata.get("certification_tier_order")
    tier_labels = metadata.get("certification_tier_labels")
    if (
        not isinstance(tier_order, list)
        or len(tier_order) != len(CERTIFICATION_TIERS)
        or set(tier_order) != CERTIFICATION_TIERS
        or not isinstance(tier_labels, dict)
        or set(tier_labels) != CERTIFICATION_TIERS
        or not all(isinstance(label, str) and label for label in tier_labels.values())
    ):
        _fail("a ordem dos níveis de certificação está ausente ou inválida.")
    for key in ("tie_threshold_pp", "declared_goal_bonus", "junior_ready_threshold"):
        if isinstance(metadata.get(key), bool) or not isinstance(metadata.get(key), (int, float)):
            _fail(f"metadado '{key}' deve ser numérico.")
    if (
        metadata["tie_threshold_pp"] < 0
        or not 0 <= metadata["declared_goal_bonus"] <= 1
        or not 0 <= metadata["junior_ready_threshold"] <= 1
    ):
        _fail("limiares e bônus dos metadados estão fora dos intervalos permitidos.")

    dimension_ids = _unique_ids(data["dimensions"], "dimensions")
    question_ids = _unique_ids(data["questions"], "questions")
    skill_ids = _unique_ids(data["skills"], "skills")
    track_ids = _unique_ids(data["tracks"], "tracks")
    certification_ids = _unique_ids(data["certifications"], "certifications")
    project_ids = _unique_ids(data["projects"], "projects")
    profile_ids = _unique_ids(data["profile_questions"], "profile_questions")

    if len(track_ids) != EXPECTED_TRACK_COUNT:
        _fail(f"devem existir exatamente {EXPECTED_TRACK_COUNT} trilhas; encontradas {len(track_ids)}.")
    for question in data["questions"]:
        dimension = question.get("dimension")
        if dimension is not None and dimension not in dimension_ids:
            _fail(f"pergunta '{question['id']}' referencia dimensão inexistente '{dimension}'.")
        if question.get("step") not in (2, 3):
            _fail(f"pergunta '{question['id']}' deve pertencer ao passo 2 ou 3.")
    if not profile_ids:
        _fail("é necessário definir perguntas de perfil.")
    for field in data["profile_questions"]:
        if not isinstance(field.get("text"), str) or field.get("type") not in {"select", "number", "text"}:
            _fail(f"pergunta de perfil '{field['id']}' precisa de texto e tipo de campo válidos.")
        if field["type"] == "select" and (
            not isinstance(field.get("options"), list) or not field["options"]
        ):
            _fail(f"pergunta de perfil '{field['id']}' precisa de opções.")
        if field["type"] == "number" and (
            isinstance(field.get("min"), bool)
            or isinstance(field.get("max"), bool)
            or not isinstance(field.get("min"), (int, float))
            or not isinstance(field.get("max"), (int, float))
            or field["min"] > field["max"]
        ):
            _fail(f"pergunta de perfil '{field['id']}' tem limites numéricos inválidos.")
    step_two_count = sum(question.get("step") == 2 for question in data["questions"])
    step_three_count = sum(question.get("step") == 3 for question in data["questions"])
    if not 12 <= step_two_count <= 16 or not 5 <= step_three_count <= 8:
        _fail("a base deve ter de 12 a 16 perguntas no passo 2 e de 5 a 8 no passo 3.")
    if not 25 <= len(data["skills"]) <= 35:
        _fail("a base deve conter de 25 a 35 skills autoavaliáveis.")

    for skill in data["skills"]:
        learn = skill.get("learn")
        if (
            not isinstance(learn, dict)
            or not isinstance(learn.get("topics"), list)
            or not learn["topics"]
            or not isinstance(learn.get("technologies"), list)
            or not learn["technologies"]
        ):
            _fail(f"skill '{skill['id']}' precisa definir tópicos e tecnologias para o roadmap.")
        if not isinstance(learn.get("est_hours_per_level"), (int, float)) or learn["est_hours_per_level"] <= 0:
            _fail(f"skill '{skill['id']}' precisa de estimativa positiva de horas por nível.")

    for cert in data["certifications"]:
        if cert.get("tier") not in CERTIFICATION_TIERS:
            _fail(f"certificação '{cert['id']}' tem nível inválido.")
        if (
            isinstance(cert.get("min_readiness"), bool)
            or not isinstance(cert.get("min_readiness"), (int, float))
            or not 0 <= cert["min_readiness"] <= 1
        ):
            _fail(f"certificação '{cert['id']}' tem prontidão mínima inválida.")

    for project in data["projects"]:
        if (
            not isinstance(project.get("stack"), list)
            or not project["stack"]
            or not isinstance(project.get("deliverables"), list)
            or not project["deliverables"]
        ):
            _fail(f"projeto '{project['id']}' precisa definir stack e entregáveis.")
        if not isinstance(project.get("skills_exercised"), list) or not project["skills_exercised"]:
            _fail(f"projeto '{project['id']}' deve exercitar ao menos uma skill.")
        unknown = set(project["skills_exercised"]) - skill_ids
        if unknown:
            _fail(f"projeto '{project['id']}' referencia skills inexistentes: {', '.join(sorted(unknown))}.")

    for track in data["tracks"]:
        track_id = track["id"]
        ideal_profile = track.get("ideal_profile")
        if not isinstance(ideal_profile, dict) or set(ideal_profile) - dimension_ids:
            _fail(f"trilha '{track_id}' tem perfil ideal inválido.")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1
            for value in ideal_profile.values()
        ):
            _fail(f"trilha '{track_id}' tem valor de perfil ideal fora de 0 a 1.")
        weights = track.get("weights")
        if not isinstance(weights, dict) or not weights:
            _fail(f"trilha '{track_id}' precisa definir pesos.")
        for question_id, weight in weights.items():
            if question_id not in question_ids:
                _fail(f"trilha '{track_id}' referencia pergunta inexistente '{question_id}' nos pesos.")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not -3 <= weight <= 3:
                _fail(f"peso de '{question_id}' na trilha '{track_id}' deve estar entre -3 e 3.")
        strong_weights = sum(weight >= 2 for weight in weights.values())
        if not 4 <= strong_weights <= 8:
            _fail(f"trilha '{track_id}' deve ter de 4 a 8 pesos fortemente positivos.")
        penalties = track.get("penalties")
        if not isinstance(penalties, list):
            _fail(f"trilha '{track_id}' precisa definir uma lista de penalidades.")
        _unique_ids(penalties, f"penalties da trilha '{track_id}'")
        for penalty in penalties:
            conditions = penalty.get("when")
            if not isinstance(conditions, list) or not conditions:
                _fail(f"penalidade '{penalty['id']}' precisa ter condições.")
            for condition in conditions:
                _validate_condition(
                    condition,
                    question_ids,
                    f"penalidade '{penalty['id']}'",
                    likert,
                )
            if (
                isinstance(penalty.get("points"), bool)
                or not isinstance(penalty.get("points"), (int, float))
                or penalty["points"] <= 0
            ):
                _fail(f"penalidade '{penalty['id']}' precisa ter pontos positivos.")
        requirements = track.get("junior_requirements")
        if not isinstance(requirements, list) or not 6 <= len(requirements) <= 12:
            _fail(f"trilha '{track_id}' deve ter de 6 a 12 requisitos para Júnior.")
        seen_requirements: set[str] = set()
        for requirement in requirements:
            skill_id = requirement.get("skill")
            if skill_id not in skill_ids:
                _fail(f"trilha '{track_id}' referencia skill inexistente '{skill_id}'.")
            if skill_id in seen_requirements:
                _fail(f"trilha '{track_id}' repete o requisito '{skill_id}'.")
            seen_requirements.add(skill_id)
            if (
                requirement.get("priority") not in PRIORITIES
                or isinstance(requirement.get("level"), bool)
                or not isinstance(requirement.get("level"), int)
                or not 1 <= requirement["level"] <= metadata["skill_level"]["max"]
            ):
                _fail(f"requisito '{skill_id}' da trilha '{track_id}' tem nível ou prioridade inválidos.")
        if not isinstance(track.get("next_level_hints"), list) or not track["next_level_hints"]:
            _fail(f"trilha '{track_id}' não possui sugestões de próximo nível.")
        if not isinstance(track.get("certifications"), list) or not 2 <= len(track["certifications"]) <= 3:
            _fail(f"trilha '{track_id}' deve referenciar de 2 a 3 certificações.")
        if set(track["certifications"]) - certification_ids:
            _fail(f"trilha '{track_id}' referencia certificação inexistente.")
        if not isinstance(track.get("projects"), list) or not 2 <= len(track["projects"]) <= 3:
            _fail(f"trilha '{track_id}' deve referenciar de 2 a 3 projetos.")
        if set(track["projects"]) - project_ids:
            _fail(f"trilha '{track_id}' referencia projeto inexistente.")
    if "demo_edge_cases" in data:
        cases = _require_list(data, "demo_edge_cases")
        _unique_ids(cases, "demo_edge_cases")
        for case in cases:
            if not isinstance(case.get("label"), str) or not isinstance(case.get("answers"), dict):
                _fail(f"caso demonstrativo '{case['id']}' precisa de rótulo e respostas.")
            default_response = case.get("default_response")
            if (
                isinstance(default_response, bool)
                or not isinstance(default_response, int)
                or not likert["min"] <= default_response <= likert["max"]
            ):
                _fail(f"caso demonstrativo '{case['id']}' tem resposta padrão inválida.")
            if set(case["answers"]) - question_ids:
                _fail(f"caso demonstrativo '{case['id']}' referencia pergunta inexistente.")
            if any(
                isinstance(answer, bool)
                or not (
                    answer == likert["unknown_label"]
                    or isinstance(answer, int)
                    and likert["min"] <= answer <= likert["max"]
                )
                for answer in case["answers"].values()
            ):
                _fail(f"caso demonstrativo '{case['id']}' tem resposta inválida.")
            expected_tracks = case.get("expected_tracks")
            if not isinstance(expected_tracks, list) or set(expected_tracks) - track_ids:
                _fail(f"caso demonstrativo '{case['id']}' referencia trilha inexistente.")
    return data


def load_knowledge_base(path: str | Path | None = None) -> dict[str, Any]:
    """Carrega o JSON padrão ou um arquivo alternativo e valida suas referências."""
    source = Path(path) if path is not None else DEFAULT_PATH
    try:
        with source.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as error:
        raise ValueError(f"Base de conhecimento não encontrada: '{source}'.") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido em '{source}', linha {error.lineno}, coluna {error.colno}: {error.msg}.") from error
    except OSError as error:
        raise ValueError(f"Não foi possível ler a base de conhecimento '{source}': {error}.") from error
    return _validate_data(data)
