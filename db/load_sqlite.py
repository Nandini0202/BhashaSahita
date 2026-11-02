"""Load data/schemes_seed.json and data/scheme_translations.json into SQLite (dev DB).
PostgreSQL schema is in schema.sql; same columns, JSON stored as text here.
Usage: python -m db.load_sqlite [db_path]
"""
import json, sqlite3, sys
from pathlib import Path

JSON_COLS = ["tags", "conditions", "documents", "verification"]
COLS = ["id", "name_en", "category", "level", "state", "ministry", "launch_year", "purpose", "benefit_type",
        "max_benefit_amount", "benefit_frequency", "repayment_required", "status", "official_url",
        "official_pdf_url", "verified", "last_verified"] + JSON_COLS

def load(db_path=":memory:", json_path=None):
    base_dir = Path(__file__).parent.parent
    json_path = json_path or base_dir / "data" / "schemes_seed.json"
    trans_path = base_dir / "data" / "scheme_translations.json"

    schemes = json.loads(Path(json_path).read_text(encoding="utf-8"))
    con = sqlite3.connect(db_path)
    
    # 1. Schemes table
    con.execute(f"CREATE TABLE IF NOT EXISTS schemes ({', '.join(COLS)}, PRIMARY KEY (id))".replace(", PRIMARY KEY (id)", "").replace("id,", "id PRIMARY KEY,", 1))
    con.execute("DELETE FROM schemes")
    for s in schemes:
        row = [json.dumps(s.get(c), ensure_ascii=False) if c in JSON_COLS else s.get(c) for c in COLS]
        con.execute(f"INSERT INTO schemes VALUES ({','.join('?' * len(COLS))})", row)

    # 2. Scheme translations table
    con.execute("""
    CREATE TABLE IF NOT EXISTS scheme_translations (
        scheme_id TEXT,
        lang TEXT,
        name TEXT,
        purpose TEXT,
        simplified_text TEXT,
        human_validated BOOLEAN DEFAULT FALSE,
        PRIMARY KEY (scheme_id, lang)
    )
    """)
    con.execute("DELETE FROM scheme_translations")

    if trans_path.exists():
        trans_data = json.loads(trans_path.read_text(encoding="utf-8"))
        rows = []
        for sid, langs in trans_data.items():
            for lcode, item in langs.items():
                rows.append((
                    sid,
                    lcode,
                    item.get("name", ""),
                    item.get("purpose", ""),
                    item.get("simplified_text", ""),
                    1 if item.get("human_validated") else 0
                ))
        con.executemany("INSERT INTO scheme_translations VALUES (?, ?, ?, ?, ?, ?)", rows)

    con.commit()
    return con

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "bhasha.db"
    c = load(out)
    sch_count, ver_count = c.execute("select count(*), sum(verified) from schemes").fetchone()
    tr_count = c.execute("select count(*) from scheme_translations").fetchone()[0]
    print(f"Loaded {out}: {sch_count} schemes ({ver_count} verified), {tr_count} translations.")
