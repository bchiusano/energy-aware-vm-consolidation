import pandas as pd
import matplotlib.pyplot as plt
# Pareto optimality analysis: environmental impact vs migration fairness
data = [
    # threshold, strategy, energy_reduction_pct, carbon_reduction_pct, water_reduction_pct, gini_norm, jain_norm
    ("0-25",  "PowerBFD", 4.21, 6.65, 6.38, 0.95, 0.05),
    ("0-25",  "CPUBFD",   3.94, 6.39, 6.13, 0.95, 0.05),
    ("0-30",  "PowerBFD", 3.69, 6.16, 5.86, 0.97, 0.04),
    ("0-30",  "CPUBFD",   3.42, 5.89, 5.60, 0.97, 0.04),
    ("5-25",  "PowerBFD", 3.74, 5.80, 5.94, 0.56, 0.47),
    ("5-25",  "CPUBFD",   3.95, 5.96, 6.13, 0.58, 0.44),
    ("5-30",  "PowerBFD", 4.32, 6.40, 6.54, 0.54, 0.49),
    ("5-30",  "CPUBFD",   4.50, 6.53, 6.70, 0.56, 0.46),
    ("10-25", "PowerBFD", 1.83, 4.03, 4.11, 0.60, 0.43),
    ("10-25", "CPUBFD",   1.91, 4.09, 4.20, 0.62, 0.41),
    ("10-30", "PowerBFD", 2.26, 4.47, 4.55, 0.59, 0.44),
    ("10-30", "CPUBFD",   2.34, 4.51, 4.62, 0.60, 0.43),
]

df = pd.DataFrame(
    data,
    columns=[
        "threshold", "strategy", "energy_reduction_pct", "carbon_reduction_pct",
        "water_reduction_pct", "gini_norm", "jain_norm",
    ],
)
df["fairness"] = 1 - df["gini_norm"]  # higher = fairer, easier to reason about alongside reductions
df["config"] = df["threshold"] + " / " + df["strategy"]


def is_dominated(row, others, objective_cols):
    # Returns True if `row` is dominated by any row in `others`:
    for _, other in others.iterrows():
        if other.name == row.name:
            continue
        at_least_as_good = all(other[c] >= row[c] for c in objective_cols)
        strictly_better = any(other[c] > row[c] for c in objective_cols)
        if at_least_as_good and strictly_better:
            return True
    return False


def pareto_front(df, objective_cols):
    # Returns a copy of df with an added boolean column 'pareto_optimal'
    df = df.copy()
    df["pareto_optimal"] = ~df.apply(lambda row: is_dominated(row, df, objective_cols), axis=1)
    return df


def plot_pareto_2d(df, x_col, y_col, x_label, y_label, title, filename=None):
    # 2D Pareto plot
    fig, ax = plt.subplots(figsize=(7, 6))

    dominated = df[~df["pareto_optimal"]]
    frontier = df[df["pareto_optimal"]].sort_values(x_col)

    ax.scatter(dominated[x_col], dominated[y_col], color="gray", alpha=0.6, label="Dominated")
    ax.scatter(frontier[x_col], frontier[y_col], color="crimson", s=70, zorder=3, label="Pareto-optimal")
    ax.plot(frontier[x_col], frontier[y_col], color="crimson", linestyle="--", alpha=0.6, zorder=2)

    for _, row in df.iterrows():
        ax.annotate(
            row["config"],
            (row[x_col], row[y_col]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()

    if filename:
        plt.savefig(filename, dpi=300, bbox_inches="tight")

    plt.show()


if __name__ == "__main__":

    full_objectives = ["energy_reduction_pct", "carbon_reduction_pct", "water_reduction_pct", "fairness"]
    df_full = pareto_front(df, full_objectives)

    print("=== Full multi-objective Pareto front (energy, carbon, water, fairness) ===")
    print(df_full[["config"] + full_objectives + ["pareto_optimal"]].to_string(index=False))
    print(f"\nPareto-optimal configurations: {df_full[df_full['pareto_optimal']]['config'].tolist()}")

    df_2d = pareto_front(df, ["energy_reduction_pct", "fairness"])
    plot_pareto_2d(
        df_2d,
        x_col="energy_reduction_pct",
        y_col="fairness",
        x_label="Energy reduction vs Baseline 2 (%)",
        y_label="Fairness (1 - normalised Gini)",
        title="Pareto frontier: Energy reduction vs Migration fairness",
        # filename="pareto_energy_fairness.png",
    )

    # Sanity check: does the 2D frontier match the full 4-objective frontier?
    print("\n2D (energy vs fairness) Pareto-optimal:", df_2d[df_2d["pareto_optimal"]]["config"].tolist())
    print("Full 4-objective Pareto-optimal:       ", df_full[df_full["pareto_optimal"]]["config"].tolist())