-- PostgreSQL schema for BHASHA SAHITA (Phase 2 loads data/schemes_seed.json into this)
CREATE TABLE schemes (
  id TEXT PRIMARY KEY,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL,
  subcategory TEXT,
  tags TEXT[],
  level TEXT CHECK (level IN ('Central','State')),
  state TEXT,
  ministry TEXT,
  launch_year INT,
  purpose TEXT,
  beneficiary TEXT[],
  benefit_type TEXT,
  max_benefit_amount NUMERIC,
  benefit_frequency TEXT,
  repayment_required BOOLEAN,
  conditions JSONB,
  documents TEXT[],
  application_procedure TEXT,
  application_start DATE,
  application_end DATE,
  status TEXT,
  official_url TEXT,
  official_pdf_url TEXT,
  verified BOOLEAN DEFAULT FALSE,
  last_verified DATE,
  updated_at TIMESTAMP DEFAULT now()
);
CREATE TABLE scheme_translations (
  scheme_id TEXT REFERENCES schemes(id),
  lang TEXT CHECK (lang IN ('en','hi','mr','pa','te','bn')),
  name TEXT, purpose TEXT, simplified_text TEXT,
  human_validated BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (scheme_id, lang)
);
