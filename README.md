# 💻 Consultor Inteligente de Carreiras em TI

> Sistema especialista acadêmico que compara afinidades e objetivos profissionais com dez trilhas de TI, explica o ranking e transforma lacunas de conhecimento em um plano de ação.

A aplicação usa um motor próprio de inferência ponderada, uma base de conhecimento JSON validada, Pandas para exportar tabelas e Streamlit para o assistente interativo. O resultado representa **aderência às respostas informadas**: não mede capacidade, não prevê desempenho e não garante resultado profissional.

## ✨ Trilhas avaliadas

| # | Trilha | Foco principal |
|---:|---|---|
| 1 | **Desenvolvimento Back-end** | Servidores, APIs, regras de negócio e bancos de dados |
| 2 | **Desenvolvimento Front-end & UI/UX** | Interfaces web, experiência do usuário e design responsivo |
| 3 | **Ciência de Dados e Machine Learning** | Estatística, análise, previsões e inteligência artificial |
| 4 | **Engenharia de Dados** | Pipelines, arquitetura de dados e processos ETL/ELT |
| 5 | **Cibersegurança** | Proteção de sistemas, redes e análise de vulnerabilidades |
| 6 | **DevOps & SRE** | Automação, CI/CD, contêineres e confiabilidade |
| 7 | **Computação em Nuvem (Cloud Architecture)** | Infraestrutura escalável e arquitetura em nuvem |
| 8 | **Desenvolvimento Mobile** | Aplicativos nativos ou multiplataforma |
| 9 | **Engenharia de Qualidade e Testes (QA)** | Testes automatizados e confiabilidade de software |
| 10 | **Gestão de Produtos (Product Management)** | Estratégia, priorização e conexão entre negócio e tecnologia |

## ⚙️ Requisitos e execução

- Python 3.10 ou superior
- Streamlit, Pandas e Plotly (versões declaradas em `requirements.txt`)
- Git para versionamento; os projetos sugeridos incluem boas práticas de portfólio GitHub

### Windows PowerShell

Na pasta do projeto:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run main.py
```

Abra `http://localhost:8501`. Para encerrar, use `Ctrl+C` no terminal.

### macOS ou Linux

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run main.py
```

Abra `http://localhost:8501`. Para encerrar, use `Ctrl+C`.

## 🧠 Arquitetura e base de conhecimento

```text
.
├── regras_carreiras.json      # Perguntas, dimensões, pesos, trilhas e plano de ação
├── knowledge_base.py          # Leitura e validação das referências do JSON
├── inference_engine.py        # Ranking ponderado, confiança e explicações
├── gap_roadmap.py             # Lacunas, prontidão, roadmap e portfólio
├── main.py                    # Wizard Streamlit
├── demo_edge_cases.py         # Tabela de perfis ambíguos para demonstração
├── tests/
│   ├── test_knowledge_base.py
│   ├── test_inference_engine.py
│   ├── test_gap_roadmap.py
│   ├── test_edge_cases.py
│   └── test_app_smoke.py
├── requirements.txt
└── README.md
```

`regras_carreiras.json` é a fonte de conhecimento do sistema. O schema contém:

- `metadata`: versão, escala Likert e rótulos, escala de skills, limiar de empate, bônus declarado, prontidão Júnior, pesos de prioridade e ordem das fases/certificações.
- `dimensions`: dimensões técnicas e comportamentais que alimentam o gráfico radar.
- `profile_questions`: nível atual, horas disponíveis e nome opcional. Perfil pessoal e horas **não alteram o ranking**.
- `questions`: 14 afinidades no Passo 2 e 6 objetivos no Passo 3, cada uma com dimensão, texto e ajuda. Todas usam Likert de 1 a 5; “Não sei” é válido.
- `skills`: 32 conhecimentos autoavaliados de 0 (“Nunca usei”) a 3 (“Avançado”), organizados por categoria, com tópicos, tecnologias e estimativa de horas por nível.
- `tracks`: exatamente dez trilhas, pesos de -3 a +3, perfil ideal, penalidades declarativas, requisitos para Júnior, sugestões de próximo nível, certificações e projetos.
- `certifications` e `projects`: catálogo com metadados; cada referência é verificada antes do uso.
- `demo_edge_cases`: perfis demonstrativos usados pelo script e pelos testes de ambiguidade.

O carregador `load_knowledge_base(path=None)` permite carregar um arquivo alternativo e verifica IDs únicos, campos, faixas, perguntas e skills referenciadas, penalidades, trilhas, certificações e projetos. Erros de leitura, JSON ou referências inválidas geram mensagens claras em português. Os casos de demonstração são dados extras no JSON, não regras no código.

## 📊 Pontuação, incerteza e desempates

Para cada resposta Likert conhecida, a afinidade é normalizada:

```text
a = (resposta - 1) / 4
```

O motor calcula, para cada trilha:

```text
score = Σ(a × peso positivo)
        − Σ(a × |peso negativo|)
        − Σ(penalidades acionadas)
        + bônus da trilha declarada

aderência (%) = clamp(score / soma dos pesos positivos respondidos, 0, 1) × 100
```

O bônus da trilha declarada é 5% da soma dos pesos positivos respondidos naquela trilha. A porcentagem é limitada ao intervalo de 0 a 100 e arredondada a uma casa. Por exemplo, com pesos positivos 3 e 2, respostas 5 e 4 geram `3×1 + 2×0,75 = 4,5`; uma resposta 5 com peso -1 subtrai 1 e uma penalidade acionada subtrai 1 ponto. Sem bônus, `score = 2,5`, o denominador é 5 e a aderência é **50%**.

“Não sei” remove aquela resposta do numerador **e** do denominador da trilha. Se nenhuma pergunta positiva for respondida, a aderência é 0%. A cobertura é a fração dos pesos positivos do catálogo que recebeu resposta. A confiança combina cobertura e a margem entre as duas primeiras posições:

```text
confiança = cobertura × (0,25 + 0,75 × min(margem_em_pontos_percentuais / 20, 1))
```

Os níveis exibidos são Baixa (< 0,40), Média (de 0,40 até menos de 0,70) e Alta (≥ 0,70). O ranking completo usa aderência decrescente, quantidade de sinais fortes (afinidade ≥ 0,75 em peso ≥ 2) e, por fim, a ordem das trilhas no JSON. O Top 3 é uma fatia desse ranking ordenado.

Penalidades são condições estruturadas (`<`, `<=`, `==`, `>=`, `>`), avaliadas sem `eval` ou `exec`. Quando duas posições adjacentes do Top 3 diferem por menos de `tie_threshold_pp` (5 pontos percentuais), o resultado marca empate parcial e compara respostas comuns e perguntas com pesos mais divergentes. A justificativa mostra contribuições positivas, conflitos, penalidades e eventual trilha declarada; as explicações usam textos da base JSON.

## 🧭 Skill gaps e plano de ação

O resultado permite escolher qualquer trilha do Top 3 para analisar o nível-alvo **Júnior**. O nível de experiência declarado dá contexto, mas a prontidão é calculada a partir das skills autoavaliadas:

```text
gap_skill = max(0, nível_exigido − nível_atual)
prontidão = Σ(min(nível_atual, nível_exigido) × peso_prioridade)
            / Σ(nível_exigido × peso_prioridade)
```

Os pesos de prioridade (essential/important/desirable) e níveis exigidos são configurados no JSON. O status por skill é atende, parcial ou lacuna. A partir do limiar de prontidão, a aplicação informa que o nível-alvo já é atendido e mostra sugestões para o próximo nível.

O roadmap separa lacunas em três fases, ordena por prioridade, tamanho do gap e ordem dos requisitos no JSON, e estima horas a partir de `est_hours_per_level`. O prazo é arredondado para cima conforme as horas semanais informadas. Certificações são filtradas pela prontidão mínima e apresentadas na ordem configurada (Entrada → Associada → Profissional). O portfólio seleciona projetos da trilha que cobrem mais lacunas, do mais simples ao mais complexo, com stack e entregáveis.

**Confirme nomes, códigos, níveis e requisitos atuais das certificações nos sites oficiais** antes de incluí-las no plano de estudos. O sistema é educacional e suas estimativas de horas são aproximações, não recomendações oficiais de certificadoras.

## 🧪 Testes e casos limite

No PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe demo_edge_cases.py
```

No macOS ou Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python demo_edge_cases.py
```

A suíte cobre personas derivadas dos pesos do JSON para as dez trilhas, carregamento e validação da base, ranking e Pandas, bônus, gaps, certificações, perfis neutro/baixo/alto/desconhecido, penalidades, ambiguidade, alteração dinâmica de peso e navegação AppTest do wizard.

Saída resumida dos casos ambíguos:

| Perfil | Ranking Top 3 | Empate parcial |
|---|---|---|
| Dados e desenvolvimento web | Front-end/UX — 92,3%; Ciência de Dados — 87,5%; Back-end — 81,8% | Sim |
| Engenharia de Dados e Back-end | Engenharia de Dados — 83,3%; Back-end — 81,8%; QA — 72,5% | Sim |
| DevOps e nuvem | DevOps/SRE — 96,4%; Cloud Architecture — 95,8%; Cibersegurança — 90,9% | Sim |

## ✅ Rastreabilidade dos requisitos

| Requisito | Implementação |
|---|---|
| R1 — Python, Pandas, JSON, Streamlit e Git | `requirements.txt`, `regras_carreiras.json`, histórico Git |
| R2 — Conhecimento desacoplado do código | `regras_carreiras.json`; `knowledge_base.load_knowledge_base` |
| R3 — Inferência ponderada e penalidades | `inference_engine.recommend_tracks` |
| R4 — Likert e entrada gradual | `metadata.likert`, `questions` e `_render_likert_step` |
| R5 — Ranking Top 3 percentual | `InferenceResult.ranking`, `InferenceResult.top_three` |
| R6 — Skill Gap Analysis | `gap_roadmap.build_gap_roadmap` |
| R7 — Roadmap, certificações e projetos | `gap_roadmap.build_gap_roadmap` e catálogo JSON |
| R8 — Wizard, gráficos, abas e plano | `main.py` |
| R9 — Dez trilhas solicitadas | `tracks` em `regras_carreiras.json` |
| R10 — Ambiguidade e casos limite | `demo_edge_cases` e `tests/test_edge_cases.py` |
| R11 — Nível atual e alvo Júnior | `profile_questions`, `metadata.target_seniority` e gap |
| R12 — Fases e documentação | cinco commits por fase e este README |

## 📝 Premissas e limitações

- Perguntas sem opinião podem ser marcadas como “Não sei”; elas não são inferidas nem preenchidas automaticamente.
- Uma skill não informada equivale a nível 0 (“Nunca usei”) para o cálculo de gaps. Os níveis informados prevalecem sobre a categoria de experiência geral.
- Dimensões ausentes de `ideal_profile` usam referência neutra 0,5 no radar.
- Horas de aprendizagem são estimativas lineares por nível; semanas são arredondadas para cima e não incluem pausas ou revisão.
- A declaração de trilha desejada aplica um bônus limitado de alinhamento, visível na explicação; perfil, nome e horas não influenciam o score.
- Empates são apresentados em vez de ocultados. A ordem do JSON é somente o último critério de desempate.
- Certificações, custos, disponibilidade regional, pré-requisitos e nomes comerciais mudam. Confirme dados vigentes com os emissores oficiais.
- A seleção de trilhas é orientação acadêmica e não substitui aconselhamento profissional nem validação com pessoas que atuam nas áreas.

---

🎓 **Projeto acadêmico** — Consultor Inteligente de Carreiras em TI.
