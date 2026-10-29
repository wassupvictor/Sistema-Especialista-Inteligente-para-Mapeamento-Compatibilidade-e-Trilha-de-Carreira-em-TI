"""Imprime no terminal uma tabela com resultados de perfis ambíguos."""

from knowledge_base import load_knowledge_base
from inference_engine import recommend_tracks


def main() -> None:
    knowledge = load_knowledge_base()
    headers = ("Caso", "Top 3", "Empate parcial", "Confiança")
    rows = []
    for case in knowledge.get("demo_edge_cases", []):
        answers = {
            question["id"]: case["default_response"]
            for question in knowledge["questions"]
        }
        answers.update(case["answers"])
        result = recommend_tracks(answers, knowledge_base=knowledge)
        ranking = " | ".join(
            f"{position}. {item.name} — {item.adherence_pct:.1f}%"
            for position, item in enumerate(result.top_three, start=1)
        )
        rows.append(
            (
                case["label"],
                ranking,
                "Sim" if result.partial_tie else "Não",
                result.confidence_level,
            )
        )
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


if __name__ == "__main__":
    main()
