# serves frontend/ and the analysis results as json
import sqlite3
from contextlib import closing

from flask import Flask, jsonify

import analysis

PORT = 8000

app = Flask(__name__, static_folder="frontend", static_url_path="")


def connect():
    return closing(sqlite3.connect(analysis.DB_PATH))


@app.get("/")
def index():
    return app.send_static_file("index.html")

#pt 2
@app.get("/api/frequencies")
def frequencies():
    with connect() as db:
        return jsonify(analysis.frequency_table(db).to_dict(orient="records"))

#pt 3
@app.get("/api/responders")
def responders():
    with connect() as db:
        per_subject, results = analysis.responder_comparison(db)
    return jsonify(per_subject=per_subject.to_dict(orient="records"), results=results.to_dict(orient="records"))

#pt 4
@app.get("/api/baseline")
def baseline():
    with connect() as db:
        samples = analysis.baseline_samples(db)["sample"].tolist()
        summary = analysis.baseline_summary(db).reset_index().to_dict(orient="records")
        mean_b_cells = analysis.mean_baseline_b_cells(db)
    return jsonify(samples=samples, summary=summary, mean_b_cells=round(mean_b_cells, 2))


if __name__ == "__main__":
    if not analysis.DB_PATH.exists():
        raise SystemExit(f"{analysis.DB_PATH.name} not found: run make pipeline first")
    app.run(port=PORT)
