export const DOC_SECTIONS = [
  { key: 'background', label: 'Contexto' },
  { key: 'research_questions', label: 'Perguntas de Pesquisa / Hipóteses' },
  { key: 'objectives', label: 'Objetivos' },
  { key: 'data_sources', label: 'Fontes de Dados' },
  { key: 'study_population', label: 'População do Estudo' },
  { key: 'variables_endpoints', label: 'Variáveis e Desfechos' },
  { key: 'methods_analysis', label: 'Métodos / Plano de Análise' },
  { key: 'expected_artifacts', label: 'Artefatos e Entregáveis Esperados' },
  { key: 'analysis_application', label: 'Fluxo de Análise' },
  { key: 'data_governance_ethics', label: 'Governança de Dados e Ética' },
  { key: 'timeline', label: 'Cronograma' },
  { key: 'risks_limitations', label: 'Riscos e Limitações' },
  { key: 'references', label: 'Referências' },
];

export const DOC_SECTION_HINTS: Record<string, string> = {
  data_sources: 'Quais dados existem? Fontes, tabelas, vínculos e acesso.',
  variables_endpoints: 'Quais campos importam? Preditoras, desfechos, codificação e regras para dados ausentes.',
  methods_analysis: 'Como a análise será executada? Modelos, validação e análises de sensibilidade.',
  expected_artifacts: 'O que a análise deve produzir? Tabelas, gráficos, modelos, exportações e relatórios.',
  analysis_application: 'Como a análise será executada na prática? Etapas, entradas, parâmetros e saídas.',
};

export const PROJECT_COLLECTION_GOALS = [
  'Dados — fontes, coorte, variáveis e preparação',
  'Métodos — plano de análise, modelos e validação',
  'Artefatos — tabelas, gráficos, modelos e exportações',
  'Fluxo — como a análise será executada',
];

export const DOC_STEPS = ['Importar / Início', 'Coleta Guiada', 'Revisão de Seções', 'Controle de Qualidade', 'Exportar'];

export const DOC_STEP_KEYS = ['basics', 'intake', 'review', 'quality', 'export'] as const;

export const DOC_STEP_LABELS: Record<string, string> = {
  basics: 'Importar / Início',
  intake: 'Coleta Guiada',
  review: 'Revisão de Seções',
  quality: 'Controle de Qualidade',
  export: 'Exportar',
};

export const CLEAN_STEPS = [
  'Selecionar Conjunto',
  'Vincular Projeto',
  'Explorar Dados',
  'Discussão de Planejamento',
  'Rascunho do Script',
  'Validação',
  'Exportar',
];

export const CLEAN_STEP_KEYS = [
  'select_dataset',
  'link_project',
  'schema_explore',
  'discussion',
  'script_draft',
  'validation',
  'export',
] as const;

export const CLEAN_BUSINESS_TOPICS = [
  'Para qual análise ou modelo preditivo você está preparando os dados?',
  'Quem deve ser incluído ou excluído da coorte?',
  'Quais filtros ou regras de qualidade de dados devem ser aplicados?',
  'Quais tabelas precisam ser unidas e em qual nível?',
  'Quais variáveis derivadas ou transformações são necessárias?',
  'Como os valores ausentes devem ser tratados?',
  'Qual é a granularidade final do conjunto de dados para modelagem?',
];

export const CLEAN_STEP_LABELS: Record<string, string> = {
  select_dataset: 'Selecionar Conjunto',
  link_project: 'Vincular Projeto',
  schema_explore: 'Explorar Dados',
  discussion: 'Discussão de Planejamento',
  script_draft: 'Rascunho do Script',
  validation: 'Validação',
  export: 'Exportar',
};
