import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Data (manually reconstructed from your table)
# -----------------------------
data = [
    # threshold, placement, energy
    ("0-30", "CPU_BFD", 69933.153194),
    ("0-30", "Power_BFD", 71097.241678),

    ("10-30", "CPU_BFD", 71915.725065),
    ("10-30", "Power_BFD", 71697.565361),

    ("20-30", "CPU_BFD", 71916.371833),
    ("20-30", "Power_BFD", 71806.922047),

    ("10-90", "CPU_BFD", 72204.396809),
    ("10-90", "Power_BFD", 72251.188055),

    ("20-90", "CPU_BFD", 72146.217376),
    ("20-90", "Power_BFD", 72334.206360),
]

df = pd.DataFrame(data, columns=["threshold", "placement", "energy"])

# enforce ordering
order = ["0-30", "10-30", "20-30", "10-90", "20-90"]
df["threshold"] = pd.Categorical(df["threshold"], categories=order, ordered=True)

# -----------------------------
# Plot
# -----------------------------
sns.set_style("whitegrid")

plt.figure(figsize=(9, 5))

sns.lineplot(
    data=df,
    x="threshold",
    y="energy",
    hue="placement",        # keeps legend separation
    style="placement",      # DIFFERENT line styles
    markers=True,           # enables markers
    dashes=True,            # ensures line styles differ
    palette=["black", "black"],  # SAME color for both lines
    markersize=7
)

# Baseline reference line
#plt.axhline(y=115.39, linestyle="--", color="gray", label="Baseline")
plt.ylim(69000, 73000)

#plt.title("Total Energy Consumption Across VM Consolidation Thresholds")
plt.xlabel("Threshold Range (%)")
plt.ylabel("Total Energy (KWh)")

plt.legend(title="Placement Strategy")
plt.tight_layout()

plt.savefig("energy_consumption_difference.png", dpi=300, bbox_inches="tight")
plt.show()


'''
Tradeoff plot

x-axis:

migrations

y-axis:

energy savings.

VERY good plot.
'''