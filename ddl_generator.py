# ddl_generator.py
import json
import re
from typing import Dict, Any

def extract_schema_info(model_output: str) -> Dict[str, Any]:
    """
    Accepts raw model output (possibly with markdown code fences or explanatory text),
    extracts the first JSON object found, and returns it as a Python dict.
    Raises ValueError if no JSON can be parsed.
    """
    # if already a dict, return it
    if isinstance(model_output, dict):
        return model_output

    # Search for ```json ... ``` fenced blocks first
    m = re.search(r"```(?:json)?\s*(\{(?:.|\n)*\})\s*```", model_output, re.DOTALL | re.IGNORECASE)
    if m:
        json_text = m.group(1)
    else:
        # fallback: find the first {...} block
        m2 = re.search(r"(\{(?:.|\n)*\})", model_output, re.DOTALL)
        json_text = m2.group(1) if m2 else None

    if not json_text:
        raise ValueError("⚠️ Could not find JSON in model output. Please ensure the model returns JSON.")

    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"⚠️ Could not parse JSON from model output: {e}")


def map_type_for_dialect(type_str: str, dialect: str) -> str:
    """
    Basic mapping of common SQL types to dialect-specific equivalents.
    This is intentionally lightweight — add mappings as you encounter new types.
    """
    if not isinstance(type_str, str):
        # if the model gives non-string, fallback to VARCHAR
        type_str = str(type_str)

    t = type_str.strip().lower()

    # VARCHAR / STRING mapping
    if "char" in t or "varchar" in t or t.startswith("string"):
        if dialect.lower() == "bigquery":
            return "STRING"
        if dialect.lower() == "snowflake":
            return "VARCHAR"
        return "VARCHAR"

    # DECIMAL / NUMERIC
    if "decimal" in t or "numeric" in t:
        if dialect.lower() == "bigquery":
            return "NUMERIC"
        return "DECIMAL(10,2)"

    # INTEGER / INT mapping
    if t in ("int", "integer") or "int" in t:
        if dialect.lower() == "bigquery":
            return "INT64"
        return "INT"

    # DATE / DATETIME / TIMESTAMP
    if "timestamp" in t or "datetime" in t:
        if dialect.lower() == "mysql":
            return "DATETIME"
        if dialect.lower() == "sqlserver":
            return "DATETIME2"
        # postgres, snowflake, bigquery: TIMESTAMP or DATE depending
        return "TIMESTAMP"

    if "date" in t:
        return "DATE"

    # BOOLEAN
    if "bool" in t:
        return "BOOLEAN"

    # fallback: return original (or upper-case)
    return type_str.upper()


def generate_ddl(schema_json: Dict[str, Any], dialect: str = "Postgres") -> str:
    """
    Generates DDL (CREATE TABLE statements) from a schema JSON.
    Accepts both formats:
      - STAR schema format:
        {
          "fact_table": {"name": "...", "columns": [{"name":"...", "type":"..."}]},
          "dimension_tables": [ {"name":"...", "columns":[...]} ]
        }
      - Or older map format:
        { "table_name": {"col_name": "TYPE", ...}, ... }
    """
    ddl_statements = []

    # STAR schema style
    if "fact_table" in schema_json:
        fact = schema_json.get("fact_table", {})
        fact_name = fact.get("name", "fact_table")
        fact_cols = []

        for col in fact.get("columns", []):
            col_name = col.get("name")
            col_type = col.get("type", "VARCHAR(255)")
            mapped = map_type_for_dialect(col_type, dialect)
            fact_cols.append(f"{col_name} {mapped}")

        ddl_statements.append(f"CREATE TABLE {fact_name} (\n    " + ",\n    ".join(fact_cols) + "\n);")

        for dim in schema_json.get("dimension_tables", []):
            dim_name = dim.get("name", "dim_table")
            dim_cols = []
            for col in dim.get("columns", []):
                col_name = col.get("name")
                col_type = col.get("type", "VARCHAR(255)")
                mapped = map_type_for_dialect(col_type, dialect)
                dim_cols.append(f"{col_name} {mapped}")
            ddl_statements.append(f"CREATE TABLE {dim_name} (\n    " + ",\n    ".join(dim_cols) + "\n);")

        return "\n\n".join(ddl_statements)

    # fallback: handle {table: {col: type, ...}, ...}
    for table_name, cols in schema_json.items():
        if not isinstance(cols, dict):
            continue
        column_defs = []
        for col_name, col_type in cols.items():
            mapped = map_type_for_dialect(col_type, dialect)
            column_defs.append(f"{col_name} {mapped}")
        ddl = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(column_defs) + "\n);"
        ddl_statements.append(ddl)

    return "\n\n".join(ddl_statements)
