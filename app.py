import streamlit as st
import subprocess
import json
import re
import graphviz
import pandas as pd


def extract_file_context(uploaded_files):
    """
    Extract structured, LLM-friendly summaries from uploaded files
    instead of dumping full content.
    """
    context_snippets = []

    for file in uploaded_files:
        filename = file.name.lower()

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(file)
                inferred = {}

                # Infer column data types
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    if "int" in dtype:
                        inferred[col] = "INT"
                    elif "float" in dtype or "double" in dtype:
                        inferred[col] = "FLOAT"
                    elif "date" in col.lower():
                        inferred[col] = "DATE"
                    else:
                        inferred[col] = "STRING"

                snippet = (
                    f"File: {file.name}\n"
                    f"Type: CSV\n"
                    f"Columns & Types: {inferred}\n"
                    f"Sample Row: {df.head(1).to_dict(orient='records')[0]}"
                )
                context_snippets.append(snippet)

            elif filename.endswith(".json"):
                data = json.load(file)
                # If JSON is a list of dicts, infer keys
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    keys = list(data[0].keys())
                    snippet = (
                        f"File: {file.name}\n"
                        f"Type: JSON\n"
                        f"Top-Level Keys: {keys}\n"
                        f"Sample Entry: {data[0]}"
                    )
                else:
                    snippet = (
                        f"File: {file.name}\n"
                        f"Type: JSON\n"
                        f"Content Preview: {str(data)[:400]}"
                    )
                context_snippets.append(snippet)

            elif filename.endswith(".txt"):
                text = file.read().decode("utf-8")[:400]
                snippet = (
                    f"File: {file.name}\n"
                    f"Type: TXT\n"
                    f"Content Preview: {text}"
                )
                context_snippets.append(snippet)

        except Exception as e:
            context_snippets.append(f"Error processing {file.name}: {e}")

    return "\n\n".join(context_snippets) if context_snippets else ""


# =========================
# Header + Theme Toggle
# =========================
st.set_page_config(page_title="Prompt → Data Model + DDL", page_icon="🧩", layout="wide")

col_title, col_toggle = st.columns([4, 1], vertical_alignment="center")
with col_title:
    st.title("🧠 Prompt → Data Model + SQL DDL Generator")
with col_toggle:
    dark_mode = st.toggle("🌙 Dark Mode", key="theme_toggle", value=False)

# Global theme styles
if dark_mode:
    st.markdown(
        """
        <style>
            .stApp { background-color: #121212; color: #e8e8e8; }
            .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background: #1e1e1e !important; color: #e8e8e8 !important; }
            .stDownloadButton button, .stButton button { background: #2a2a2a !important; color: #e8e8e8 !important; border: 1px solid #3a3a3a !important; }
            .stCode code { background: #0f0f0f !important; color: #e8e8e8 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.write("Enter a business scenario to generate Star Schema, SQL DDL, and an ERD diagram.")

# =========================
# Inputs
# =========================
user_prompt = st.text_area(
    "Describe your data scenario:",
    height=150,
    placeholder="e.g. Analyze online sales by product, customer, and time."
)

# 📁 Optional: File Upload for RAG Context
uploaded_files = st.file_uploader(
    "Upload relevant files (CSV, JSON, or TXT) for context-aware schema generation:",
    type=["csv", "json", "txt"],
    accept_multiple_files=True
)


sql_dialect = st.selectbox(
    "Select SQL Dialect:",
    ["ANSI SQL", "Snowflake", "Databricks", "PostgreSQL", "MySQL"]
)

# =========================
# Helpers
# =========================
def generate_ddl(schema_json, dialect="ANSI SQL"):
    ddl_statements = []
    header = f"-- SQL Dialect: {dialect}\n"

    fact = schema_json.get("fact_table")
    if fact:
        cols = [f"{c['name']} {c['type']}" for c in fact.get("columns", [])]
        ddl_statements.append(
            f"CREATE TABLE {fact['name']} (\n    " + ",\n    ".join(cols) + "\n);"
        )

    for dim in schema_json.get("dimension_tables", []):
        cols = [f"{c['name']} {c['type']}" for c in dim.get("columns", [])]
        ddl_statements.append(
            f"CREATE TABLE {dim['name']} (\n    " + ",\n    ".join(cols) + "\n);"
        )

    return header + "\n\n".join(ddl_statements)

@st.cache_data(show_spinner=False)
def call_ollama_cached(full_prompt: str) -> str:
    resp = subprocess.run(
        ["ollama", "run", "llama3"],
        input=full_prompt.encode("utf-8"),
        capture_output=True,
        text=False
    )
    return resp.stdout.decode("utf-8").strip()

def generate_erd(schema_json) -> graphviz.Digraph:
    dot = graphviz.Digraph(comment="Star Schema ERD")
    dot.attr(rankdir="LR")

    fact = schema_json.get("fact_table")
    fact_name = fact["name"] if fact else None

    if fact_name:
        dot.node(fact_name, f"FACT: {fact_name}", shape="box", style="filled", color="lightblue")

    for dim in schema_json.get("dimension_tables", []):
        dim_name = dim["name"]
        dot.node(dim_name, f"DIM: {dim_name}", shape="ellipse", style="filled", color="lightgray")
        if fact_name:
            dot.edge(dim_name, fact_name)

    return dot

# =========================
# Main Action
# =========================
if st.button("Generate Schema + SQL DDL + ERD", type="primary"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Generating with Llama 3..."):
            try:
                file_context = extract_file_context(uploaded_files) if uploaded_files else "No external documents provided."

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

User prompt: {user_prompt}
Additional context from uploaded files:

{file_context}
SQL Dialect: {sql_dialect}
"""

                output = call_ollama_cached(full_prompt)

                # Extract JSON from model output
                match = re.search(r"\{(?:.|\n)*\}", output)
                if not match:
                    st.error("⚠️ Could not find JSON in model output. Showing raw text:")
                    st.text_area("Raw Output", output, height=300)
                else:
                    try:
                        schema_json = json.loads(match.group(0))

                        st.subheader("🌟 Generated Star Schema (JSON)")
                        st.json(schema_json)

                        ddl = generate_ddl(schema_json, sql_dialect)
                        st.subheader("💻 Generated SQL DDL")
                        st.code(ddl, language="sql")

                        st.download_button(
                            "Download Schema JSON",
                            data=json.dumps(schema_json, indent=2),
                            file_name="data_model_schema.json",
                            mime="application/json"
                        )
                        st.download_button(
                            "Download SQL DDL",
                            data=ddl,
                            file_name="data_model_schema.sql",
                            mime="text/sql"
                        )

                        st.subheader("🗺️ ERD Diagram")
                        erd = generate_erd(schema_json)
                        # Use Streamlit's built-in Graphviz renderer (no system 'dot' needed)
                        st.graphviz_chart(erd.source)

                    except json.JSONDecodeError:
                        st.error("⚠️ JSON parsing failed. Showing raw output:")
                        st.text_area("Raw Output", output, height=300)

            except Exception as e:
                st.error(f"❌ Error: {e}")
