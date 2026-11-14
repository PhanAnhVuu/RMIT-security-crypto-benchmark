import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

df = pd.read_csv("asymmetric_results.csv")
df["time_us"] = df["time_s"] * 1_000_000
df["log_time"] = np.log(df["time_us"])
print("rows:", len(df), "| runs per cell:", df.groupby(["algorithm", "operation"]).size().unique())

print()
print("Mean time (microseconds) and coefficient of variation (std / mean):")
summary = df.groupby(["operation", "algorithm"])["time_us"].agg(["mean", "std"])
summary["cv"] = summary["std"] / summary["mean"]
print(summary.round(2))

for op in ["keygen", "sign", "verify"]:
    sub = df[df["operation"] == op]
    groups = [g["log_time"].values for _, g in sub.groupby("algorithm")]
    f, p = stats.f_oneway(*groups)
    print()
    print("ONE-WAY ANOVA on log(time):", op)
    print("F = %.1f, p = %.3g" % (f, p))
    print("Levene p = %.3g | Kruskal-Wallis p = %.3g" % (stats.levene(*groups).pvalue, stats.kruskal(*groups).pvalue))
    print(pairwise_tukeyhsd(sub["log_time"], sub["algorithm"]))

print()
print("TWO-WAY ANOVA: algorithm x operation on log(time)")
model = smf.ols("log_time ~ C(algorithm) * C(operation)", data=df).fit()
table = sm.stats.anova_lm(model, typ=2)
table["eta_sq"] = table["sum_sq"] / table["sum_sq"].sum()
print(table.to_string(float_format=lambda x: "%.4g" % x))
print("Shapiro-Wilk on residuals: p = %.3g" % stats.shapiro(model.resid).pvalue)
cells = [g["log_time"].values for _, g in df.groupby(["algorithm", "operation"])]
print("Levene across all cells: p = %.3g" % stats.levene(*cells).pvalue)
