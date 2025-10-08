import json

def extract_schema_info(model_output: str):
    """
    Extracts Fact and Dimension table information from model's JSON output.
    """
    try:
        data = json.loads(model_output)
        return data
    except json.JSONDecodeError:
        raise ValueError("⚠️ Could not parse JSON from model output. Please check the output format.")

def generate_ddl(schema_info: dict):
    """
    Generates DDL statements from parsed schema information.
    """
    ddl_statements = []

    for table_name, columns in schema_info.items():
        ddl = f"CREATE TABLE {table_name} (\n"
        column_defs = []

        for col_name, col_type in columns.items():
            column_defs.append(f"    {col_name} {col_type}")

        ddl += ",\n".join(column_defs) + "\n);"
        ddl_statements.append(ddl)

    return "\n\n".join(ddl_statements)
