import streamlit as st
import subprocess
import json
import re

st.set_page_config(page_title="Prompt → Data Model", page_icon="🧩", layout="centered")

st.title("🧠 Prompt → Data Model Generator")
st.write(
    "Enter a business scenario, and the local Llama 3 model will design a **Star Schema** for you (Fact + Dimension tables)."
)

# --- Input prompt from user ---
user_prompt = st.text_area(
    "Describe your data scenario:",
    height=150,
    placeholder="e.g. I want to analyze online sales by product, customer, and time..."
)

if st.button("Generate Schema"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Generating schema with Llama 3..."):
            try:
                # Ensure input is string
                full_prompt = str(user_prompt)
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

User prompt: {full_prompt}
"""

                # Call Llama 3 locally via Ollama
                response = subprocess.run(
                    ["ollama", "run", "llama3"],
                    input=full_prompt.encode("utf-8"),
                    capture_output=True,
                    text=False
                )

                # Decode output
                output = response.stdout.decode("utf-8").strip()

                # --- Extract JSON from possible markdown/code block ---
                json_match = re.search(r"\{(?:.|\n)*\}", output)
                if json_match:
                    try:
                        schema_json = json.loads(json_match.group(0))
                        st.json(schema_json)
                        st.success("✅ Schema generated successfully!")

                        # Download button
                        st.download_button(
                            label="💾 Download Schema JSON",
                            data=json.dumps(schema_json, indent=2),
                            file_name="data_model_schema.json",
                            mime="application/json"
                        )
                    except json.JSONDecodeError:
                        st.error("⚠️ Could not parse JSON even after extraction. Showing raw output:")
                        st.text_area("Raw Output", output, height=300)
                else:
                    st.error("⚠️ Could not find JSON in model output. Showing raw text:")
                    st.text_area("Raw Output", output, height=300)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
