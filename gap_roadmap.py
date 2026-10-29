"""Cálculo puro de lacunas de skills e plano de desenvolvimento."""

from dataclasses import dataclass
from math import ceil
from typing import Any, Mapping

from knowledge_base import load_knowledge_base


@dataclass(frozen=True)
class SkillGap:
    skill_id: str
    name: str
    category: str
    current_level: int
    required_level: int
    gap: int
    priority: str
    priority_label: str
    status: str
    topics: tuple[str, ...]
    technologies: tuple[str, ...]
    estimated_hours: int


@dataclass(frozen=True)
class RoadmapItem:
    skill_id: str
    name: str
    topics: tuple[str, ...]
    technologies: tuple[str, ...]
    estimated_hours: int
    estimated_weeks: int


@dataclass(frozen=True)
class RoadmapPhase:
    title: str
    items: tuple[RoadmapItem, ...]
    estimated_hours: int
    estimated_weeks: int


@dataclass(frozen=True)
class CertificationSuggestion:
    name: str
    issuer: str
    tier: str
    tier_label: str
    min_readiness: float
    timing: str


@dataclass(frozen=True)
class PortfolioProject:
    title: str
    description: str
    stack: tuple[str, ...]
    deliverables: tuple[str, ...]
    exercised_skills: tuple[str, ...]
    difficulty: int
    matched_gaps: int


@dataclass(frozen=True)
class GapRoadmap:
    track_id: str
    track_name: str
    current_level: str | None
    target_level: str
    readiness: float
    meets_junior: bool
    skills: tuple[SkillGap, ...]
    next_level_hints: tuple[str, ...]
    phases: tuple[RoadmapPhase, ...]
    certifications: tuple[CertificationSuggestion, ...]
    projects: tuple[PortfolioProject, ...]
    markdown: str

    def skills_dataframe(self):
        """Exporta as lacunas para apresentação tabular no Streamlit/Pandas."""
        import pandas as pd

        return pd.DataFrame(
            [
                {
                    "skill": item.name,
                    "nível atual": item.current_level,
                    "nível exigido": item.required_level,
                    "gap": item.gap,
                    "prioridade": item.priority_label,
                    "status": item.status,
                }
                for item in self.skills
            ]
        )


def _validate_skill_levels(
    skill_levels: Mapping[str, Any],
    skills: list[dict[str, Any]],
    scale: dict[str, Any],
) -> dict[str, int]:
    if not isinstance(skill_levels, Mapping):
        raise ValueError("A autoavaliação de skills deve ser fornecida em um dicionário.")
    skill_ids = {skill["id"] for skill in skills}
    unknown = set(skill_levels) - skill_ids
    if unknown:
        raise ValueError(f"Skill inexistente: {', '.join(sorted(map(str, unknown)))}.")
    validated = {}
    for skill_id, level in skill_levels.items():
        if (
            isinstance(level, bool)
            or not isinstance(level, int)
            or not scale["min"] <= level <= scale["max"]
        ):
            raise ValueError(
                f"Nível inválido para '{skill_id}': use um inteiro de "
                f"{scale['min']} a {scale['max']}."
            )
        validated[skill_id] = level
    return validated


def _make_markdown(
    track_name: str,
    current_level: str | None,
    target_level: str,
    readiness: float,
    meets_junior: bool,
    phases: tuple[RoadmapPhase, ...],
    certifications: tuple[CertificationSuggestion, ...],
    projects: tuple[PortfolioProject, ...],
    hints: tuple[str, ...],
) -> str:
    lines = [
        f"# Plano de desenvolvimento: {track_name}",
        "",
        f"- Nível informado: {current_level or 'não informado'}",
        f"- Nível-alvo: {target_level}",
        f"- Prontidão estimada: {readiness:.1f}%",
        "",
    ]
    if meets_junior:
        lines.extend(
            [f"Você já atende ao nível {target_level} estimado pela base de skills.", ""]
        )
        lines.extend(f"- Próximo nível: {hint}" for hint in hints)
        lines.append("")
    for phase in phases:
        lines.extend(
            [
                f"## {phase.title}",
                f"Estimativa: {phase.estimated_hours} horas, aproximadamente {phase.estimated_weeks} semanas.",
                "",
            ]
        )
        if not phase.items:
            lines.extend(["Sem lacunas prioritárias nesta fase.", ""])
        for item in phase.items:
            lines.append(
                f"- **{item.name}** — {item.estimated_hours} horas "
                f"(aprox. {item.estimated_weeks} semanas); tecnologias: {', '.join(item.technologies)}."
            )
            lines.append(f"  - Tópicos: {', '.join(item.topics)}.")
        lines.append("")
    lines.extend(["## Certificações", ""])
    if certifications:
        for cert in certifications:
            lines.append(
                f"- {cert.name} ({cert.issuer}; {cert.tier_label}): {cert.timing}."
            )
    else:
        lines.append("Nenhuma certificação desta trilha atende à prontidão atual.")
    lines.extend(["", "## Portfólio GitHub", ""])
    for project in projects:
        lines.append(f"- **{project.title}** — {project.description}")
        lines.append(f"  - Stack: {', '.join(project.stack)}.")
        lines.append(f"  - Entregáveis: {', '.join(project.deliverables)}.")
    lines.extend(
        [
            "",
            "Boas práticas: mantenha README claro, commits pequenos e descritivos, "
            "CI com GitHub Actions e testes automatizados.",
            "",
        ]
    )
    return "\n".join(lines)


def build_gap_roadmap(
    track_id: str,
    skill_levels: Mapping[str, Any],
    hours_per_week: int,
    current_level: str | None = None,
    knowledge_base: dict[str, Any] | None = None,
) -> GapRoadmap:
    """Compara skills atuais com o nível-alvo e monta um plano de desenvolvimento."""
    data = knowledge_base if knowledge_base is not None else load_knowledge_base()
    tracks = {track["id"]: track for track in data["tracks"]}
    if track_id not in tracks:
        raise ValueError(f"Trilha inexistente: '{track_id}'.")
    time_budget = next(
        (field for field in data["profile_questions"] if field.get("role") == "time_budget"),
        None,
    )
    if not isinstance(time_budget, dict):
        raise ValueError("A base não define o campo de horas semanais.")
    minimum_hours = time_budget["min"]
    maximum_hours = time_budget["max"]
    if (
        isinstance(hours_per_week, bool)
        or not isinstance(hours_per_week, int)
        or not minimum_hours <= hours_per_week <= maximum_hours
    ):
        raise ValueError("Informe uma quantidade de horas semanais dentro dos limites da base.")
    track = tracks[track_id]
    skills_by_id = {skill["id"]: skill for skill in data["skills"]}
    levels = _validate_skill_levels(
        skill_levels,
        data["skills"],
        data["metadata"]["skill_level"],
    )
    priority_weights = data["metadata"]["priority_weights"]
    priority_order = {
        priority: order
        for order, priority in enumerate(
            sorted(priority_weights, key=priority_weights.get, reverse=True)
        )
    }
    certification_tier_order = {
        tier: order
        for order, tier in enumerate(data["metadata"]["certification_tier_order"])
    }

    gaps: list[tuple[int, SkillGap]] = []
    weighted_covered = 0.0
    weighted_required = 0.0
    for order, requirement in enumerate(track["junior_requirements"]):
        skill = skills_by_id[requirement["skill"]]
        required = requirement["level"]
        current = levels.get(
            skill["id"], data["metadata"]["skill_level"]["min"]
        )
        priority = requirement["priority"]
        weight = priority_weights[priority]
        weighted_covered += min(current, required) * weight
        weighted_required += required * weight
        gap = max(0, required - current)
        status = "atende" if gap == 0 else "parcial" if current > 0 else "lacuna"
        estimated_hours = ceil(gap * skill["learn"]["est_hours_per_level"])
        gaps.append(
            (
                order,
                SkillGap(
                    skill_id=skill["id"],
                    name=skill["name"],
                    category=skill["category"],
                    current_level=current,
                    required_level=required,
                    gap=gap,
                    priority=priority,
                    priority_label=data["metadata"]["priority_labels"][priority],
                    status=status,
                    topics=tuple(skill["learn"]["topics"]),
                    technologies=tuple(skill["learn"]["technologies"]),
                    estimated_hours=estimated_hours,
                ),
            )
        )
    readiness_ratio = weighted_covered / weighted_required if weighted_required else 1.0
    readiness = round(readiness_ratio * 100, 1)
    meets_junior = readiness_ratio >= data["metadata"]["junior_ready_threshold"]
    ordered_gaps = sorted(
        gaps,
        key=lambda item: (
            priority_order[item[1].priority],
            -item[1].gap,
            item[0],
        ),
    )

    phases = []
    for phase_definition in data["metadata"]["roadmap_phases"]:
        phase_title = phase_definition["title"]
        priority = phase_definition["priority"]
        phase_gaps = [item for _, item in ordered_gaps if item.priority == priority and item.gap]
        roadmap_items = tuple(
            RoadmapItem(
                skill_id=item.skill_id,
                name=item.name,
                topics=item.topics,
                technologies=item.technologies,
                estimated_hours=item.estimated_hours,
                estimated_weeks=ceil(item.estimated_hours / hours_per_week) if item.estimated_hours else 0,
            )
            for item in phase_gaps
        )
        hours = sum(item.estimated_hours for item in roadmap_items)
        phases.append(
            RoadmapPhase(
                title=phase_title,
                items=roadmap_items,
                estimated_hours=hours,
                estimated_weeks=ceil(hours / hours_per_week) if hours else 0,
            )
        )

    certifications_by_id = {cert["id"]: cert for cert in data["certifications"]}
    eligible_certs = [
        (order, certifications_by_id[cert_id])
        for order, cert_id in enumerate(track["certifications"])
        if certifications_by_id[cert_id]["min_readiness"] <= readiness_ratio
    ]
    eligible_certs.sort(
        key=lambda pair: (
            certification_tier_order[pair[1]["tier"]],
            pair[1]["min_readiness"],
            pair[0],
        )
    )
    certifications = tuple(
        CertificationSuggestion(
            name=cert["name"],
            issuer=cert["issuer"],
            tier=cert["tier"],
            tier_label=data["metadata"]["certification_tier_labels"][cert["tier"]],
            min_readiness=cert["min_readiness"],
            timing=(
                "após fechar lacunas essenciais"
                if cert["tier"] != "entry"
                else "após consolidar os fundamentos essenciais"
            ),
        )
        for _, cert in eligible_certs
    )

    projects_by_id = {project["id"]: project for project in data["projects"]}
    projects_in_track = [
        (order, projects_by_id[project_id])
        for order, project_id in enumerate(track["projects"])
    ]
    gap_ids = {item.skill_id for _, item in gaps if item.gap}
    ranked_projects = sorted(
        projects_in_track,
        key=lambda pair: (
            -len(gap_ids.intersection(pair[1]["skills_exercised"])),
            pair[1]["difficulty"],
            pair[0],
        ),
    )[:3]
    ranked_projects.sort(key=lambda pair: (pair[1]["difficulty"], pair[0]))
    projects = tuple(
        PortfolioProject(
            title=project["title"],
            description=project["description"],
            stack=tuple(project["stack"]),
            deliverables=tuple(project["deliverables"]),
            exercised_skills=tuple(project["skills_exercised"]),
            difficulty=project["difficulty"],
            matched_gaps=len(gap_ids.intersection(project["skills_exercised"])),
        )
        for _, project in ranked_projects
    )
    skill_results = tuple(item for _, item in gaps)
    phase_results = tuple(phases)
    hints = tuple(track["next_level_hints"]) if meets_junior else ()
    target_level = data["metadata"]["target_seniority"]
    markdown = _make_markdown(
        track["name"],
        current_level,
        target_level,
        readiness,
        meets_junior,
        phase_results,
        certifications,
        projects,
        hints,
    )
    return GapRoadmap(
        track_id=track_id,
        track_name=track["name"],
        current_level=current_level,
        target_level=target_level,
        readiness=readiness,
        meets_junior=meets_junior,
        skills=skill_results,
        next_level_hints=hints,
        phases=phase_results,
        certifications=certifications,
        projects=projects,
        markdown=markdown,
    )
