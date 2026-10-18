"""Create cell-count.db from cell-count.csv using the schema in schema.sql."""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
SCHEMA_PATH = ROOT / "schema.sql"
DB_PATH = ROOT / "cell-count.db"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
# CSV columns that each have a lookup table of the same name
LOOKUP_COLUMNS = ["project", "condition", "treatment", "sample_type"]


def load_row(db, row):
    for column in LOOKUP_COLUMNS:
        db.execute(f"INSERT OR IGNORE INTO {column} (name) VALUES (?)", (row[column],))

    db.execute(
        "INSERT OR IGNORE INTO subject (name, project, condition, age, sex) VALUES (?, ?, ?, ?, ?)",
        (row["subject"], row["project"], row["condition"], int(row["age"]), row["sex"]),
    )
    subject_id = db.execute("SELECT id FROM subject WHERE name = ?", (row["subject"],)).fetchone()[0]

    db.execute(
        "INSERT OR IGNORE INTO subject_treatment (subject_id, treatment, response) VALUES (?, ?, ?)",
        (subject_id, row["treatment"], row["response"] or None),
    )
    subject_treatment_id = db.execute(
        "SELECT id FROM subject_treatment WHERE subject_id = ? AND treatment = ?",
        (subject_id, row["treatment"]),
    ).fetchone()[0]

    sample_id = db.execute(
        "INSERT INTO sample (name, subject_treatment_id, sample_type, time_from_treatment_start) VALUES (?, ?, ?, ?)",
        (row["sample"], subject_treatment_id, row["sample_type"], int(row["time_from_treatment_start"])),
    ).lastrowid

    db.executemany(
        "INSERT INTO cell_count (sample_id, population, count) VALUES (?, ?, ?)",
        [(sample_id, p, int(row[p])) for p in POPULATIONS],
    )


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"{CSV_PATH.name} not found: copy it into {ROOT}")
    DB_PATH.unlink(missing_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA_PATH.read_text())

    db.executemany("INSERT INTO population (name) VALUES (?)", [(p,) for p in POPULATIONS])
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            load_row(db, row)

    db.commit()
    n_samples = db.execute("SELECT COUNT(*) FROM sample").fetchone()[0]
    db.close()
    print(f"Loaded {n_samples} samples into {DB_PATH.name}")


if __name__ == "__main__":
    main()
