# Library AI Agent — Streamlit App

> **Live Streamlit version** of the Library AI Agent, powered by IBM Granite on watsonx.ai

## 🚀 Run Locally

```bash
cd streamlit_app
streamlit run app.py
```

Opens at **http://localhost:8501**

## ☁️ Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set:
   - **Repository**: your GitHub repo
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   WATSONX_API_KEY = "your_api_key"
   WATSONX_PROJECT_ID = "your_project_id"
   WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
   GRANITE_MODEL_ID = "ibm/granite-4-h-small"
   ```
5. Click **Deploy** — live in ~60 seconds!

## 📁 Structure

```
streamlit_app/
├── app.py                    # Dashboard (entry point)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   ├── config.toml           # IBM-themed dark UI
│   └── secrets.toml          # IBM credentials (local only)
├── services/
│   ├── granite_service.py    # IBM Granite NLP via ibm-watsonx-ai
│   └── database.py           # JSON persistence layer
├── pages/
│   ├── 1_🤖_AI_Chat.py       # Conversational AI agent
│   ├── 2_📖_Catalog.py       # Browse & search books
│   ├── 3_📋_Reservations.py  # My reservations & waitlists
│   └── 4_👥_Students.py      # Student profile management
└── data/
    └── db.json               # Persistent library database
```
