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
    "background": "Background",
    "research_questions": "Research Questions / Hypotheses",
    "objectives": "Objectives",
    "data_sources": "Data Sources",
    "study_population": "Study Population",
    "variables_endpoints": "Variables & Endpoints",
    "methods_analysis": "Methods / Analysis Plan",
    "expected_artifacts": "Expected Artifacts & Deliverables",
    "analysis_application": "Analysis Workflow",
    "data_governance_ethics": "Data Governance & Ethics",
    "timeline": "Timeline",
    "risks_limitations": "Risks & Limitations",
    "references": "References",
}

# What we must learn from the researcher (flexible how they provide it)
COLLECTION_PRIORITIES = [
    "Data: sources, cohort, variables, endpoints, and how data will be prepared",
    "Methods: statistical/ML approach, validation, and reproducibility",
    "Artifacts: tables, figures, models, and other outputs the analysis must produce",
    "Workflow: how the analysis will be run, with what inputs and outputs",
]

SECTION_GUIDANCE = {
    "background": "Clinical/scientific context and why this study matters.",
    "research_questions": "Specific, testable questions or hypotheses.",
    "objectives": "Primary and secondary objectives aligned with the questions.",
    "data_sources": (
        "Datasets, tables, linkage, refresh cadence, access, and governance."
    ),
    "study_population": "Inclusion/exclusion criteria, cohort definition, and index dates.",
    "variables_endpoints": (
        "Predictors, outcomes, covariates, derived fields, and endpoint definitions. "
        "Be explicit about types, coding, and missing-data expectations."
    ),
    "methods_analysis": (
        "Statistical/ML methods, model families, validation strategy, sensitivity analyses, "
        "and reproducibility."
    ),
    "expected_artifacts": (
        "Concrete deliverables the analysis must produce: summary tables, figures/plots, "
        "fitted models, scoring outputs, export formats (CSV, PDF), and any dashboards or "
        "reports. Name each artifact and what decision it supports."
    ),
    "analysis_application": (
        "How the analysis will be executed in practice: workflows, inputs (parameters, filters, "
        "cohort selectors), outputs (link to expected artifacts), steps, validation, and "
        "error handling."
    ),
    "data_governance_ethics": "Ethics approval, privacy, consent, and data handling.",
    "timeline": "Key milestones and delivery timeline.",
    "risks_limitations": "Scientific, data-quality, and operational risks.",
    "references": "Prior work, protocols, and relevant literature.",
}

DOC_SYSTEM_PROMPT = """You are a health data science assistant helping researchers document a project.

The researcher may provide information in any order or style they prefer — do not force a rigid
interview. Help them describe their study clearly and completely.

Prioritize collecting:
1. DATA — sources, cohort, variables, endpoints, cleaning/preparation needs
2. METHODS — analysis plan, models, validation, reproducibility
3. ARTIFACTS — tables, figures, models, exports, and other outputs the analysis must produce
4. WORKFLOW — how the analysis will be run, what inputs are needed, and what outputs are expected

Do not mention that software or an application will be built for the researcher. Focus on the
science: data, methods, and deliverables.

Ask focused follow-up questions only when key information is missing. Never invent data sources,
variables, or ethics approvals. Keep responses concise and professional."""

QUALITY_CHECKLIST_ITEMS = [
    "Research goals and questions are clear",
    "Data sources and access are described",
    "Study population and key variables/endpoints are defined",
    "Methods/analysis plan is specified and feasible",
    "Expected artifacts are listed (tables, figures, models, exports)",
    "Analysis workflow describes inputs, steps, and outputs",
    "Ethics and data governance are addressed",
    "Risks and limitations are acknowledged",
]

CLEAN_SYSTEM_PROMPT = """You are a health data science assistant helping researchers plan data cleaning
and preparation for modeling. You have access to the database structure and sample rows (de-identified
examples only — treat them as illustrative, not exhaustive).

Guide the conversation in a practical business flow:
1. GOAL — What analysis or model are they building? What is the target population?
2. COHORT — Inclusion/exclusion rules, date ranges, index events
3. FILTERING — Row-level filters, quality checks, duplicate handling
4. JOINS — Which tables to link and on what keys
5. TRANSFORMS — Derived variables, recoding, aggregations, missing data rules
6. MODELING PREP — Final grain (patient, encounter, etc.), feature set, train/validation split needs

Ask one or two focused questions at a time. Reference actual table and column names from the schema.
Never assume columns exist unless listed. Prefer pandas and SQLAlchemy. Do not suggest destructive SQL.
Keep language accessible to researchers, not only engineers."""

CLEAN_KICKOFF_PROMPT = """Based on the dataset structure and sample rows provided, open the cleaning
planning conversation. Briefly summarize what you see in the data (tables, key fields, sample patterns).
Then ask about their modeling/cleaning goal and cohort definition. Keep it concise — 3-5 sentences plus
2-3 clear questions."""

CLEAN_BUSINESS_TOPICS = [
    "What analysis or predictive model are you preparing data for?",
    "Who should be included or excluded from the cohort?",
    "What filters or data quality rules should be applied?",
    "Which tables need to be joined, and at what level (patient, encounter, etc.)?",
    "What derived variables or transformations are needed for modeling?",
    "How should missing values be handled?",
    "What is the final output dataset grain and key columns for modeling?",
]

SCRIPT_TEMPLATE_HEADER = '''"""
Data cleaning script generated by Health Research Assistant.
Review carefully before running against production databases.
Execute only in an approved environment with appropriate access controls.
"""

import os
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/db")


def get_engine():
    return create_engine(DATABASE_URL)


'''
