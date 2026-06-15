from app.services.scriptgen.validator import validate_script


VALID_SCRIPT = '''
import os
from sqlalchemy import create_engine
import pandas as pd

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/db")

def main():
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM patients", engine)
    return df

if __name__ == "__main__":
    main()
'''


def test_valid_script_passes():
    result = validate_script(VALID_SCRIPT)
    assert result["syntax_ok"] is True
    assert result["safety_ok"] is True
    assert result["valid"] is True


def test_empty_script_fails():
    result = validate_script("")
    assert result["valid"] is False
    assert "vazio" in result["issues"][0].lower()


def test_forbidden_drop_detected():
    bad = VALID_SCRIPT + '\nengine.execute("DROP TABLE patients")'
    result = validate_script(bad)
    assert result["safety_ok"] is False


def test_syntax_error_detected():
    result = validate_script("def main(:\n    pass")
    assert result["syntax_ok"] is False
