import streamlit as st
import subprocess
import json
import re

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

def generate_ddl(schema_json):
    """Generate SQL CREATE TABLE statements from JSON schema."""
    ddl_statements = []

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

    return "\n\n".join(ddl_statements)


if st.button("Generate Schema + SQL DDL"):
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

User prompt: {user_prompt}
"""

                # Call Ollama
                response = subprocess.run(
                    ["ollama", "run", "llama3"],
                    input=full_prompt.encode("utf-8"),
                    capture_output=True,
                    text=False
                )

                output = response.stdout.decode("utf-8").strip()

                # Extract JSON
                json_match = re.search(r"\{(?:.|\n)*\}", output)
                if json_match:
                    try:
                        schema_json = json.loads(json_match.group(0))
                        st.subheader("🌟 Generated Star Schema (JSON)")
                        st.json(schema_json)

                        # Download JSON
                        st.download_button(
                            label="💾 Download Schema JSON",
                            data=json.dumps(schema_json, indent=2),
                            file_name="data_model_schema.json",
                            mime="application/json"
                        )

                        # Generate DDL
                        ddl = generate_ddl(schema_json)
                        st.subheader("💻 Generated SQL DDL")
                        st.code(ddl, language="sql")

                        # Download DDL
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