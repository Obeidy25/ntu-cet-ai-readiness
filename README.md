# NTU CET - RAG Policy Analysis & Hybrid QA Prototype

A state-of-the-art Hybrid RAG (Retrieval-Augmented Generation) system built with FastAPI, ChromaDB, and Streamlit. Designed for policy analysis and document Q&A, supporting local open-source LLMs (Ollama) for privacy and edge deployment, as well as cloud LLMs (OpenAI, Anthropic, Gemini) using custom API keys.

---

## 🌟 Key Features

### 1. 🧠 Semantic & Sentence-Aware Chunking
- **Intelligent Text Splitting**: Uses a two-level splitting mechanism (paragraph boundary `\n\n` followed by sentence boundaries `. ! ? ؟`) for both Arabic and Latin text.
- **Context Preservation**: Groups full sentences up to `CHUNK_SIZE` (500 chars) instead of cutting mid-sentence.
- **Dynamic Overlap**: Carries trailing sentences into adjacent chunks with automatic size-capping to prevent chunk overflow.
- **Oversized Sentence Fallback**: Handles long unpunctuated sentences gracefully.

### 2. 📂 Multi-Format Document Ingestion
- **Supported Formats**: Upload and ingest **PDF**, **Excel** (`.xlsx` / `.xls`), and **Word** (`.docx`) files through a single unified interface.
- **PDF Extraction** (`PyMuPDF`): Page-by-page text and table extraction with automatic Markdown serialization.
- **Excel Extraction** (`openpyxl`): Each worksheet is treated as an independent page; all rows are serialized as Markdown tables preserving headers and cell relationships.
- **DOCX Extraction** (`python-docx`): Extracts paragraph text (grouped into virtual pages of 30 paragraphs) and all embedded Word tables as Markdown.
- **Automatic MIME Routing**: The frontend detects the file extension and sets the correct MIME type; the backend validates the extension and routes to the matching extraction function.
- **Unified Vector Indexing**: Extracted content from all formats is chunked and stored in ChromaDB with the same `source`, `page`, and `content_type` metadata schema.

### 3. 📊 Policy Gap Analysis & ITU AI Readiness 2.0 Framework
- **Dedicated UI Workspace (`⚖️ Policy Gap Analysis Tab`)**: A purpose-built tab in the Streamlit frontend allowing users to select two documents (`Document A` vs `Document B`), trigger instant comparative gap analysis, render formatted results, and export the analysis to Markdown (`📥 Download Gap Analysis`).
- **Official ITU AI Readiness 2.0 13-Dimension Mapping (`POST /compare`)**: Evaluates policy/strategy documents against the official 13 dimensions:
  - `Data/model Marketplace`
  - `Generated Content Marketplace`
  - `Cross-domain Correlation Analysis`
  - `Contextualization & Regional Impact`
  - `Level of Integration of AI in Workflows`
  - `Human Interface`
  - `Strategy Alignment`
  - `Collaboration with AI`
  - `Impacts of Humans in AI Integration`
  - `AI & Policies`
  - `AI for Inclusion`
  - `Granular Priorities`
  - `Digital Infrastructure`
- **ITU-T Y.3172 Pipeline Node Alignment**: Identifies gaps related to standard machine learning pipeline nodes (`SRC`, `Collector`, `Pre-producer`, `Model`, `Policy`, `Distributor`, `SINK`).
- **Structured 4-Part Output**: Tags every identified gap with its bracketed dimension name (e.g. `[Strategy Alignment]`, `[Digital Infrastructure]`) across unique topics, shared differences, and concrete recommendations.
- **Optimized Context Budget**: Intelligently caps per-document chunks (`MAX_CHUNKS_PER_DOC_FOR_COMPARE = 10`) for fast and balanced multi-document reasoning.

### 4. 🛡️ Two-Stage Query Routing & Dynamic Conversational Onboarding
- **Stage 1: Greeting & Dynamic Onboarding**: Intercepts greetings and small talk (Arabic & English, ≤ 7 words) to greet the user politely in 0ms latency, list actual documents present in the knowledge base, and suggest 2-3 tailored discussion starter questions without hallucinations.
- **Stage 2: Calibrated Relevance Threshold Filtering**: Evaluates calibrated exponential decay similarity score (`100 * exp(-dist / 220)`). If the top retrieved chunk is below **12.0% similarity**, the system skips LLM generation and returns a graceful refusal in the matching language, fully preventing hallucinations while supporting cross-lingual queries.
- **Strict Multi-Provider System Prompts**: Enforces language matching, strict factual grounding, structured formatting, and zero-hallucination guardrails across all local and cloud LLM providers.

### 5. 🇸🇦 Native Arabic RTL Typography & Cross-Lingual Knowledge Synthesis
- **Dynamic Right-to-Left (RTL) Layout**: Automatically detects Arabic text and applies native RTL styling (`direction: rtl; text-align: right;`) with modern Arabic typography and customized quote banners (`arabic-quote`).
- **Cross-Lingual Information Extraction**: Seamlessly understands Arabic questions directed at English documents, extracting key facts, metrics, and tables to provide fluent, well-structured Arabic responses.

### 6. 🧠 Multi-Turn Conversational Memory & Persistent Chat Sessions
- **Persistent SQLite Chat Database**: Automatically saves all conversations to `./chat_sessions.db` with auto-generated titles, timestamps, and message counts.
- **Multi-Session Sidebar Navigation**: Users can browse past conversations, start a new chat (`➕ New Chat`), or delete unwanted sessions (`🗑️`).
- **Sliding-Window Dialogue Context**: Automatically retains a 4-message sliding window (last 2 full turns) to seamlessly understand follow-up questions, pronouns, and references across all local and cloud providers.
- **↩️ Reply to Specific Message (Targeted Quoting)**: Users can click `↩️` on any prior message to reply directly to that exact point with visual blockquote formatting and prioritized prompt grounding.
- **Multi-Document Summary Handler**: Automatically detects overview requests (`summary`, `overview`, `لخص`, `الأهداف`, `النتائج`) and aggregates representative excerpts across all ingested files for a unified executive summary.

### 7. 📊 Structured Table Extraction & Markdown Preservation
- **PyMuPDF Table Extraction** (PDF): Automatically detects vector and tabular data structures within PDF pages using `page.find_tables()`.
- **openpyxl Sheet Extraction** (Excel): Reads all worksheets and converts rows into Markdown tables with full header preservation.
- **python-docx Table Extraction** (DOCX): Extracts all embedded Word tables and serializes them as Markdown.
- **Atomic Table Chunks**: Indexes tables as complete units with `content_type: "table"` metadata so tabular rows and headers are never broken apart mid-sentence.
- **Interactive UI Indicators**: Frontend highlights retrieved table chunks with `📊 [Table]` icons and badges.

### 8. 🖼️ Multi-Modal Vision AI Chart & Diagram Analysis *(PDF only)*
- **Intelligent Visual Filtering**: Automatically scans uploaded PDFs for significant charts, diagrams, and figures, while filtering out decorative icons, bullets, and tiny logos (width/height < 150px).
- **Vision AI Captioning**: Analyzes visual charts using multimodal models (local `llama3.2-vision`/`llava` or cloud `gemini-1.5-flash`/`gpt-4o-mini`/`claude-3-5-sonnet`) to extract precise axes, metrics, percentages, and trends.
- **Vector-Indexed Visual Knowledge**: Stores chart descriptions as first-class semantic chunks with `content_type: "figure"` so visual knowledge is fully retrievable through natural language queries.
- **On-Demand Performance Toggle**: Users can toggle Vision AI on/off during PDF ingestion (`🖼️ Analyze Charts with Vision AI`) to maximize processing speed on lightweight local hardware or enable deep visual extraction on powerful machines.

> [!NOTE]
> Vision AI chart analysis is available for **PDF files only**. Excel and DOCX files use structural text and table extraction instead.

### 9. 📈 Cross-Document Comparative Visual Synthesis & Dynamic Chart Generation
- **Comparative Multi-Doc Reasoning**: Analyzes metrics, models, percentages, and policies across multiple uploaded documents to synthesize differences and commonalities.
- **Dynamic Mermaid Diagram Synthesis**: Synthesizes executable Mermaid diagrams (`pie`, `graph TD`, `quadrantChart`, `mindmap`) illustrating the comparative breakdown.
- **Interactive In-Chat Rendering**: Streamlit frontend automatically renders Mermaid code blocks as sleek, dark-mode SVG diagrams directly inside the chat interface.

### 10. 🛡️ Concurrency Control & Atomic State-Machine Resilience
- **ChromaDB Write Mutex (`chroma_write_lock`)**: Serializes concurrent document uploads and chunk deletions into an orderly async queue, eliminating vector store collisions and race conditions.
- **SQLite WAL Mode (`PRAGMA journal_mode=WAL`)**: Configures Write-Ahead Logging with a 10s busy timeout, allowing simultaneous chat session reads and atomic updates with zero `"database is locked"` errors.
- **LLM Inference Semaphore (`generation_semaphore = 2`)**: Limits overlapping heavy model inferences to prevent GPU memory exhaustion, local Ollama crashes, or system freezes.
- **Frontend State-Machine (`pending_turn`) & Action Locking (`is_busy`)**: Prevents in-flight generation interruptions when users interact with sidebar widgets or buttons, committing prompt and answer turns atomically.

### 11. 💻 Modern Frontend (Streamlit)
- **Chat Sessions Sidebar**: Interactive list of past chat sessions with auto-generated titles, active session highlights, and individual delete buttons.
- **Knowledge Base Sidebar**: Displays an interactive, auto-refreshing list of ingested documents (PDF / Excel / DOCX) with truncated titles, chunk count badges, and per-document delete buttons (`🗑️`).
- **Hybrid Provider Selector**: Seamlessly switch between local Ollama models (e.g., `llama3.1`, `qwen2.5-coder`) and cloud providers (`OpenAI`, `Anthropic`, `Gemini`).
- **Interactive Retrieval Inspection**: Expandable view in chat messages showing retrieved context sources, page numbers, content types (`📄 Text`, `📊 Table`, `📈 Figure`), and exact similarity percentages.

---

## 📁 Project Structure

```
ntu_cet_project/
├── backend.py               # FastAPI server: multi-format ingestion (PDF/Excel/DOCX), ChromaDB vector store, SQLite sessions, table & vision extraction, query routing, memory, concurrency locks, and LLM providers.
├── frontend.py              # Streamlit UI: multi-format file uploader, chat session manager, Arabic RTL typography, knowledge base management, model selection, reply quoting, Vision toggle, and interactive RAG chat.
├── test_concurrency.py      # Diagnostic test script for multi-client concurrency control, async locks, and SQLite thread safety.
├── test_visual_synthesis.py # Diagnostic test script for cross-document visual synthesis and Mermaid diagram extraction.
├── test_sessions.py         # Diagnostic test script for SQLite persistent chat sessions, CRUD operations, and reply quoting.
├── test_vision.py           # Diagnostic test script for PDF image extraction, size filtering, and Vision AI payload formatting.
├── test_tables.py           # Diagnostic test script for structured table extraction and Markdown serialization.
├── test_memory.py           # Diagnostic test script for multi-turn conversational memory and payload formatting.
├── test_chunking.py         # Diagnostic test script for evaluating chunking metrics (min/max/avg length, overlap, oversized checks).
├── test_compare.py          # Diagnostic test script for document comparison and gap analysis logic.
├── test_routing.py          # Diagnostic test script for greeting fast-path and relevance threshold guardrails.
├── requirements.txt         # Python package dependencies.
└── .env.example             # Sample environment variable configuration.
```

---

## 🚀 Setup & Installation

### 1. Prerequisites & Dependencies
Ensure Python 3.10+ is installed. Install required packages:
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes all necessary libraries:

| Package | Purpose |
|---|---|
| `fastapi` / `uvicorn` | Backend API server |
| `streamlit` | Frontend web UI |
| `chromadb` | Vector database |
| `pymupdf` | PDF text & table extraction |
| `openpyxl` | Excel (.xlsx / .xls) extraction |
| `python-docx` | Word (.docx) extraction |
| `openai` | OpenAI & Ollama API client |
| `Pillow` | Image processing for Vision AI |
| `python-dotenv` | Environment variable loading |

### 2. Ollama Setup (Local LLMs, Embeddings & Vision AI)
Download and install [Ollama](https://ollama.com). Pull the local embedding model, text generation models, and optional local vision model.

#### A. Required Local Embedding Model (Always Free & Offline)
```bash
# High-precision embedding model for ChromaDB vector store
ollama pull nomic-embed-text
```

#### B. Local Text & Reasoning Models (Choose based on your hardware)
The system **automatically auto-detects and supports any model** installed in Ollama via dynamic discovery:

- **💻 Lightweight Tier (Laptops / Standard PCs - 8GB to 16GB RAM):**
  ```bash
  ollama pull llama3.1
  ollama pull qwen2.5-coder:1.5b
  ollama pull deepseek-r1:8b
  ```

- **🚀 Flagship / High-End Workstation Tier (Evaluators / High-VRAM GPUs - RTX 3090/4090, A100/H100, Apple Silicon M2/M3/M4 Max/Ultra):**
  ```bash
  # State-of-the-art enterprise-grade reasoning & multilingual models
  ollama pull llama3.3:70b
  ollama pull qwen2.5:32b
  ollama pull qwen2.5:72b
  ollama pull deepseek-r1:14b
  ollama pull deepseek-r1:32b
  ```

#### C. Local Vision AI Models (For 100% Offline Chart & Diagram Extraction)
```bash
# Recommended for standard & high-end machines (Free, offline multimodal extraction)
ollama pull llama3.2-vision
# High-end flagship vision model:
# ollama pull llama3.2-vision:90b
# Alternative local vision model:
# ollama pull llava:34b
```

> [!TIP]
> **🚀 Zero-Configuration Auto-Discovery & Blazing Performance**:
> - **Seamless Model Switching**: Any model pulled in Ollama appears immediately in the frontend dropdown selector. Click `🔄` in the sidebar to refresh models without restarting the server.
> - **Hardware Acceleration**: On high-performance evaluation machines with dedicated GPUs, ChromaDB vector indexing and local LLM inferences run at blistering speeds with near-instant generation.
> - **Hybrid Cloud Fallback**: Cloud providers (**Google Gemini**, **OpenAI**, **Anthropic**) remain available at any time via sidebar API keys.

---

## 🏃 Running the Application

### Step 1: Start Ollama Service
```bash
ollama serve
```

### Step 2: Launch FastAPI Backend
In a separate terminal:
```bash
uvicorn backend:app --reload --port 8000
```
Backend API interactive documentation will be available at `http://localhost:8000/docs`.

### Step 3: Launch Streamlit Frontend
In a separate terminal:
```bash
streamlit run frontend.py
```
The application will open automatically at `http://localhost:8501`.

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System status & total vector database chunk count |
| `POST` | `/ingest` | Uploads and processes a **PDF, Excel, or DOCX** file with sentence-aware chunking & optional Vision AI (PDF only) |
| `POST` | `/ask` | Queries the RAG pipeline with 2-stage routing, cross-lingual synthesis & multi-turn memory |
| `GET` | `/documents` | Returns all ingested document names and chunk statistics |
| `DELETE` | `/documents/{doc_name}` | Deletes a document and purges all its chunks from ChromaDB with write-lock protection |
| `POST` | `/compare` | Performs policy gap analysis between two ingested documents |
| `GET` | `/sessions` | Returns list of all saved chat sessions sorted by newest activity |
| `GET` | `/sessions/{session_id}` | Retrieves full message history and metadata for a specific session |
| `DELETE` | `/sessions/{session_id}` | Deletes a specific conversation session from SQLite database |
| `GET` | `/models` | Detects installed local Ollama models & available cloud options |

---

## 📄 Supported File Formats

| Format | Extension | Extraction Method | Tables | Vision AI |
|---|---|---|---|---|
| PDF | `.pdf` | PyMuPDF (`fitz`) | ✅ Auto-detected | ✅ Supported |
| Excel | `.xlsx` / `.xls` | openpyxl | ✅ All sheets as Markdown | ❌ N/A |
| Word | `.docx` | python-docx | ✅ All embedded tables | ❌ N/A |

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `"Backend is not reachable"` | Backend server is offline | Ensure `uvicorn backend:app --port 8000` is running |
| Empty local models list | Ollama server is stopped | Start `ollama serve` and verify models with `ollama list` |
| Ingestion error | Embedding model missing | Run `ollama pull nomic-embed-text` |
| `"Unsupported file type"` error | Wrong file format uploaded | Upload only `.pdf`, `.xlsx`, `.xls`, or `.docx` files |
| Low similarity response | Query context relevance < 12% | Upload more relevant documents or rephrase the question |
| Generic chart description | Local vision model missing | Run `ollama pull llama3.2-vision` or use a Cloud API key (Gemini/OpenAI) |
| Excel shows no data | Sheet is empty | Ensure the Excel file has data rows in at least one worksheet |
