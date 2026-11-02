# BHASHA SAHITA (भाषा सहिता)
Multilingual, RAG-First Government Scheme Discovery & Verified Eligibility Engine.

BHASHA SAHITA retrieves information from official government documents (PDFs, circulars, notifications) and uses retrieved chunks to answer user queries with precise citations.

> **Core Architectural Principle**:
> *RAG handles scheme discovery, document retrieval, and contextual explanations. The eligibility engine remains strictly deterministic so that eligibility decisions are never guessed or fabricated by an AI model.*

---

## 1. Overall Architecture

```
DATA PIPELINE                              USER PIPELINE
Central Govt Sources                       User Query (en, hi, mr, pa, te, bn)
State Govt Sources (HR, MH, PB, WB, TG)         │
       │                                        ▼
Official PDFs / Guidelines / Portals       Language Detection (6 Indic Languages)
       │                                        │
Document Collection (app/ingestion/collector)   ▼
       │                                   Query Understanding (app/nlp)
PDF / HTML / Text Extraction (extractor)        │
       │                                        ▼
Text Cleaning & Indic NFC Normalization    Query Multilingual Embedding (app/embeddings)
       │                                        │
Metadata Extraction (metadata_extractor)        ▼
       │                                   Hybrid Retrieval (Vector + BM25)
Semantic Chunking (with page & headers)         │
       │                                        ▼
Multilingual Embeddings (app/embeddings)   Metadata Filtering (10 Scheme Filters)
       │                                        │
Vector Database (PostgreSQL+pgvector /     Reranking (Score & Relevance Blending)
LocalVectorStore fallback)                      │
                                                ▼
                                           Retrieved Document Chunks
                                                │
                                                ├──────────────────────────────┐
                                                ▼                              ▼
                                      Deterministic Engine           RAG Context Builder
                                    (app/eligibility - 3 Indicators) (Page & Section citations)
                                                │                              │
                                                └──────────────┬───────────────┘
                                                               ▼
                                                    Answer Generation (app/rag)
                                                               │
                                                               ▼
                                                    Multilingual Grounded Response
                                                    (Sources + Eligibility + Dashboard)
```

---

## 2. Key Components & Responsibilities

### Data Ingestion Pipeline (`app/ingestion/`)
- **`extractor.py`**: Extracts structured text and page numbers from official PDF guidelines using PyMuPDF (`pymupdf`), HTML pages, and text documents with OCR fallback.
- **`cleaner.py`**: Normalizes Indic scripts via Unicode NFC, cleans whitespace, removes navigation headers, footers, and boilerplate legal disclaimers.
- **`metadata_extractor.py`**: Extracts structured schema metadata: scheme name, category, subcategory, state, level, beneficiary, age criteria, income ceilings, social categories, financial & non-financial benefits, required documents, deadlines, and portal URLs.
- **`chunker.py`**: Splits documents into semantic chunks (200–350 words) with context headers: `[Scheme: <Name> | ID: <ID> | Level: <L> | State: <S> | Section: <H> | Page: <P>]`.
- **`collector.py`**: Generates and manages official guideline documents for all Central and State schemes in `data/documents/`.

### Multilingual Embeddings (`app/embeddings/`)
- **`generator.py`**: Generates dense 256-dimensional multilingual vector representations for document chunks and user queries across English, Hindi, Marathi, Punjabi, Telugu, and Bengali. Supports cross-lingual semantic alignment and unit L2 normalization.

### Vector Storage (`app/vector_store/`)
- **`base.py`**: Abstract Base Class defining standard vector store operations.
- **`local_store.py`**: High-performance embedded vector store combining NumPy cosine similarity, BM25 inverted index, Reciprocal Rank Fusion (RRF), and full metadata filtering.
- **`pgvector_store.py`**: PostgreSQL + `pgvector` implementation for relational storage with vector cosine distance (`<=>`) and JSONB querying.
- **`factory.py`**: Automatically connects to PostgreSQL + `pgvector` if `DATABASE_URL` is configured, or seamlessly falls back to `LocalVectorStore`.

### Hybrid Retrieval & Reranking (`app/search.py`)
- Blends dense vector search scores with sparse BM25 keyword matching via Reciprocal Rank Fusion.
- Enforces all **10 structured metadata filters**:
  1. Category (7 categories)
  2. Government level (Central / State)
  3. State (Haryana, Maharashtra, Punjab, West Bengal, Telangana, UP, Rajasthan, Karnataka, Bihar)
  4. District (Rewari, Ambala, Hisar, Pune, Amritsar, Kolkata, etc.)
  5. Beneficiary (Farmer, Student, Woman, Senior Citizen, Entrepreneur, Artisan)
  6. Age group (Under 18, 18-25, 26-40, 41-60, 60+)
  7. Family income (1L, 1.8L, 2.5L, 5L, 8L)
  8. Social category (General, SC, ST, OBC, EWS)
  9. Benefit type (Grant, Subsidy, Loan, Pension, Insurance, Scholarship)
  10. Application status (Open, Year-round, Seasonal, Closed, Needs verification)
- Reranks results using semantic relevance, intent match, and eligibility weighting.

### Deterministic Eligibility Rule Engine (`app/eligibility.py`)
*Rules decide eligibility, never the AI model.*
Computes and returns **3 separate structured indicators**:
1. **Eligibility Match**:
   - Verdict: `meets_listed_conditions` / `possibly_eligible` / `not_eligible`
   - Matched, pending, and failed condition counts
   - Detailed condition breakdown (unknown conditions remain pending, never assumed satisfied).
2. **Benefit Details**:
   - Benefit amount (₹), payment frequency, benefit type, and repayment obligation status.
3. **Document Readiness**:
   - Evaluates applicant's documents against scheme requirements.
   - Outputs: available documents, missing documents, readiness percentage, and status (`ready` / `partially_ready` / `needs_documents`).

### Context Builder & RAG Pipeline (`app/rag.py`)
- Aggregates top retrieved chunks from official documents with full citation metadata (Document title, section heading, page number, official PDF link, official portal URL).
- Synthesizes grounded answers in the requested language (English, Hindi, Marathi, Punjabi, Telugu, Bengali).
- Seamlessly connects to Gemini API when `GEMINI_API_KEY` is configured, with a high-fidelity deterministic grounded generation fallback.

---

## 3. Quick Start & Execution

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run all 41 automated tests
python -m pytest

# 3. Run Multilingual NLP & RAG Benchmark Evaluation
python scripts/evaluate_nlp.py

# 4. Start FastAPI server & Interactive Dashboard
uvicorn app.main:app --reload
```
Open **`http://localhost:8000`** in your browser.

---

## 4. API Endpoints

- `POST /search`: Multilingual hybrid RAG search with 10 filter controls, sorting, retrieved guideline chunks, and 3 eligibility indicators.
- `POST /rag/answer`: Full document-based RAG answer generation with official citations and deterministic eligibility evaluation.
- `POST /rag/retrieve`: Direct hybrid chunk retrieval over official government guideline documents.
- `POST /eligibility/evaluate`: Deterministic rule evaluation returning the 3 indicators.
- `GET /rag/stats`: Vector store and document ingestion metrics.
- `GET /schemes`: Scheme catalog with filters and localization.
- `GET /schemes/{id}`: Detailed scheme metadata and 6-language translations.
- `POST /explain`: Grounded explanation for a single scheme with citations.
- `GET /languages`: Supported 6 Indic languages.
- `GET /categories`: 7 scheme categories taxonomy.

---

## 5. Evaluation Benchmark Results

Ran across 36 ground-truth multilingual queries covering all 6 languages and 7 categories:
- **Language Detection Accuracy**: 97.22%
- **Intent / Category Detection Macro-F1**: 94.55%
- **NER / Profile Extraction Accuracy**: 95.00%
- **Hybrid Search Recall@5**: 100.00%
- **Search Precision@5**: 87.36%
- **Official Citation Coverage**: 100.00%
- **Average Latency per Query**: 9.89 ms
