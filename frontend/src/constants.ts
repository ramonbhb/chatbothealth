export const DOC_SECTIONS = [
  { key: 'background', label: 'Background' },
  { key: 'research_questions', label: 'Research Questions / Hypotheses' },
  { key: 'objectives', label: 'Objectives' },
  { key: 'data_sources', label: 'Data Sources' },
  { key: 'study_population', label: 'Study Population' },
  { key: 'variables_endpoints', label: 'Variables & Endpoints' },
  { key: 'methods_analysis', label: 'Methods / Analysis Plan' },
  { key: 'expected_artifacts', label: 'Expected Artifacts & Deliverables' },
  { key: 'analysis_application', label: 'Analysis Workflow' },
  { key: 'data_governance_ethics', label: 'Data Governance & Ethics' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'risks_limitations', label: 'Risks & Limitations' },
  { key: 'references', label: 'References' },
];

export const DOC_SECTION_HINTS: Record<string, string> = {
  data_sources: 'What data exists? Sources, tables, linkage, and access.',
  variables_endpoints: 'Which fields matter? Predictors, outcomes, coding, missing data rules.',
  methods_analysis: 'How will analysis run? Models, validation, sensitivity checks.',
  expected_artifacts: 'What must the analysis produce? Tables, figures, models, exports, reports.',
  analysis_application: 'How will the analysis be run? Steps, inputs, parameters, and outputs.',
};

export const PROJECT_COLLECTION_GOALS = [
  'Data — sources, cohort, variables, preparation',
  'Methods — analysis plan, models, validation',
  'Artifacts — tables, figures, models, exports',
  'Workflow — how the analysis will be run',
];

export const DOC_STEPS = ['Import / Start', 'Guided Intake', 'Section Review', 'Quality Gate', 'Export'];

export const DOC_STEP_KEYS = ['basics', 'intake', 'review', 'quality', 'export'] as const;

export const DOC_STEP_LABELS: Record<string, string> = {
  basics: 'Import / Start',
  intake: 'Guided Intake',
  review: 'Section Review',
  quality: 'Quality Gate',
  export: 'Export',
};

export const CLEAN_STEPS = [
  'Select Dataset',
  'Link Project',
  'Explore Data',
  'Planning Discussion',
  'Script Draft',
  'Validation',
  'Export',
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
  'What analysis or predictive model are you preparing data for?',
  'Who should be included or excluded from the cohort?',
  'What filters or data quality rules should be applied?',
  'Which tables need to be joined, and at what level?',
  'What derived variables or transformations are needed?',
  'How should missing values be handled?',
  'What is the final output dataset grain for modeling?',
];

export const CLEAN_STEP_LABELS: Record<string, string> = {
  select_dataset: 'Select Dataset',
  link_project: 'Link Project',
  schema_explore: 'Explore Data',
  discussion: 'Planning Discussion',
  script_draft: 'Script Draft',
  validation: 'Validation',
  export: 'Export',
};
