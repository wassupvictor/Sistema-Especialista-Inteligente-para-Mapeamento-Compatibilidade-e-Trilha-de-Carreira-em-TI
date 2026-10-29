"""Interface Streamlit em formato de assistente para planejamento de carreira."""

from collections import defaultdict

import plotly.graph_objects as go
import streamlit as st

from gap_roadmap import build_gap_roadmap
from inference_engine import UNKNOWN_ANSWER, recommend_tracks
from knowledge_base import load_knowledge_base


st.set_page_config(
    page_title="Consultor de Carreiras em TI",
    page_icon="💻",
    layout="wide",
)

knowledge = load_knowledge_base()
metadata = knowledge["metadata"]
likert = metadata["likert"]
likert_labels = likert["labels"]
profile_questions = knowledge["profile_questions"]
questions_by_step = {
    step: [question for question in knowledge["questions"] if question["step"] == step]
    for step in (2, 3)
}
tracks_by_id = {track["id"]: track for track in knowledge["tracks"]}
track_names = {track["id"]: track["name"] for track in knowledge["tracks"]}

if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
st.session_state.setdefault("profile_values", {})
st.session_state.setdefault("answers", {})
st.session_state.setdefault("skill_levels", {})

step = st.session_state.wizard_step
st.title("💻 Consultor Inteligente de Carreiras em TI")
st.write(
    "Responda às etapas para conhecer trilhas compatíveis e receber um plano "
    "de desenvolvimento personalizado."
)
if step < 4:
    st.progress(step / 4, text=f"Etapa {step} de 3")


def _advance(target_step: int) -> None:
    st.session_state.wizard_step = target_step
    st.rerun()


def _show_navigation(back_step: int | None, next_label: str, next_step: int) -> None:
    left, right = st.columns(2)
    if back_step is not None and left.button("Voltar", use_container_width=True):
        _advance(back_step)
    if right.button(next_label, type="primary", use_container_width=True):
        _advance(next_step)


def _render_profile_step() -> None:
    st.header("Passo 1 — Perfil pessoal")
    values = {}
    for field in profile_questions:
        key = f"profile_{field['id']}"
        if field["type"] == "select":
            default = st.session_state.profile_values.get(field["id"], field["options"][0])
            st.session_state.setdefault(key, default)
            values[field["id"]] = st.selectbox(field["text"], field["options"], key=key)
        elif field["type"] == "number":
            minimum = field["min"]
            maximum = field["max"]
            default = st.session_state.profile_values.get(field["id"], minimum)
            st.session_state.setdefault(key, default)
            values[field["id"]] = st.number_input(
                field["text"],
                min_value=minimum,
                max_value=maximum,
                step=1,
                key=key,
            )
        elif field["type"] == "text":
            default = st.session_state.profile_values.get(field["id"], "")
            st.session_state.setdefault(key, default)
            values[field["id"]] = st.text_input(field["text"], key=key)
        else:
            st.error(f"Tipo de campo de perfil não reconhecido: {field['type']}.")
    if st.button("Próximo", type="primary", use_container_width=True):
        time_fields = [item for item in profile_questions if item.get("role") == "time_budget"]
        valid = all(
            isinstance(values[field["id"]], int)
            and field["min"] <= values[field["id"]] <= field["max"]
            for field in time_fields
        )
        if not valid:
            st.error("Informe uma quantidade válida de horas disponíveis por semana.")
        else:
            st.session_state.profile_values = values
            _advance(2)


def _render_likert_step(current_step: int) -> None:
    if current_step == 2:
        st.header("Passo 2 — Afinidades técnicas e conhecimentos")
        st.caption("As respostas de afinidade usam escala de 1 a 5; “Não sei” é uma resposta válida.")
    else:
        st.header("Passo 3 — Objetivos de carreira")
        st.caption("Indique suas preferências e trade-offs; você também pode declarar uma trilha desejada.")

    for question in questions_by_step[current_step]:
        state_key = f"answer_{question['id']}"
        default = st.session_state.answers.get(question["id"], UNKNOWN_ANSWER)
        st.session_state.setdefault(state_key, default)
        st.radio(
            question["text"],
            [UNKNOWN_ANSWER, *(str(value) for value in range(likert["min"], likert["max"] + 1))],
            format_func=lambda value: (
                value
                if value == UNKNOWN_ANSWER
                else f"{value} — {likert_labels.get(value, '')}".strip()
            ),
            horizontal=True,
            help=question["help"],
            key=state_key,
        )

    if current_step == 2:
        st.subheader("Autoavaliação de conhecimentos")
        skill_levels = {
            0: "Nunca usei",
            1: "Básico",
            2: "Intermediário",
            3: "Avançado",
        }
        grouped_skills: dict[str, list[dict]] = defaultdict(list)
        for skill in knowledge["skills"]:
            grouped_skills[skill["category"]].append(skill)
        for category, skills in grouped_skills.items():
            with st.expander(category):
                for skill in skills:
                    state_key = f"skill_{skill['id']}"
                    default = st.session_state.skill_levels.get(skill["id"], 0)
                    st.session_state.setdefault(state_key, default)
                    st.radio(
                        skill["name"],
                        options=range(4),
                        format_func=lambda value: f"{value} — {skill_levels[value]}",
                        horizontal=True,
                        key=state_key,
                    )

    if current_step == 3:
        desired_tracks = [None, *(track["id"] for track in knowledge["tracks"])]
        st.session_state.setdefault("declared_goal", st.session_state.get("selected_goal"))
        st.selectbox(
            "Trilha desejada (opcional)",
            desired_tracks,
            format_func=lambda track_id: "Nenhuma preferência declarada"
            if track_id is None
            else track_names[track_id],
            key="declared_goal",
        )

    left, right = st.columns(2)
    if left.button("Voltar", use_container_width=True):
        _advance(current_step - 1)
    next_label = "Próximo" if current_step == 2 else "Ver resultado"
    if right.button(next_label, type="primary", use_container_width=True):
        current_answers = {
            question["id"]: (
                UNKNOWN_ANSWER
                if st.session_state[f"answer_{question['id']}"] == UNKNOWN_ANSWER
                else int(st.session_state[f"answer_{question['id']}"])
            )
            for question in questions_by_step[current_step]
        }
        st.session_state.setdefault("answers", {})
        st.session_state.answers.update(current_answers)
        if current_step == 2:
            st.session_state.skill_levels.update(
                {
                    skill["id"]: st.session_state.get(
                        f"skill_{skill['id']}",
                        st.session_state.skill_levels.get(skill["id"], 0),
                    )
                    for skill in knowledge["skills"]
                }
            )
            _advance(3)
        else:
            if any(answer not in [UNKNOWN_ANSWER, *range(1, 6)] for answer in st.session_state.answers.values()):
                st.error("Revise as respostas antes de continuar.")
            else:
                profile_values = st.session_state.profile_values
                profile_by_role = {
                    field["role"]: profile_values[field["id"]]
                    for field in profile_questions
                    if field["id"] in profile_values and field.get("role")
                }
                skills = {
                    skill["id"]: st.session_state.skill_levels.get(skill["id"], 0)
                    for skill in knowledge["skills"]
                }
                st.session_state.selected_goal = st.session_state.get("declared_goal")
                try:
                    recommendation = recommend_tracks(
                        st.session_state.answers,
                        st.session_state.selected_goal,
                        knowledge,
                    )
                except ValueError as error:
                    st.error(f"Não foi possível analisar suas respostas: {error}")
                else:
                    st.session_state.recommendation = recommendation
                    st.session_state.profile_by_role = profile_by_role
                    st.session_state.skill_levels = skills
                    _advance(4)


def _render_radar(track_id: str, answers: dict) -> None:
    track = tracks_by_id[track_id]
    questions_by_dimension = {
        question["dimension"]: question
        for question in knowledge["questions"]
        if question["dimension"] is not None
    }
    dimensions = knowledge["dimensions"]
    user_values = []
    ideal_values = []
    for dimension in dimensions:
        question = questions_by_dimension.get(dimension["id"])
        response = answers.get(question["id"]) if question is not None else UNKNOWN_ANSWER
        user_values.append(
            None
            if not isinstance(response, int) or isinstance(response, bool)
            else (response - likert["min"]) / (likert["max"] - likert["min"])
        )
        ideal_values.append(track["ideal_profile"].get(dimension["id"], 0.5))
    labels = [dimension["name"] for dimension in dimensions]
    figure = go.Figure()
    figure.add_trace(
        go.Scatterpolar(
            r=user_values + [user_values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name="Seu perfil",
        )
    )
    figure.add_trace(
        go.Scatterpolar(
            r=ideal_values + [ideal_values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name="Perfil de referência",
        )
    )
    figure.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 1]}},
        showlegend=True,
        margin={"l": 35, "r": 35, "t": 35, "b": 35},
    )
    st.plotly_chart(figure, use_container_width=True)


def _render_results() -> None:
    result = st.session_state.recommendation
    profile = st.session_state.profile_by_role
    name = profile.get("display_name", "").strip()
    if name:
        st.subheader(f"Plano de carreira de {name}")
    st.header("Resultado da análise")
    tabs = st.tabs(
        [
            "Ranking",
            "Por que estas trilhas?",
            "Gaps",
            "Roadmap",
            "Portfólio e certificações",
        ]
    )
    with tabs[0]:
        metric_columns = st.columns(3)
        for column, item, position in zip(metric_columns, result.top_three, range(1, 4)):
            column.metric(f"{position}º — {item.name}", f"{item.adherence_pct:.1f}%")
        confidence_col, coverage_col = st.columns(2)
        confidence_col.metric("Confiança", result.confidence_level)
        coverage_col.metric("Perguntas consideradas", f"{result.coverage * 100:.1f}%")
        if result.partial_tie:
            st.warning("Há empate parcial entre posições próximas do Top 3.")
            for explanation in result.tie_explanations:
                st.write(explanation)
        st.subheader("Compatibilidade das dez trilhas")
        ranking_frame = result.to_dataframe().set_index("trilha")
        st.bar_chart(ranking_frame["aderencia_percentual"], y_label="Aderência (%)")
        chart_options = [item.track_id for item in result.top_three]
        chart_track_id = st.selectbox(
            "Trilha para comparar o perfil no gráfico radar",
            chart_options,
            format_func=lambda track_id: track_names[track_id],
            key="radar_track",
        )
        st.subheader("Perfil por dimensão")
        _render_radar(chart_track_id, st.session_state.answers)

    with tabs[1]:
        st.caption(
            "As justificativas descrevem compatibilidade entre respostas e critérios da base; "
            "não representam capacidade profissional."
        )
        for item in result.top_three:
            st.subheader(item.name)
            st.write(item.description)
            if item.contributions:
                st.markdown("**Sinais que aproximam esta trilha:**")
                for explanation in item.contributions:
                    st.markdown(f"- {explanation}")
            if item.conflicts:
                st.markdown("**Preferências que reduzem a aderência:**")
                for explanation in item.conflicts:
                    st.markdown(f"- {explanation}")
            if item.penalties:
                st.markdown("**Conflitos identificados:**")
                for explanation in item.penalties:
                    st.markdown(f"- {explanation}")
            if result.declared_goal_id == item.track_id:
                bonus = metadata["declared_goal_bonus"] * 100
                st.info(
                    f"Trilha desejada declarada por você: bônus de alinhamento de "
                    f"{bonus:.0f}% aplicado aos pesos respondidos."
                )

    top_ids = [item.track_id for item in result.top_three]
    selected_track_id = st.selectbox(
        "Trilha para análise de gaps e plano de ação",
        top_ids,
        format_func=lambda track_id: track_names[track_id],
        key="gap_track",
    )
    gap_plan = build_gap_roadmap(
        selected_track_id,
        st.session_state.skill_levels,
        profile["time_budget"],
        current_level=profile.get("experience"),
        knowledge_base=knowledge,
    )
    with tabs[2]:
        st.subheader(f"Lacunas para {gap_plan.track_name} — alvo Júnior")
        readiness_col, level_col = st.columns(2)
        readiness_col.metric("Prontidão estimada", f"{gap_plan.readiness:.1f}%")
        level_col.metric("Nível-alvo", gap_plan.target_level)
        if gap_plan.meets_junior:
            st.success("Com base nas skills informadas, você já atende ao nível Júnior estimado.")
            for hint in gap_plan.next_level_hints:
                st.markdown(f"- {hint}")
        st.dataframe(gap_plan.skills_dataframe(), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Plano personalizado")
        for phase in gap_plan.phases:
            with st.expander(
                f"{phase.title} — {phase.estimated_hours} horas / "
                f"aproximadamente {phase.estimated_weeks} semanas",
                expanded=bool(phase.items),
            ):
                if not phase.items:
                    st.write("Sem lacunas prioritárias nesta fase.")
                for item in phase.items:
                    st.markdown(f"**{item.name}** — {item.estimated_hours} horas")
                    st.write(f"Tecnologias: {', '.join(item.technologies)}")
                    st.write(f"Tópicos: {', '.join(item.topics)}")
        st.download_button(
            "Baixar plano em Markdown",
            data=gap_plan.markdown,
            file_name=f"plano_{gap_plan.track_id}.md",
            mime="text/markdown",
        )

    with tabs[4]:
        st.subheader("Projetos para o portfólio GitHub")
        for project in gap_plan.projects:
            st.markdown(f"### {project.title}")
            st.write(project.description)
            st.write(f"**Stack:** {', '.join(project.stack)}")
            st.write(f"**Entregáveis:** {', '.join(project.deliverables)}")
        st.subheader("Certificações compatíveis com sua prontidão")
        if gap_plan.certifications:
            for certification in gap_plan.certifications:
                st.markdown(
                    f"- **{certification.name}** — {certification.issuer}; "
                    f"nível {certification.tier}; momento indicado: {certification.timing}."
                )
        else:
            st.info("Nenhuma certificação desta trilha atende à prontidão atual.")
        st.caption(
            "Confirme nomes, códigos e requisitos atuais das certificações nos sites oficiais."
        )

    st.warning(
        "A aderência mede compatibilidade entre suas respostas e os critérios modelados; "
        "não mede capacidade nem garante resultado profissional."
    )
    if st.button("Refazer", type="primary"):
        st.session_state.clear()
        st.rerun()


if step == 1:
    _render_profile_step()
elif step in (2, 3):
    _render_likert_step(step)
else:
    _render_results()
