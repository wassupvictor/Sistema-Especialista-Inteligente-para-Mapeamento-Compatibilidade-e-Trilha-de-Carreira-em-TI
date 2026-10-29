# 💻 Consultor Inteligente de Carreiras em TI

> ### Descubra trilhas de TI compatíveis com seus interesses e planeje seus próximos passos.

Sistema especialista acadêmico com **inferência ponderada**, **base de conhecimento JSON** e uma interface interativa feita com **Streamlit**.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-aplica%C3%A7%C3%A3o-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-an%C3%A1lise-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-gr%C3%A1ficos-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)

**Navegação:** [Trilhas](#-trilhas-avaliadas) · [Execução](#-como-executar) · [Pontuação](#-como-funciona-a-pontuação) · [Gaps e roadmap](#-análise-de-gaps-e-plano-de-ação) · [Testes](#-testes-e-casos-limite)

---

> **Importante:** a aderência mostra compatibilidade entre as respostas e os critérios modelados. **Não mede capacidade, não prevê desempenho e não garante resultado profissional.**

## 📚 Navegação

- [Trilhas avaliadas](#-trilhas-avaliadas)
- [Como executar](#-como-executar)
- [Arquitetura e base de conhecimento](#-arquitetura-e-base-de-conhecimento)
- [Como funciona a pontuação](#-como-funciona-a-pontuação)
- [Análise de gaps e plano de ação](#-análise-de-gaps-e-plano-de-ação)
- [Testes e casos limite](#-testes-e-casos-limite)
- [Rastreabilidade dos requisitos](#-rastreabilidade-dos-requisitos)
- [Premissas e limitações](#-premissas-e-limitações)

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

## ⚙️ Como executar

### Requisitos

- Python **3.10 ou superior**
- Git
- Dependências listadas em `requirements.txt` (Streamlit, Pandas e Plotly)

### Windows — PowerShell

Abra o PowerShell na pasta do projeto e execute:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run main.py
```

Abra [http://localhost:8501](http://localhost:8501) no navegador. Para encerrar, pressione `Ctrl+C` no terminal.

### macOS ou Linux

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run main.py
```

Abra [http://localhost:8501](http://localhost:8501) no navegador. Para encerrar, pressione `Ctrl+C` no terminal.

## 🧠 Arquitetura e base de conhecimento

```text
.
├── regras_carreiras.json      # Perguntas, pesos, trilhas e plano de ação
├── knowledge_base.py          # Carregamento e validação do JSON
├── inference_engine.py        # Ranking ponderado e explicações
├── gap_roadmap.py             # Gaps, prontidão, roadmap e portfólio
├── main.py                    # Wizard e resultados Streamlit
├── demo_edge_cases.py         # Demonstração dos perfis ambíguos
├── tests/
│   ├── test_knowledge_base.py
│   ├── test_inference_engine.py
│   ├── test_gap_roadmap.py
│   ├── test_edge_cases.py
│   └── test_app_smoke.py
├── requirements.txt
└── README.md
```

`regras_carreiras.json` é a fonte de conhecimento do sistema. Nenhuma pergunta, trilha, peso, certificação ou projeto precisa ser codificado no Python.

| Seção JSON | Conteúdo |
|---|---|
| `metadata` | Versão, escalas e rótulos, bônus, limiares, prioridades e ordem das fases/certificações |
| `dimensions` | Dimensões que alimentam o gráfico radar |
| `profile_questions` | Nível atual, horas disponíveis e nome opcional |
| `questions` | 14 afinidades no Passo 2 e 6 objetivos no Passo 3 |
| `skills` | 32 conhecimentos por categoria, com tópicos, tecnologias e estimativa de horas |
| `tracks` | Dez trilhas, pesos, penalidades, perfil ideal e plano para o nível Júnior |
| `certifications` e `projects` | Catálogos referenciados pelas trilhas |
| `demo_edge_cases` | Perfis ambíguos usados na demonstração e nos testes |

As afinidades usam escala Likert de **1 a 5**; “Não sei” é uma resposta válida. As skills são autoavaliadas de **0** (“Nunca usei”) a **3** (“Avançado”). Perfil pessoal e horas disponíveis dão contexto ao plano, mas não alteram a pontuação das trilhas.

`knowledge_base.load_knowledge_base(path=None)` carrega o arquivo padrão ou um caminho alternativo. O carregador valida IDs, faixas, referências entre perguntas, skills, trilhas, certificações e projetos. Erros de leitura, JSON inválido ou referências inconsistentes geram mensagens em português.

## 📊 Como funciona a pontuação

Cada resposta conhecida é normalizada para uma afinidade entre 0 e 1:

```text
a = (resposta − 1) / 4
```

O motor calcula a pontuação e a aderência de cada trilha:

```text
score = Σ(a × peso positivo)
        − Σ(a × |peso negativo|)
        − Σ(penalidades acionadas)
        + bônus da trilha declarada

aderência (%) = clamp(score / soma dos pesos positivos respondidos, 0, 1) × 100
```

<details>
<summary><strong>Exemplo numérico</strong></summary>

Com pesos positivos **3** e **2**, respostas **5** e **4** geram:

```text
3 × 1 + 2 × 0,75 = 4,5 pontos
```

Uma resposta **5** com peso **−1** subtrai 1 ponto; uma penalidade acionada subtrai mais 1. Sem bônus, o score fica em **2,5**, o denominador é **5** e a aderência é **50%**.

</details>

### Incerteza, confiança e empates

- **“Não sei”** remove a resposta do numerador e do denominador da trilha. Sem respostas positivas conhecidas, a aderência é 0%.
- A **cobertura** é a fração dos pesos positivos do catálogo que recebeu resposta.
- A confiança combina cobertura e a margem entre as duas primeiras posições:

  ```text
  confiança = cobertura × (0,25 + 0,75 × min(margem em pontos percentuais / 20, 1))
  ```

- Os níveis são **Baixa** (`< 0,40`), **Média** (`0,40` a `< 0,70`) e **Alta** (`≥ 0,70`).
- O ranking é ordenado por aderência, quantidade de sinais fortes (afinidade `≥ 0,75` em peso `≥ 2`) e, por fim, pela ordem das trilhas no JSON.
- Diferenças menores que `tie_threshold_pp` entre posições adjacentes do Top 3 são marcadas como **empate parcial**. A explicação compara respostas comuns e perguntas com pesos diferentes.
- Pesos negativos representam conflitos de preferência. Penalidades usam condições estruturadas (`<`, `<=`, `==`, `>=`, `>`), sem `eval` ou `exec`.
- As justificativas apresentam sinais positivos, conflitos, penalidades e eventual trilha desejada, com textos mantidos na base JSON.

O bônus da trilha declarada é **5%** da soma dos pesos positivos respondidos naquela trilha. A porcentagem final é limitada ao intervalo de 0 a 100 e arredondada a uma casa decimal.

## 🧭 Análise de gaps e plano de ação

É possível selecionar qualquer trilha do Top 3 para comparar as skills informadas com o nível-alvo **Júnior**:

```text
gap_skill = max(0, nível_exigido − nível_atual)

prontidão =
  Σ(min(nível_atual, nível_exigido) × peso da prioridade)
  / Σ(nível_exigido × peso da prioridade)
```

Os pesos de prioridade (`essential`, `important`, `desirable`) e os níveis exigidos são configuráveis no JSON. O status de cada skill é **atende**, **parcial** ou **lacuna**. Atingido o limiar de prontidão, a aplicação informa que o nível-alvo já é atendido e mostra sugestões para o próximo nível.

O roadmap organiza as lacunas em três fases:

1. **Fundamentos essenciais**
2. **Consolidação**
3. **Diferenciais + certificação**

As horas são estimadas com `est_hours_per_level`; o prazo é arredondado para cima com base nas horas semanais disponíveis. As certificações são filtradas pela prontidão mínima e ordenadas em **Entrada → Associada → Profissional**. Os projetos de portfólio são escolhidos conforme as lacunas que exercitam, do mais simples ao mais complexo.

> **Certificações:** confirme nomes, códigos, níveis e requisitos atuais nos sites oficiais dos emissores. As estimativas de horas são aproximações educacionais, não recomendações oficiais.

## 🧪 Testes e casos limite

### Windows — PowerShell

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe demo_edge_cases.py
```

### macOS ou Linux

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python demo_edge_cases.py
```

A suíte cobre personas derivadas dos pesos JSON para as dez trilhas, validação da base, ranking e Pandas, bônus, gaps, certificações, perfis neutro/baixo/alto/desconhecido, penalidades, ambiguidade, alteração dinâmica de peso e navegação do wizard com AppTest.

### Resultados dos perfis ambíguos

| Perfil | 1º lugar | 2º lugar | 3º lugar | Empate |
|---|---|---|---|:---:|
| Dados e desenvolvimento web | Front-end/UX — **92,3%** | Ciência de Dados — **87,5%** | Back-end — **81,8%** | Sim |
| Engenharia de Dados e Back-end | Engenharia de Dados — **83,3%** | Back-end — **81,8%** | QA — **72,5%** | Sim |
| DevOps e nuvem | DevOps/SRE — **96,4%** | Cloud Architecture — **95,8%** | Cibersegurança — **90,9%** | Sim |

## ✅ Rastreabilidade dos requisitos

| Req. | Implementação |
|:---:|---|
| R1 | `requirements.txt`, `regras_carreiras.json` e histórico Git |
| R2 | `knowledge_base.load_knowledge_base`; conhecimento em JSON |
| R3 | `inference_engine.recommend_tracks` |
| R4 | `metadata.likert`, `questions` e wizard em `main.py` |
| R5 | `InferenceResult.ranking`, `InferenceResult.top_three` e `to_dataframe()` |
| R6 | `gap_roadmap.build_gap_roadmap` |
| R7 | `gap_roadmap.build_gap_roadmap` e catálogos JSON |
| R8 | Wizard, gráficos, abas e download Markdown em `main.py` |
| R9 | As dez entradas da seção `tracks` |
| R10 | `demo_edge_cases` e `tests/test_edge_cases.py` |
| R11 | `profile_questions`, `metadata.target_seniority` e cálculo dos gaps |
| R12 | Este README e os commits por fase |

## 📝 Premissas e limitações

- Respostas “Não sei” não são inferidas nem contabilizadas no numerador ou denominador.
- Skill não informada equivale ao nível 0 (“Nunca usei”) no cálculo de gaps.
- A autoavaliação de skills determina a prontidão; o nível geral declarado fornece contexto.
- Dimensões não definidas em `ideal_profile` usam referência neutra **0,5** no gráfico radar.
- Horas de aprendizagem são estimativas lineares por nível; semanas são arredondadas para cima e não incluem pausas ou revisão.
- Nome, horas e experiência geral não influenciam o score; a trilha desejada aplica o bônus informado.
- Empates são apresentados. A ordem do JSON é somente o último critério de desempate.
- Certificações, custos, disponibilidade regional, pré-requisitos e nomes comerciais podem mudar. Confirme dados vigentes com os emissores.
- As recomendações são orientação acadêmica e não substituem aconselhamento profissional.

---

---

🎓 **Projeto acadêmico — Ciência da Computação, UNIPAC Barbacena**
