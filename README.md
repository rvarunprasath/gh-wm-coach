# GH Wealth Management Coach (`gh-wm-coach`)

An intelligent, continuous-memory AI financial coach that combines a **Dual-Store Architecture (Relational Ledger + Embedded Knowledge Graph)** with an active conversational & voice workspace and real-time financial portfolio snapshots.

---

## 🌟 Key Capabilities

1. **Dual-Store Financial Architecture**:
   - **Relational Tables (SQLite)**: Provides numeric accuracy for portfolios, asset allocations, equity holdings, bank balances, and transactions.
   - **Embedded Knowledge Graph (NetworkX + SQLite)**: Preserves interconnected semantic memory—family dependents, life events (e.g. child college in 2028), retirement milestones, and risk profiles.
2. **Multi-Modal Data Ingestion**:
   - **Voice & Speech Recognition**: Integrated Web Speech API for verbal financial status updates (e.g., *"I hold total equity in stocks worth 20 lakhs"*).
   - **Document Parsing**: Ingests Bank statements, Mutual Fund CAS, and Broker CSVs (e.g. Zerodha, Groww).
   - **External API Integrations**: Simulated consent-based connect flow for RBI Account Aggregator (Setu / Finvu) and Broker APIs.
3. **GraphRAG Reasoning Engine**:
   - Solves multi-variable trade-offs (e.g., *"Can I buy a 50L apartment in 2 years?"*) by analyzing cash flow, current assets, and competing milestones stored in the knowledge graph without needing the user to re-explain their background.
4. **Interactive Split-Pane Workspace**:
   - **Left Pane**: Active interaction space (Chat, Voice recorder, Grounding & memory sync trace, preset prompts).
   - **Right Pane**: Segmented view with:
     - 📊 **Snapshot**: Asset allocation breakdown, holdings ledger, and connected bank accounts.
     - 🎯 **Life Goals**: Timeline of upcoming financial milestones with accumulated progress.
     - 🕸️ **Knowledge Graph**: Interactive node-link inspector of entities and directed relations.

---

## 🏗️ Project Architecture

```
gh-wm-coach/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application & startup hook
│   │   ├── api/
│   │   │   ├── chat.py               # /api/chat & /api/voice endpoints
│   │   │   ├── portfolio.py          # /api/portfolio snapshot & reset
│   │   │   ├── graph.py              # /api/graph node & link visualizer
│   │   │   └── ingestion.py          # /api/ingest/upload & /connect-api
│   │   ├── db/
│   │   │   ├── relational.py         # SQLite relational ledger engine
│   │   │   └── graph_store.py        # Embedded NetworkX knowledge graph
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic data schemas
│   │   └── services/
│   │       ├── extractor.py          # NLP & currency fact extractor (Lakhs/Crores)
│   │       ├── parser.py             # Statement parser (PDF/CSV)
│   │       ├── agent.py              # GraphRAG AI Coach reasoning agent
│   │       └── seed_data.py          # Realistic starter financial portfolio
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Split-pane interactive workspace
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Header.tsx            # Top bar with net worth & quick actions
│   │   │   ├── ChatSpace.tsx         # Left pane: chat, voice, grounding trace
│   │   │   ├── PortfolioSnapshot.tsx # Right pane: asset allocation & holdings
│   │   │   ├── LifeTimeline.tsx      # Right pane: life goals & milestones
│   │   │   ├── KnowledgeGraphView.tsx# Right pane: interactive graph viewer
│   │   │   ├── StatementUploadModal.tsx
│   │   │   └── ConnectApiModal.tsx
│   │   └── lib/
│   │       ├── api.ts                # Backend client
│   │       └── types.ts              # TypeScript definitions
│   └── package.json
└── start.sh                          # One-command dual server launcher
```

---

## 🚀 Quick Start

### 1. Start Both Backend & Frontend
Run the launcher script:
```bash
./start.sh
```

Or run them individually in separate terminals:

**Backend (FastAPI)**:
```bash
cd backend
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

**Frontend (Next.js)**:
```bash
cd frontend
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Testing the User Flows

1. **Voice or Text Financial Updates**:
   - Type or speak: `I hold total equity in stocks worth 20 lakhs`
   - **Result**: The agent automatically extracts the ₹20,00,000 equity valuation, inserts it into the `holdings` table, creates the `Asset` node in the Knowledge Graph, links it with `OWNS`, and recalculates your Net Worth and asset allocation live on the dashboard.
2. **Context-Aware Trade-off Query**:
   - Ask: `Can I afford to purchase a 50 lakh apartment in 2 years?`
   - **Result**: The coach retrieves your ₹85,000/month surplus, factors in 24 months of savings (₹20.4L) vs 20% down payment (₹10L), calculates the loan EMI on the remaining ₹40L, and checks against competing goals in your Knowledge Graph (like Ananya's college fund in 2028).
3. **Statement Ingestion**:
   - Click **"Upload Statement"** in the top bar and test with the pre-loaded **HDFC Bank CSV** or **Zerodha Holdings CSV** to see automatic statement processing and graph synchronization.
4. **API Integration**:
   - Click **"Connect API"** to simulate linking with **Zerodha Kite**, **Groww**, or **RBI Account Aggregators** with one click.

---

## ☁️ Cloud Deployment (Cloud Run, AlloyDB, Gemini & Cloud Build)

Complete production cloud deployment instructions, Terraform configurations, and CI/CD pipelines are available in **[DEPLOYMENT.md](file:///Users/arunprasathrv/Documents/batcave/weave/gh-wm-coach/DEPLOYMENT.md)**.

- **Frontend Microservice**: Next.js 14 deployed to Google Cloud Run (`wm-coach-frontend`).
- **Backend Microservice**: FastAPI GraphRAG engine deployed to Google Cloud Run (`wm-coach-backend`).
- **Database**: Google Cloud **AlloyDB for PostgreSQL** with Private Services Access (PSA).
- **AI Reasoning**: Google **Gemini AI** (`gemini-2.0-flash`) via Google AI Studio API key or Vertex AI.
- **Networking**: Custom VPC (`wm-coach-vpc`) with **Direct VPC Egress** connecting Cloud Run to AlloyDB on private IP.
- **CI/CD Pipelines**: Automated Google Cloud Build triggers on push to [https://github.com/EaseMyWorld/gh-wm-coach](https://github.com/EaseMyWorld/gh-wm-coach).
- **Quick Setup**: Run `./scripts/setup-gcp-infra.sh` or `terraform apply` in `./terraform`.
