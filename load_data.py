"""Create cell-count.db from cell-count.csv using the schema in schema.sql."""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
SCHEMA_PATH = ROOT / "schema.sql"
DB_PATH = ROOT / "cell-count.db"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def lookup_id(db, table, name):
    """Return the id of `name` in a lookup table, inserting it if it's new."""
    db.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (name,))
    return db.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()[0]


def load_row(db, row, population_ids):
    db.execute(
        "INSERT OR IGNORE INTO subject (name, project_id, condition_id, age, sex) VALUES (?, ?, ?, ?, ?)",
        (
            row["subject"],
            lookup_id(db, "project", row["project"]),
            lookup_id(db, "condition", row["condition"]),
            int(row["age"]),
            row["sex"],
        ),
    )
    subject_id = db.execute("SELECT id FROM subject WHERE name = ?", (row["subject"],)).fetchone()[0]

    treatment_id = lookup_id(db, "treatment", row["treatment"])
    db.execute(
        "INSERT OR IGNORE INTO subject_treatment (subject_id, treatment_id, response) VALUES (?, ?, ?)",
        (subject_id, treatment_id, row["response"] or None),
    )
    subject_treatment_id = db.execute(
        "SELECT id FROM subject_treatment WHERE subject_id = ? AND treatment_id = ?",
        (subject_id, treatment_id),
    ).fetchone()[0]

    sample_id = db.execute(
        "INSERT INTO sample (name, subject_treatment_id, sample_type_id, time_from_treatment_start) VALUES (?, ?, ?, ?)",
        (
            row["sample"],
            subject_treatment_id,
            lookup_id(db, "sample_type", row["sample_type"]),
            int(row["time_from_treatment_start"]),
        ),
    ).lastrowid

    db.executemany(
        "INSERT INTO cell_count (sample_id, population_id, count) VALUES (?, ?, ?)",
        [(sample_id, population_ids[p], int(row[p])) for p in POPULATIONS],
    )


def main():
    DB_PATH.unlink(missing_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA_PATH.read_text())

    population_ids = {p: lookup_id(db, "population", p) for p in POPULATIONS}
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            load_row(db, row, population_ids)

    db.commit()
    n_samples = db.execute("SELECT COUNT(*) FROM sample").fetchone()[0]
    db.close()
    print(f"Loaded {n_samples} samples into {DB_PATH.name}")


if __name__ == "__main__":
    main()
