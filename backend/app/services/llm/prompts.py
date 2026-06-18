PROJECT_DOC_SECTIONS = [
    "background",
    "research_questions",
    "objectives",
    "data_sources",
    "study_population",
    "variables_endpoints",
    "methods_analysis",
    "expected_artifacts",
    "analysis_application",
    "data_governance_ethics",
    "timeline",
    "risks_limitations",
    "references",
]

SECTION_LABELS = {
    "background": "Contexto",
    "research_questions": "Perguntas de Pesquisa / Hipóteses",
    "objectives": "Objetivos",
    "data_sources": "Fontes de Dados",
    "study_population": "População do Estudo",
    "variables_endpoints": "Variáveis e Desfechos",
    "methods_analysis": "Métodos / Plano de Análise",
    "expected_artifacts": "Artefatos e Entregáveis Esperados",
    "analysis_application": "Fluxo de Análise",
    "data_governance_ethics": "Governança de Dados e Ética",
    "timeline": "Cronograma",
    "risks_limitations": "Riscos e Limitações",
    "references": "Referências",
}

COLLECTION_PRIORITIES = [
    "Dados: fontes, coorte, variáveis, desfechos e como os dados serão preparados",
    "Métodos: abordagem estatística/ML, validação e reprodutibilidade",
    "Artefatos: tabelas, gráficos, modelos e outras saídas que a análise deve produzir",
    "Fluxo: como a análise será executada, com quais entradas e saídas",
]

SECTION_GUIDANCE = {
    "background": "Contexto clínico/científico e por que este estudo é relevante.",
    "research_questions": "Perguntas ou hipóteses específicas e testáveis.",
    "objectives": "Objetivos primários e secundários alinhados às perguntas.",
    "data_sources": (
        "Conjuntos de dados, tabelas, vínculos, periodicidade de atualização, acesso e governança."
    ),
    "study_population": "Critérios de inclusão/exclusão, definição da coorte e datas de índice.",
    "variables_endpoints": (
        "Preditoras, desfechos, covariáveis, campos derivados e definições de endpoints. "
        "Seja explícito sobre tipos, codificação e expectativas para dados ausentes."
    ),
    "methods_analysis": (
        "Métodos estatísticos/ML, famílias de modelos, estratégia de validação, análises de sensibilidade "
        "e reprodutibilidade."
    ),
    "expected_artifacts": (
        "Entregáveis concretos que a análise deve produzir: tabelas resumo, gráficos, "
        "modelos ajustados, saídas de pontuação, formatos de exportação (CSV, PDF) e relatórios. "
        "Nomeie cada artefato e qual decisão ele apoia."
    ),
    "analysis_application": (
        "Como a análise será executada na prática: fluxos de trabalho, entradas (parâmetros, filtros, "
        "seletores de coorte), saídas (ligadas aos artefatos esperados), etapas, validação e "
        "tratamento de erros."
    ),
    "data_governance_ethics": "Aprovação ética, privacidade, consentimento e tratamento de dados.",
    "timeline": "Marcos principais e cronograma de entrega.",
    "risks_limitations": "Riscos científicos, de qualidade de dados e operacionais.",
    "references": "Trabalhos anteriores, protocolos e literatura relevante.",
}

DOC_SYSTEM_PROMPT = """Você é um assistente de ciência de dados em saúde ajudando pesquisadores a documentar um projeto.

O pesquisador pode fornecer informações em qualquer ordem ou estilo. Não force uma entrevista rígida.
Ajude-o a descrever o estudo de forma clara e completa.

Priorize coletar:
1. DADOS: fontes, coorte, variáveis, desfechos e necessidades de limpeza/preparação
2. MÉTODOS: plano de análise, modelos, validação e reprodutibilidade
3. ARTEFATOS: tabelas, gráficos, modelos, exportações e outras saídas que a análise deve produzir
4. FLUXO: como a análise será executada, quais entradas são necessárias e quais saídas são esperadas

Não mencione que software ou uma aplicação será construída para o pesquisador. Foque na ciência:
dados, métodos e entregáveis.

Faça perguntas de acompanhamento focadas apenas quando informações chave estiverem faltando.
Nunca invente fontes de dados, variáveis ou aprovações éticas. Mantenha respostas concisas e profissionais.

Sempre responda em português brasileiro. Não use hífens nem travessões nas suas respostas."""

QUALITY_CHECKLIST_ITEMS = [
    "Objetivos e perguntas de pesquisa estão claros",
    "Fontes de dados e acesso estão descritos",
    "População do estudo e variáveis/desfechos principais estão definidos",
    "Métodos/plano de análise estão especificados e são viáveis",
    "Artefatos esperados estão listados (tabelas, gráficos, modelos, exportações)",
    "O fluxo de análise descreve entradas, etapas e saídas",
    "Ética e governança de dados estão abordadas",
    "Riscos e limitações estão reconhecidos",
]

CLEAN_SYSTEM_PROMPT = """Você é um assistente de ciência de dados em saúde ajudando pesquisadores a planejar
a limpeza e preparação de dados para modelagem. Você tem acesso à estrutura do banco de dados e linhas de
amostra (apenas exemplos desidentificados; trate-os como ilustrativos, não exaustivos).

Conduza a conversa em um fluxo prático de negócio:
1. OBJETIVO: Qual análise ou modelo estão construindo? Qual é a população alvo?
2. COORTE: Regras de inclusão/exclusão, intervalos de datas, eventos de índice
3. FILTRAGEM: Filtros em nível de linha, verificações de qualidade, tratamento de duplicatas
4. JUNÇÕES: Quais tabelas vincular e em quais chaves
5. TRANSFORMAÇÕES: Variáveis derivadas, recodificação, agregações e regras para dados ausentes
6. PREPARAÇÃO PARA MODELAGEM: Granularidade final (paciente, encontro etc.), conjunto de features, necessidades de divisão treino/validação

Faça uma ou duas perguntas focadas por vez. Referencie nomes reais de tabelas e colunas do esquema.
Nunca assuma que colunas existem a menos que estejam listadas. Prefira pandas e SQLAlchemy. Não sugira SQL destrutivo.
Cada pipeline de limpeza deve ler das tabelas fonte originais (base zerada), nunca de artefatos de outra versão.
Mantenha a linguagem acessível para pesquisadores, não apenas engenheiros.

Sempre responda em português brasileiro. Não use hífens nem travessões nas suas respostas."""

CLEAN_KICKOFF_PROMPT = """Com base na estrutura do conjunto de dados e nas linhas de amostra fornecidas, abra a
conversa de planejamento de limpeza. Resuma brevemente o que você vê nos dados (tabelas, campos principais,
padrões nas amostras). Em seguida, pergunte sobre o objetivo de modelagem/limpeza e a definição da coorte.
Seja conciso: 3 a 5 frases mais 2 ou 3 perguntas claras. Responda em português brasileiro."""

CLEAN_BUSINESS_TOPICS = [
    "Para qual análise ou modelo preditivo você está preparando os dados?",
    "Quem deve ser incluído ou excluído da coorte?",
    "Quais filtros ou regras de qualidade de dados devem ser aplicados?",
    "Quais tabelas precisam ser unidas e em qual nível (paciente, encontro etc.)?",
    "Quais variáveis derivadas ou transformações são necessárias para modelagem?",
    "Como os valores ausentes devem ser tratados?",
    "Qual é a granularidade final do conjunto de dados e as colunas chave para modelagem?",
]

SCRIPT_TEMPLATE_HEADER = '''"""
Script de limpeza de dados gerado pelo Assistente de Pesquisa em Saúde.
Revise cuidadosamente antes de executar em bancos de dados de produção.
Execute apenas em ambiente aprovado com controles de acesso adequados.
"""

import os
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/db")


def get_engine():
    return create_engine(DATABASE_URL)


'''
