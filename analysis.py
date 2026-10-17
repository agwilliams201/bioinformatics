# pts 2-4
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "cell-count.db"
OUTPUT_DIR = ROOT / "outputs"
RESPONSE_GROUPS = {"yes": ("Responders", "#2a78d6"), "no": ("Non-responders", "#eb6834")}

FREQUENCY_SQL = """
SELECT s.name AS sample,
       SUM(c.count) OVER (PARTITION BY c.sample_id) AS total_count,
       p.name AS population,
       c.count,
       100.0 * c.count / SUM(c.count) OVER (PARTITION BY c.sample_id) AS percentage
FROM cell_count c
JOIN sample s ON s.id = c.sample_id
JOIN population p ON p.id = c.population_id
ORDER BY c.sample_id, c.population_id
"""

#recapitulate csv rows basically
SAMPLE_SQL = """
SELECT s.name AS sample, su.name AS subject, pr.name AS project, co.name AS condition,
       su.sex, t.name AS treatment, st.response, ty.name AS sample_type,
       s.time_from_treatment_start
FROM sample s
JOIN sample_type ty ON ty.id = s.sample_type_id
JOIN subject_treatment st ON st.id = s.subject_treatment_id
JOIN treatment t ON t.id = st.treatment_id
JOIN subject su ON su.id = st.subject_id
JOIN project pr ON pr.id = su.project_id
JOIN condition co ON co.id = su.condition_id
"""

MELANOMA_MIRACLIB_PBMC = "condition = 'melanoma' AND treatment = 'miraclib' AND sample_type = 'PBMC'"

#pt 2
def frequency_table(db):
    return pd.read_sql(FREQUENCY_SQL, db)


def query_samples(db, where):
    return pd.read_sql(f"SELECT * FROM ({SAMPLE_SQL}) WHERE {where}", db)

#pt 3
def responder_comparison(db, frequencies):
    samples = query_samples(db, MELANOMA_MIRACLIB_PBMC)
    # take avg bc 3 visits
    per_subject = (
        frequencies.merge(samples, on="sample")
        .groupby(["subject", "response", "population"], as_index=False, sort=False)["percentage"]
        .mean()
    )

    results = []
    for population, group in per_subject.groupby("population", sort=False):
        responders = group.loc[group.response == "yes", "percentage"]
        non_responders = group.loc[group.response == "no", "percentage"]
        results.append({
            "population": population,
            "responder_mean": responders.mean(),
            "non_responder_mean": non_responders.mean(),
            "p_value": stats.ttest_ind(responders, non_responders, equal_var=False).pvalue,
        })
    results = pd.DataFrame(results)
    results["adjusted_p_value"] = stats.false_discovery_control(results.p_value)
    results["significant"] = results.adjusted_p_value < 0.05
    return per_subject, results


def plot_responder_boxplots(per_subject, results, path):
    fig, axes = plt.subplots(1, len(results), figsize=(3 * len(results), 4.5), facecolor="#fcfcfb")
    for ax, row in zip(axes, results.itertuples()):
        group = per_subject[per_subject.population == row.population]
        boxes = ax.boxplot(
            [group.loc[group.response == r, "percentage"] for r in RESPONSE_GROUPS],
            tick_labels=[label for label, _ in RESPONSE_GROUPS.values()],
            patch_artist=True,
            widths=0.6,
            medianprops={"color": "#0b0b0b"},
            flierprops={"markersize": 3, "markeredgecolor": "#898781"},
        )
        for box, (_, color) in zip(boxes["boxes"], RESPONSE_GROUPS.values()):
            box.set(facecolor=color, alpha=0.8, edgecolor=color)
        ax.set_title(f"{row.population}\nadjusted p = {row.adjusted_p_value:.2g}", fontsize=10)
        ax.set_facecolor("#fcfcfb")
        ax.grid(axis="y", color="#e1e0d9", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Relative frequency, mean per subject (%)")
    fig.suptitle("Melanoma, miraclib, PBMC: responders vs non-responders")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)

#pt 4
def baseline_summary(db):
    baseline = query_samples(db, f"{MELANOMA_MIRACLIB_PBMC} AND time_from_treatment_start = 0")
    return {
        "Samples per project": baseline.groupby("project").size(),
        "Subjects per response": baseline.groupby("response").subject.nunique(),
        "Subjects per sex": baseline.groupby("sex").subject.nunique(),
    }


def mean_baseline_b_cells(db, frequencies):
    samples = query_samples(db, "condition = 'melanoma' AND sex = 'M' AND response = 'yes' AND time_from_treatment_start = 0")
    b_cells = frequencies[frequencies.population == "b_cell"].merge(samples, on="sample")
    return b_cells["count"].mean()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH)

    frequencies = frequency_table(db)
    frequencies.to_csv(OUTPUT_DIR / "frequencies.csv", index=False)
    print("Part 2: relative frequency of each population in each sample")
    print(frequencies.head(10).to_string(index=False, float_format="%.2f"))
    print(f"... {len(frequencies)} rows, saved to outputs/frequencies.csv\n")

    per_subject, results = responder_comparison(db, frequencies)
    results.to_csv(OUTPUT_DIR / "responder_comparison.csv", index=False)
    plot_responder_boxplots(per_subject, results, OUTPUT_DIR / "responder_boxplots.png")
    print("Part 3: melanoma/miraclib PBMC responders vs non-responders (mean % per subject, Welch's t-test)")
    print(results.to_string(index=False, float_format="%.4g"))
    significant = results.loc[results.significant, "population"].tolist()
    print(f"Significant at adjusted p < 0.05: {', '.join(significant) or 'none'}")
    print("Saved to outputs/responder_comparison.csv and outputs/responder_boxplots.png\n")

    print("Part 4: melanoma PBMC samples at baseline from miraclib-treated subjects")
    for title, counts in baseline_summary(db).items():
        print(f"{title}: {counts.to_dict()}")
    print(f"Mean B cells, melanoma male responders at baseline: {mean_baseline_b_cells(db, frequencies):.2f}")
    db.close()


if __name__ == "__main__":
    main()
