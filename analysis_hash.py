import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

df = pd.read_csv("hash_results.csv")
df["log_throughput"] = np.log(df["throughput_mb_s"])
df["size_label"] = df["size_bytes"].astype(str)

print("rows:", len(df), "| algorithms:", df["algorithm"].nunique(), "| sizes:", df["size_bytes"].nunique())
print("runs per cell:", df.groupby(["algorithm", "size_bytes"]).size().unique())

print()
print("PART A: one-way ANOVA at 1 MB (throughput MB/s)")
sub = df[df["size_bytes"] == 1_000_000]
groups = [g["throughput_mb_s"].values for _, g in sub.groupby("algorithm")]
f, p = stats.f_oneway(*groups)
print("F = %.1f, p = %.3g" % (f, p))
print("Levene (equal variances): p = %.3g" % stats.levene(*groups).pvalue)
print("Kruskal-Wallis (rank-based check): p = %.3g" % stats.kruskal(*groups).pvalue)
print(pairwise_tukeyhsd(sub["throughput_mb_s"], sub["algorithm"]))

print()
print("PART B: two-way ANOVA, algorithm x size, on log(throughput)")
model = smf.ols("log_throughput ~ C(algorithm) * C(size_label)", data=df).fit()
table = sm.stats.anova_lm(model, typ=2)
table["eta_sq"] = table["sum_sq"] / table["sum_sq"].sum()
print(table.to_string(float_format=lambda x: "%.4g" % x))
print("Shapiro-Wilk on residuals: p = %.3g" % stats.shapiro(model.resid).pvalue)
cells = [g["log_throughput"].values for _, g in df.groupby(["algorithm", "size_bytes"])]
print("Levene across all cells: p = %.3g" % stats.levene(*cells).pvalue)
