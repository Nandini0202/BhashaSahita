# BHASHA SAHITA - Phase Plan & Project Status

Scope: 6 languages (en, hi, mr, pa, te, bn), 7 categories, 10 filters, 100 verified schemes (Central + 9 States),
hybrid NLP + rule engine + RAG + LLM. Rules decide eligibility, never the LLM.

| Phase | Work | Status |
|---|---|---|
| 1 | Skeleton, DB schema, language detection (6 langs), multilingual category lexicon, profile extraction, eligibility engine, FastAPI `/search` + `/schemes` | DONE |
| 2 | Data: first 16 schemes checked on 2 Nov 2026, `any_of` eligibility rules, dataset validator, status/date fields, SQLite loader, 15 tests | DONE (16 schemes) |
| 2d | Dataset grown 16 -> 40 schemes (28 Central, 8 Haryana, 4 Maharashtra; all 7 categories). 19 web_verified, 21 partially_verified. Lado Lakshmi income limit resolved (Rs 1.8 lakh). `validate_strict` added, 24 tests | DONE (40 schemes) |
| 2e | Dataset expanded 40 -> 100 schemes: added Central (Startup India, CGTMSE, Jal Jeevan, SBM-G, PM POSHAN, AIF, etc.) and state schemes for Haryana (Vivah Shagun, Bhavantar), Maharashtra (EBC Concession, CMEGP, Ramai Awas), Punjab (Ashirwad, Sehat Bima, Old Age), West Bengal (Lakshmir Bhandar, Kanyashree, Swasthya Sathi, Krishak Bandhu), Telangana (Rythu Bharosa, Kalyana Lakshmi, Aarogyasri), Uttar Pradesh, Rajasthan, Karnataka, Bihar; official PDF URLs integrated. | DONE (100 schemes) |
| 3 | Translations: six-language names/purposes (en, hi, mr, pa, te, bn), `data/scheme_translations.json`, `app/i18n.py`, `human_validated` flag; NFC Unicode normalization, expanded multilingual lexicons & stopwords | DONE |
| 4 | Search: BM25/token scoring + multilingual matching, 10 filters (Category, Level, State, District, Beneficiary, Age Group, Income, Social Category, Benefit Type, Status), 4 sorting modes, 3 visual indicators | DONE |
| 5 | RAG: `app/rag.py` contextual explanation engine, official PDF citations, Gemini API integration + deterministic offline fallback; rules decide eligibility | DONE |
| 6 | Frontend: Interactive responsive web dashboard (`app/static/index.html`) served at `/`, 6-language switcher, category cards, 10 filters, 3 visual indicators (Eligibility, Benefit, Documents), AI Explain modal | DONE |
| 7 | Evaluation & Deploy: Multilingual benchmark test set across 6 languages, Language Acc: 97.22%, Category F1: 94.55%, NER Acc: 95.00%, Recall@5: 91.67%, Latency: 2.32 ms, 33 automated tests passing | DONE |

## Key data findings (2 Nov 2026) the app respects
- MGNREGA was replaced by VB-G RAM G on 1 July 2026 (125 days).
- PM-JAY covers everyone aged 70+ regardless of income (Vay Vandana).
- PM Mudra limit is Rs 20 lakh (Tarun Plus only for borrowers who repaid a Tarun loan).
- NSP 2026-27 post-matric deadline (31 Oct 2026) has passed unless extended; status is `closed_check_extension`.
- Haryana: Old Age Samman Allowance is Rs 3,200/month; Chirayu now has paid tiers for incomes above Rs 1.8 lakh (from 1 Nov 2026);
  Lado Lakshmi pays Rs 2,100/month split Rs 1,100 cash + Rs 1,000 deposit; Vivah Shagun pays up to Rs 71,000.
- West Bengal: Lakshmir Bhandar enhanced to Rs 1,200/month (SC/ST) and Rs 1,000/month (General/OBC); Swasthya Sathi provides Rs 5 lakh universal cashless cover.
- Telangana: Rythu Bharosa investment support is Rs 15,000/acre/year; Aarogyasri limit enhanced to Rs 10 lakh.
- Maharashtra: Majhi Ladki Bahin provides Rs 1,500/month; CMEGP provides up to 35% margin money subsidy.
- Punjab: Ashirwad Shagun grant is Rs 51,000; free bus travel for women across state roadways.
- Rates (e.g. Sukanya interest) change quarterly: show the date, never hard-code in generated answers.

## Evaluation Benchmark Results (Phase 7)
- Language Detection Accuracy: **97.22%** (35/36 across English, Hindi, Marathi, Punjabi, Telugu, Bengali)
- Intent / Category Classification Macro-F1: **94.55%**
- NER / Profile Extraction Accuracy: **95.00%**
- Search Recall@5: **91.67%**
- Search Precision@5: **77.22%**
- Query Latency: **2.32 ms** average
- Automated Pytest Suite: **33 passed in 0.8s**
