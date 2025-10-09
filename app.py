# app.py
import streamlit as st
import subprocess
import json
import re

from ddl_generator import extract_schema_info, generate_ddl

st.set_page_config(page_title="Prompt → Data Model + DDL", page_icon="🧩", layout="centered")

st.title("🧠 Prompt → Data Model + SQL DDL Generator")
st.write(
    "Enter a business scenario. The local Llama 3 model will design a **Star Schema** and generate SQL DDL statements for you."
)

# --- Input prompt ---
user_prompt = st.text_area(
    "Describe your data scenario:",
    height=150,
    placeholder="e.g. Analyze online sales by product, customer, and time."
)

# --- SQL Dialect selection ---
dialect = st.selectbox("SQL Dialect", ["Postgres", "MySQL", "Snowflake", "BigQuery", "SQLServer"])

def call_ollama_cli(prompt: str, model: str = "llama3") -> str:
    """
    Run the Ollama model via subprocess and return stdout as text.
    """
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        capture_output=True
    )
    return proc.stdout.decode("utf-8")


def extract_json_from_output(output: str) -> str:
    """
    Try to extract JSON block from model output (handles ```json``` code fences or the first {...} block).
    Returns the JSON string or raises ValueError.
    """
    # code fence search
    m = re.search(r"```(?:json)?\s*(\{(?:.|\n)*\})\s*```", output, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)

    # fallback: first brace block
    m2 = re.search(r"(\{(?:.|\n)*\})", output, re.DOTALL)
    if m2:
        return m2.group(1)

    raise ValueError("⚠️ Could not find JSON in model output.")


def build_model_prompt(user_prompt: str) -> str:
    return f"""
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

User prompt: {user_prompt}
"""


if st.button("Generate Schema + SQL DDL"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Generating schema with Llama 3..."):
            try:
                full_prompt = build_model_prompt(user_prompt)
                raw_output = call_ollama_cli(full_prompt, model="llama3")
                # extract JSON string
                try:
                    json_text = extract_json_from_output(raw_output)
                except ValueError:
                    st.error("⚠️ Could not find a JSON block in model output. See raw output below.")
                    st.text_area("Raw Output", raw_output, height=300)
                    raise

                # parse JSON into dict
                try:
                    schema_json = json.loads(json_text)
                except json.JSONDecodeError as e:
                    st.error(f"⚠️ JSON parse failed: {e}")
                    st.text_area("Raw JSON", json_text, height=300)
                    raise

                # show JSON
                st.subheader("🌟 Generated Star Schema (JSON)")
                st.json(schema_json)

                # generate dialect-aware DDL
                ddl = generate_ddl(schema_json, dialect)
                st.subheader("💻 Generated SQL DDL")
                st.code(ddl, language="sql")

                # downloads
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

            except Exception as e:
                # error already displayed above; show concise message
                st.error(f"❌ Error: {str(e)}")
