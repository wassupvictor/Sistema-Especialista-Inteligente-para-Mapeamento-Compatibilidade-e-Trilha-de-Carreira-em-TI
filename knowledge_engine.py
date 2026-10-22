"""Rule-based career recommendation engine."""

from collections import defaultdict
import collections
from collections.abc import Mapping
from dataclasses import dataclass

# Experta 1.9.4 depends on frozendict 1.2, which still imports this legacy alias.
if not hasattr(collections, "Mapping"):
    collections.Mapping = Mapping

from experta import DefFacts, Fact, KnowledgeEngine, Rule


MATH_LEVELS = ("Baixa", "Média", "Alta")

ACTIVITIES = {
    "backend": "Escrever algoritmos, construir APIs e implementar regras de negócio",
    "frontend": "Criar interfaces visuais, responsivas e fáceis de usar",
    "data_science": "Analisar dados e desenvolver modelos preditivos",
    "data_engineering": "Construir pipelines e arquiteturas para movimentar dados",
    "cybersecurity": "Proteger sistemas, redes e investigar vulnerabilidades",
    "devops": "Automatizar deploys e melhorar a confiabilidade dos serviços",
    "cloud": "Planejar e operar infraestrutura escalável em nuvem",
    "mobile": "Desenvolver aplicativos para celulares e tablets",
    "qa": "Testar software e prevenir defeitos antes da entrega",
    "product": "Entender usuários, definir estratégia e priorizar funcionalidades",
}

TOOLS = {
    "python": "Python",
    "javascript": "JavaScript",
    "java_csharp": "Java ou C#",
    "sql": "SQL e ferramentas de banco de dados",
    "linux_networks": "Linux e redes",
    "git_containers": "Git, Docker e contêineres",
    "cloud_platforms": "AWS, Azure ou Google Cloud",
    "flutter": "Flutter ou Dart",
    "testing": "Ferramentas de teste automatizado",
    "product_tools": "Ferramentas ágeis e de produto",
    "beginner": "Nenhuma / estou começando",
}

VALUES = {
    "apis": "Entregar APIs e funcionalidades de negócio",
    "interfaces": "Entregar interfaces intuitivas para usuários",
    "insights": "Gerar previsões, análises e insights",
    "data_platform": "Disponibilizar dados confiáveis para outras equipes",
    "protection": "Manter sistemas e pessoas protegidos",
    "automation": "Entregar software de forma automatizada e estável",
    "scalability": "Manter uma infraestrutura escalável e resiliente",
    "mobile_experience": "Criar boas experiências em dispositivos móveis",
    "quality": "Garantir software confiável e sem defeitos",
    "product_outcomes": "Criar produtos úteis e alinhados ao negócio",
}

GOALS = {
    "backend": "Desenvolver serviços e sistemas back-end",
    "frontend": "Desenvolver interfaces e experiências digitais",
    "data_science": "Trabalhar com ciência de dados ou inteligência artificial",
    "data_engineering": "Trabalhar com engenharia e plataformas de dados",
    "cybersecurity": "Atuar com segurança cibernética",
    "devops": "Atuar com DevOps, SRE ou automação",
    "cloud": "Projetar soluções de computação em nuvem",
    "mobile": "Desenvolver aplicativos mobile",
    "qa": "Atuar com qualidade e testes de software",
    "product": "Liderar produtos digitais e decisões de negócio",
}


CAREERS = {
    "backend": {
        "name": "Desenvolvimento Back-end",
        "description": "Lógica de servidores, APIs, regras de negócio e bancos de dados.",
    },
    "frontend": {
        "name": "Desenvolvimento Front-end & UI/UX",
        "description": "Interfaces web responsivas, experiência do usuário e frameworks reativos.",
    },
    "data_science": {
        "name": "Ciência de Dados e Machine Learning",
        "description": "Estatística, modelagem preditiva, análise de dados e inteligência artificial.",
    },
    "data_engineering": {
        "name": "Engenharia de Dados",
        "description": "Arquitetura de dados, pipelines ETL/ELT e infraestrutura para Data Lakes.",
    },
    "cybersecurity": {
        "name": "Cibersegurança",
        "description": "Defesa cibernética, vulnerabilidades, criptografia e redes seguras.",
    },
    "devops": {
        "name": "DevOps & SRE",
        "description": "Automação, integração e entrega contínua (CI/CD), contêineres e confiabilidade.",
    },
    "cloud": {
        "name": "Computação em Nuvem (Cloud Architecture)",
        "description": "Planejamento, migração e gestão de infraestruturas escaláveis.",
    },
    "mobile": {
        "name": "Desenvolvimento Mobile",
        "description": "Aplicativos nativos ou multiplataforma com tecnologias como Flutter e React Native.",
    },
    "qa": {
        "name": "Engenharia de Qualidade e Testes (QA)",
        "description": "Testes automatizados, confiabilidade de software e processos de qualidade.",
    },
    "product": {
        "name": "Gestão de Produtos (Product Management)",
        "description": "Ponte entre negócio, design e desenvolvimento, com foco em estratégia e priorização.",
    },
}


class UserProfile(Fact):
    """Answers collected during the career interview."""


class Evidence(Fact):
    """A rule's contribution to a career and its human-readable reason."""


@dataclass(frozen=True)
class Recommendation:
    career_id: str
    career_name: str
    description: str
    score: int
    reasons: tuple[str, ...]
    scores: dict[str, int]


class CareerKnowledgeEngine(KnowledgeEngine):
    @DefFacts()
    def _initial_facts(self):
        yield Fact(engine_ready=True)

    def _support(self, career_id, reason, points=2):
        self.declare(Evidence(career=career_id, reason=reason, points=points))

    # Each career is supported by three independent, cross-dimensional rules.
    @Rule(UserProfile(activity="backend", tool="python"))
    def backend_python(self):
        self._support("backend", "Sua preferência por lógica e APIs combina com sua afinidade por Python.")

    @Rule(UserProfile(activity="backend", value="apis"))
    def backend_apis(self):
        self._support("backend", "Você prefere entregar APIs e funcionalidades de negócio.")

    @Rule(UserProfile(goal="backend", tool="java_csharp"))
    def backend_goal(self):
        self._support("backend", "Seu objetivo de desenvolver serviços combina com Java ou C#.")

    @Rule(UserProfile(activity="frontend", tool="javascript"))
    def frontend_javascript(self):
        self._support("frontend", "Sua preferência por interfaces combina com JavaScript.")

    @Rule(UserProfile(activity="frontend", value="interfaces"))
    def frontend_interfaces(self):
        self._support("frontend", "Você valoriza entregar interfaces intuitivas para usuários.")

    @Rule(UserProfile(goal="frontend", tool="javascript"))
    def frontend_goal(self):
        self._support("frontend", "Seu objetivo de trabalhar com experiências digitais reforça esse caminho.")

    @Rule(UserProfile(activity="data_science", math="Alta"))
    def data_science_math(self):
        self._support("data_science", "Sua afinidade alta com matemática favorece estatística e modelagem.")

    @Rule(UserProfile(activity="data_science", value="insights"))
    def data_science_insights(self):
        self._support("data_science", "Você prefere transformar dados em análises, previsões e insights.")

    @Rule(UserProfile(goal="data_science", tool="python"))
    def data_science_goal(self):
        self._support("data_science", "Python e seu objetivo em IA/dados se alinham à trilha.")

    @Rule(UserProfile(activity="data_engineering", tool="sql"))
    def data_engineering_sql(self):
        self._support("data_engineering", "Sua preferência por pipelines combina com SQL e plataformas de dados.")

    @Rule(UserProfile(activity="data_engineering", value="data_platform"))
    def data_engineering_platform(self):
        self._support("data_engineering", "Você prefere disponibilizar dados confiáveis para outras equipes.")

    @Rule(UserProfile(goal="data_engineering", math="Média"))
    def data_engineering_goal(self):
        self._support("data_engineering", "Seu objetivo em engenharia de dados combina com uma afinidade matemática intermediária.")

    @Rule(UserProfile(activity="cybersecurity", tool="linux_networks"))
    def cybersecurity_networks(self):
        self._support("cybersecurity", "Sua preferência por segurança combina com Linux e redes.")

    @Rule(UserProfile(activity="cybersecurity", value="protection"))
    def cybersecurity_protection(self):
        self._support("cybersecurity", "Proteger sistemas é o valor que você prefere entregar.")

    @Rule(UserProfile(goal="cybersecurity", tool="linux_networks"))
    def cybersecurity_goal(self):
        self._support("cybersecurity", "Seu objetivo em segurança e sua afinidade com redes apontam para esta trilha.")

    @Rule(UserProfile(activity="devops", tool="git_containers"))
    def devops_containers(self):
        self._support("devops", "Automação e confiabilidade combinam com Git e contêineres.")

    @Rule(UserProfile(activity="devops", value="automation"))
    def devops_automation(self):
        self._support("devops", "Você prefere entregas automatizadas e serviços estáveis.")

    @Rule(UserProfile(goal="devops", tool="git_containers"))
    def devops_goal(self):
        self._support("devops", "Seu objetivo em DevOps/SRE combina com sua afinidade por contêineres.")

    @Rule(UserProfile(activity="cloud", tool="cloud_platforms"))
    def cloud_platforms(self):
        self._support("cloud", "Sua preferência por infraestrutura combina com plataformas de nuvem.")

    @Rule(UserProfile(activity="cloud", value="scalability"))
    def cloud_scalability(self):
        self._support("cloud", "Você prefere entregar infraestrutura escalável e resiliente.")

    @Rule(UserProfile(goal="cloud", tool="cloud_platforms"))
    def cloud_goal(self):
        self._support("cloud", "Seu objetivo de projetar soluções em nuvem reforça essa recomendação.")

    @Rule(UserProfile(activity="mobile", tool="flutter"))
    def mobile_flutter(self):
        self._support("mobile", "Sua preferência por aplicativos combina com Flutter ou Dart.")

    @Rule(UserProfile(activity="mobile", value="mobile_experience"))
    def mobile_experience(self):
        self._support("mobile", "Você valoriza experiências dedicadas a celulares e tablets.")

    @Rule(UserProfile(goal="mobile", tool="flutter"))
    def mobile_goal(self):
        self._support("mobile", "Seu objetivo mobile e sua afinidade com Flutter/Dart estão alinhados.")

    @Rule(UserProfile(activity="qa", tool="testing"))
    def qa_testing(self):
        self._support("qa", "Sua preferência por qualidade combina com ferramentas de testes automatizados.")

    @Rule(UserProfile(activity="qa", value="quality"))
    def qa_quality(self):
        self._support("qa", "Você prefere garantir software confiável e prevenir defeitos.")

    @Rule(UserProfile(goal="qa", tool="testing"))
    def qa_goal(self):
        self._support("qa", "Seu objetivo em qualidade e testes reforça essa trilha.")

    @Rule(UserProfile(activity="product", tool="product_tools"))
    def product_agile(self):
        self._support("product", "Sua preferência por estratégia combina com ferramentas ágeis e de produto.")

    @Rule(UserProfile(activity="product", value="product_outcomes"))
    def product_value(self):
        self._support("product", "Você prefere criar produtos úteis e alinhados às necessidades do negócio.")

    @Rule(UserProfile(goal="product", math="Baixa"))
    def product_goal(self):
        self._support("product", "Seu objetivo de liderar produtos digitais reforça o perfil de gestão de produto.")

    @Rule(UserProfile(activity="backend"))
    def backend_activity(self):
        self._support("backend", "Sua atividade diária preferida é desenvolver lógica e APIs.", points=1)

    @Rule(UserProfile(activity="frontend"))
    def frontend_activity(self):
        self._support("frontend", "Sua atividade diária preferida é criar interfaces.", points=1)

    @Rule(UserProfile(activity="data_science"))
    def data_science_activity(self):
        self._support("data_science", "Sua atividade diária preferida é analisar dados.", points=1)

    @Rule(UserProfile(activity="data_engineering"))
    def data_engineering_activity(self):
        self._support("data_engineering", "Sua atividade diária preferida é construir pipelines de dados.", points=1)

    @Rule(UserProfile(activity="cybersecurity"))
    def cybersecurity_activity(self):
        self._support("cybersecurity", "Sua atividade diária preferida é proteger sistemas.", points=1)

    @Rule(UserProfile(activity="devops"))
    def devops_activity(self):
        self._support("devops", "Sua atividade diária preferida é automatizar e elevar a confiabilidade.", points=1)

    @Rule(UserProfile(activity="cloud"))
    def cloud_activity(self):
        self._support("cloud", "Sua atividade diária preferida é planejar infraestrutura em nuvem.", points=1)

    @Rule(UserProfile(activity="mobile"))
    def mobile_activity(self):
        self._support("mobile", "Sua atividade diária preferida é desenvolver aplicativos móveis.", points=1)

    @Rule(UserProfile(activity="qa"))
    def qa_activity(self):
        self._support("qa", "Sua atividade diária preferida é testar software.", points=1)

    @Rule(UserProfile(activity="product"))
    def product_activity(self):
        self._support("product", "Sua atividade diária preferida é definir estratégia de produto.", points=1)


def recommend_career(profile):
    """Run the rule engine and return its highest-scoring career."""
    required_fields = {"math", "activity", "tool", "value", "goal"}
    missing_fields = required_fields.difference(profile)
    if missing_fields:
        raise ValueError(f"Respostas ausentes: {', '.join(sorted(missing_fields))}")
    if profile["math"] not in MATH_LEVELS:
        raise ValueError("Afinidade matemática inválida.")
    if profile["activity"] not in ACTIVITIES:
        raise ValueError("Preferência de atuação inválida.")
    if profile["tool"] not in TOOLS:
        raise ValueError("Ferramenta ou linguagem inválida.")
    if profile["value"] not in VALUES:
        raise ValueError("Tipo de entrega de valor inválido.")
    if profile["goal"] not in GOALS:
        raise ValueError("Objetivo profissional inválido.")

    engine = CareerKnowledgeEngine()
    engine.reset()
    engine.declare(UserProfile(**profile))
    engine.run()

    totals = defaultdict(int)
    reasons = defaultdict(list)
    for fact in engine.facts.values():
        if isinstance(fact, Evidence):
            totals[fact["career"]] += fact["points"]
            reasons[fact["career"]].append(fact["reason"])

    winner = max(CAREERS, key=lambda career_id: totals[career_id])
    career = CAREERS[winner]
    return Recommendation(
        career_id=winner,
        career_name=career["name"],
        description=career["description"],
        score=totals[winner],
        reasons=tuple(reasons[winner]),
        scores={career_id: totals[career_id] for career_id in CAREERS},
    )
