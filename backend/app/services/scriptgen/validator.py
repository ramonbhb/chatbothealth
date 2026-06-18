import ast
import re


FORBIDDEN_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\b",
    r"\bALTER\s+TABLE\b",
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
]


def validate_script(source: str) -> dict:
    issues: list[str] = []
    syntax_ok = True
    lint_ok = True
    safety_ok = True

    if not source.strip():
        return {
            "valid": False,
            "syntax_ok": False,
            "lint_ok": False,
            "safety_ok": False,
            "issues": ["O script está vazio"],
        }

    try:
        ast.parse(source)
    except SyntaxError as exc:
        syntax_ok = False
        issues.append(f"Erro de sintaxe: {exc.msg} (linha {exc.lineno})")

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, source, re.IGNORECASE):
            safety_ok = False
            issues.append(f"Padrão proibido detectado: {pattern}")

    if "DATABASE_URL" not in source and "create_engine" in source:
        lint_ok = False
        issues.append("Use a variável de ambiente DATABASE_URL para conexões com o banco de dados")

    valid = syntax_ok and safety_ok and lint_ok
    return {
        "valid": valid,
        "syntax_ok": syntax_ok,
        "lint_ok": lint_ok,
        "safety_ok": safety_ok,
        "issues": issues,
    }


def build_readme_snippet(*, session_id: int, user_email: str, model_used: str) -> str:
    return f"""# Script de Limpeza de Dados: Guia de Execução

Gerado pelo Assistente de Pesquisa em Saúde
ID da Sessão: {session_id}
Autor: {user_email}
Modelo: {model_used}

## Pré requisitos
- Python 3.11+
- pandas, SQLAlchemy, psycopg2-binary (ou driver de banco adequado)
- Acesso aprovado ao banco de dados em ambiente seguro

## Configuração
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
pip install pandas sqlalchemy psycopg2-binary
```

## Execução
```bash
python data_clean.py
```

## Importante
- Revise o script com sua equipe de engenharia de dados antes do uso em produção.
- Nunca execute scripts não revisados em bancos de dados de produção.
- Garanta conformidade com as políticas de governança de dados da sua instituição.
"""
