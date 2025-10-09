import streamlit as st
import subprocess
import json
import re
from graphviz import Digraph

st.set_page_config(page_title="Prompt → Data Model + DDL", page_icon="🧩", layout="centered")

# --- Header ---
st.title("🧠 Prompt → Data Model + SQL DDL Generator")
st.write("Provide a business scenario and generate star schema, SQL DDL, and ERD diagram.")

# --- Input prompt ---
user_prompt = st.text_area(
    "📝 Describe your data scenario:",
    height=150,
    placeholder="e.g. Analyze online sales by product, customer, and time."
)

sql_dialect = st.selectbox("🗂 Select SQL Dialect:", ["ANSI SQL", "Snowflake", "Databricks", "PostgreSQL", "MySQL"])

def generate_ddl(schema_json, dialect="ANSI SQL"):
    """Generate SQL CREATE TABLE statements from JSON schema, with dialect hints."""
    ddl_statements = []
    comment = f"-- SQL Dialect: {dialect}\n"

    # Fact table
    fact = schema_json.get("fact_table")
    if fact:
        columns = [f"{col['name']} {col['type']}" for col in fact["columns"]]
        ddl = f"CREATE TABLE {fact['name']} (\n    " + ",\n    ".join(columns) + "\n);"
        ddl_statements.append(ddl)

    # Dimension tables
    for dim in schema_json.get("dimension_tables", []):
        columns = [f"{col['name']} {col['type']}" for col in dim["columns"]]
        ddl = f"CREATE TABLE {dim['name']} (\n    " + ",\n    ".join(columns) + "\n);"
        ddl_statements.append(ddl)

    return comment + "\n\n".join(ddl_statements)

@st.cache_data(show_spinner=False)
def call_ollama_cached(full_prompt):
    """Call Ollama and cache results for identical prompts."""
    response = subprocess.run(
        ["ollama", "run", "llama3"],
        input=full_prompt.encode("utf-8"),
        capture_output=True,
        text=False
    )
    output = response.stdout.decode("utf-8").strip()
    return output

def generate_erd(schema_json):
    """Generate ERD diagram using graphviz."""
    dot = Digraph()

    # Add fact table
    fact = schema_json.get("fact_table")
    if fact:
        dot.node(fact["name"], f"{fact['name']}", shape="box")

    # Add dimension tables and relationships
    for dim in schema_json.get("dimension_tables", []):
        dot.node(dim["name"], dim["name"], shape="ellipse")
        if fact:
            dot.edge(dim["name"], fact["name"])

    return dot

if st.button("🚀 Generate Schema + SQL DDL"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Generating schema with Llama 3..."):
            try:
                full_prompt = f"""
You are a data modeling assistant. The user will describe a business scenario.
Design a STAR SCHEMA (1 fact table + supporting dimension tables).
Return the schema ONLY in valid JSON format with this structure:
{{
  "fact_table": {{
    "name": "FactTableName",
    "columns": [
      {{"name": "ColumnName", "type": "datatype", "description": "what it stores"}}
    ]
  }},
  "dimension_tables": [
    {{
      "name": "DimTableName",
      "columns": [
        {{"name": "ColumnName", "type": "datatype", "description": "what it stores"}}
      ]
    }}
  ]
}}

SQL Dialect: {sql_dialect}
User prompt: {user_prompt}
"""

                # Cached model call
                output = call_ollama_cached(full_prompt)

                # Extract JSON
                json_match = re.search(r"\{(?:.|\n)*\}", output)
                if json_match:
                    try:
                        schema_json = json.loads(json_match.group(0))

                        # Tabs for JSON + DDL
                        tab1, tab2 = st.tabs(["📄 Star Schema JSON", "💾 SQL DDL"])

                        with tab1:
                            st.json(schema_json)

                        with tab2:
                            ddl = generate_ddl(schema_json, sql_dialect)
                            st.code(ddl, language="sql")

                        # --- ERD Diagram below tabs ---
                        st.subheader("🗺️ ERD Diagram")
                        erd = generate_erd(schema_json)
                        st.graphviz_chart(erd)

                        # Downloads
                        st.download_button(
                            label="💾 Download Schema JSON",
                            data=json.dumps(schema_json, indent=2),
                            file_name="data_model_schema.json",
                            mime="application/json"
                        )

                        st.download_button(
                            label="💾 Download SQL DDL",
                            data=ddl,
                            file_name="data_model_schema.sql",
                            mime="text/sql"
                        )

                    except json.JSONDecodeError:
                        st.error("⚠️ Could not parse JSON even after extraction. Showing raw output:")
                        st.text_area("Raw Output", output, height=300)
                else:
                    st.error("⚠️ Could not find JSON in model output. Showing raw text:")
                    st.text_area("Raw Output", output, height=300)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
