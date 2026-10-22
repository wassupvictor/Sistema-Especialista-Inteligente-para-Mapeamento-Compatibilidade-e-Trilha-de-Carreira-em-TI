"""Streamlit interface for the IT career expert system."""

import streamlit as st

from knowledge_engine import (
    ACTIVITIES,
    GOALS,
    MATH_LEVELS,
    TOOLS,
    VALUES,
    recommend_career,
)


st.set_page_config(
    page_title="Consultor de Carreiras em TI",
    page_icon="💻",
    layout="centered",
)

st.title("💻 Consultor Inteligente de Carreiras em TI")
st.write(
    "Responda à entrevista para receber uma recomendação explicada por um "
    "motor de inferência baseado em regras."
)

with st.form("career_interview"):
    math = st.selectbox(
        "1. Como você avalia sua afinidade com matemática e estatística?",
        MATH_LEVELS,
    )
    activity = st.selectbox(
        "2. Qual atividade diária mais combina com você?",
        options=list(ACTIVITIES),
        format_func=lambda key: ACTIVITIES[key],
    )
    tool = st.selectbox(
        "3. Qual linguagem ou ferramenta você conhece melhor?",
        options=list(TOOLS),
        format_func=lambda key: TOOLS[key],
    )
    value = st.selectbox(
        "4. Que tipo de resultado prefere entregar?",
        options=list(VALUES),
        format_func=lambda key: VALUES[key],
    )
    goal = st.selectbox(
        "5. Qual é seu principal objetivo profissional?",
        options=list(GOALS),
        format_func=lambda key: GOALS[key],
    )
    submitted = st.form_submit_button("Descobrir minha trilha")

if submitted:
    try:
        recommendation = recommend_career(
            {
                "math": math,
                "activity": activity,
                "tool": tool,
                "value": value,
                "goal": goal,
            }
        )
    except ValueError as error:
        st.error(f"Não foi possível analisar suas respostas: {error}")
    else:
        st.success(f"Trilha recomendada: **{recommendation.career_name}**")
        st.write(recommendation.description)
        st.subheader("Por que esta trilha?")
        for reason in recommendation.reasons:
            st.markdown(f"- {reason}")
        st.caption(
            f"Pontuação: {recommendation.score}. "
            "A pontuação representa a quantidade e o peso das regras compatíveis; "
            "ela não é uma avaliação de capacidade."
        )