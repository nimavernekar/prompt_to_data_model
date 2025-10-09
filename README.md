# 🧠 Prompt → Star Schema + SQL DDL + ERD Generator

A Streamlit-powered app that:
✅ Takes a business scenario as input  
✅ Generates a Star Schema (JSON) using LLM  
✅ Produces SQL DDL based on selected dialect  
✅ Visualizes the schema as an ERD diagram  
✅ Allows SVG download of the ERD

## 🚀 Features

- Streamlit UI with theme toggle
- Star Schema (Fact + Dimensions) generation
- SQL Dialect support (ANSI, Snowflake, Databricks, PostgreSQL, MySQL)
- ERD Diagram Preview + Download (SVG)
- Caching to avoid repeated model calls

## ▶️ Run Locally

```bash
python -m streamlit run app.py

Make sure Graphviz is installed:


brew install graphviz
📌 Tech Stack
Python
Streamlit
Graphviz
Ollama / Llama 3 (local model)


---

# ✅ 4️⃣ Add & Commit README

```bash
git add README.md
git commit -m "Add README documentation"
git push origin feature/erd-visualization
