# BHASHA SAHITA (भाषा सहिता)
Multilingual Government Scheme Discovery & Verified Eligibility Engine.
Supports 6 languages (English, हिन्दी, मराठी, ਪੰਜਾਬੀ, తెలుగు, বাংলা), 100 verified schemes across Central and 9 States, 10 filter controls, and source-grounded explanations.

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run all 33 automated tests
python -m pytest -q

# 3. Run NLP & Multilingual Evaluation Benchmark
python scripts/evaluate_nlp.py

# 4. Load dataset & translations into SQLite dev database
python -m db.load_sqlite bhasha.db

# 5. Start web server & interactive dashboard
uvicorn app.main:app --reload
```
Open **`http://localhost:8000`** in your browser to view the interactive web dashboard.

## Key Features
1. **100 Verified Schemes**: 50 Central Government and 50 State Government schemes (covering Haryana, Maharashtra, Punjab, West Bengal, Telangana, Uttar Pradesh, Rajasthan, Karnataka, Bihar) across all 7 categories:
   - Education & Scholarships (16 schemes)
   - Agriculture & Farmers (16 schemes)
   - Women & Child Welfare (20 schemes)
   - Business & Entrepreneurship (11 schemes)
   - Healthcare & Insurance (12 schemes)
   - Housing & Basic Needs (9 schemes)
   - Employment, Pension & Social Security (16 schemes)
2. **6-Language Multilingual Support**: English, Hindi, Marathi, Punjabi, Telugu, and Bengali. Full scheme translations, localized categories, and NFC Unicode normalization.
3. **10 Interactive Filter Controls**:
   - Category (7 categories)
   - Government Level (Central / State)
   - State / UT (Haryana, Maharashtra, Punjab, West Bengal, Telangana, UP, Rajasthan, Karnataka, Bihar)
   - Beneficiary (Student, Farmer, Woman, Senior Citizen, Entrepreneur, Artisan)
   - Age Group (Under 18, 18-25, 26-40, 41-60, 60+)
   - Family Income ceiling (1L, 1.8L, 2.5L, 5L, 8L)
   - Social Category (General, SC, ST, OBC, EWS)
   - Benefit Type (Grant, Subsidy, Loan, Pension, Insurance, Scholarship)
   - Application Status (Open, Year-round, Seasonal, Closed, Needs verification)
   - District Filter
4. **3 Visual Indicators per Scheme**:
   - **Eligibility Match**: Detailed condition count (e.g. 3/3 matched, 2/3 pending, or ineligible condition)
   - **Financial Benefit**: ₹ amount, payment frequency, and grant/loan/subsidy indicator
   - **Document Readiness**: Required documents checklist and pending documents counter
5. **RAG & Grounded AI Explanations**: Contextual Q&A over official guidelines (`/explain`). Strictly follows the rule: *Rules decide eligibility, never the LLM.*
6. **High Performance**: Sub-3ms query latency, 97.2% language detection accuracy, 94.6% intent macro-F1, and 91.7% Recall@5.

## Project Structure
- `app/`:
  - `main.py`: FastAPI server serving web dashboard (`/`) and REST APIs (`/search`, `/schemes`, `/explain`, `/languages`, `/categories`)
  - `search.py`: Search engine with tokenization, cross-lingual scoring, 10 filters, and sorting
  - `eligibility.py`: Deterministic rule engine evaluating eligibility (`any_of`, `between`, `lte`, `gte`, `in`, `eq`)
  - `language.py`: 6-language script & functional marker detector with NFC normalization
  - `nlp.py`: Multilingual intent category detection and profile/entity extraction
  - `i18n.py`: Multilingual translations and localization engine
  - `rag.py`: Source-grounded explanation engine citing official portals and guidelines
  - `validate.py`: Data-quality and release validator (`validate` and `validate_strict`)
  - `static/index.html`: Modern, responsive HTML5 + Tailwind web dashboard
- `data/`:
  - `schemes_seed.json`: Canonical dataset of 100 verified schemes
  - `scheme_translations.json`: 600 translations across 6 languages
  - `VERIFICATION_LOG.md`: Verification log and source citations for all 100 schemes
- `db/`:
  - `schema.sql`: PostgreSQL schema definitions
  - `load_sqlite.py`: Dev SQLite database loader
- `tests/`:
  - `test_core.py`: Baseline NLP and eligibility tests
  - `test_phase2.py`: Initial schemes and rules tests
  - `test_phase2d.py`: 40 schemes expansion and strict validation tests
  - `test_full_project.py`: Complete project tests (100 schemes, 10 filters, RAG, FastAPI)
  - `test_evaluation_benchmark.py`: NLP evaluation benchmark automated test
- `scripts/`:
  - `build_full_dataset.py`: Dataset expansion and validator script
  - `build_translations.py`: 6-language translations generator
  - `evaluate_nlp.py`: Multilingual benchmark evaluation suite
