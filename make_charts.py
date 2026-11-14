import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
SIZE_LABELS = {1_000: "1 KB", 100_000: "100 KB", 1_000_000: "1 MB", 10_000_000: "10 MB", 100_000_000: "100 MB"}
NAMES = {
    "md5": "MD5", "sha1": "SHA-1", "sha256": "SHA-256", "sha3_256": "SHA3-256",
    "3des_cbc": "3DES-CBC", "aes256_gcm": "AES-256-GCM", "chacha20_poly1305": "ChaCha20-Poly1305",
    "rsa2048": "RSA-2048", "ecdsa_p256": "ECDSA P-256", "ed25519": "Ed25519",
}
TICKS = [10, 20, 30, 50, 100, 200, 300, 500, 1000, 2000, 3000, 5000]


def throughput_chart(csv, title, outfile):
    df = pd.read_csv(csv)
    stats = df.groupby(["algorithm", "size_bytes"])["throughput_mb_s"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for color, (name, g) in zip(PALETTE, stats.groupby("algorithm")):
        ax.errorbar(g["size_bytes"], g["mean"], yerr=g["std"], marker="o", capsize=3, label=NAMES[name], color=color)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.minorticks_off()
    ymin, ymax = stats["mean"].min() * 0.8, stats["mean"].max() * 1.3
    ax.set_ylim(ymin, ymax)
    ticks = [t for t in TICKS if ymin <= t <= ymax]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:,}" for t in ticks])
    ax.set_xticks(list(SIZE_LABELS))
    ax.set_xticklabels(list(SIZE_LABELS.values()))
    ax.set_xlabel("Input size")
    ax.set_ylabel("Throughput (MB/s, log scale)")
    ax.set_title(title + "\n(mean ± 1 SD, 30 runs)", fontsize=11)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=200)
    plt.close(fig)


def asymmetric_chart(csv, outfile):
    df = pd.read_csv(csv)
    df["time_us"] = df["time_s"] * 1_000_000
    stats = df.groupby(["operation", "algorithm"])["time_us"].agg(["mean", "std"])
    ops = ["keygen", "sign", "verify"]
    algos = ["rsa2048", "ecdsa_p256", "ed25519"]
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, (algo, color) in enumerate(zip(algos, PALETTE)):
        means = [stats.loc[(op, algo), "mean"] for op in ops]
        stds = [stats.loc[(op, algo), "std"] for op in ops]
        pos = [j + (i - 1) * width for j in range(len(ops))]
        ax.bar(pos, means, width, yerr=stds, capsize=3, label=NAMES[algo], color=color)
        for x, v, s in zip(pos, means, stds):
            label = f"{v:,.1f}" if v < 100 else f"{v:,.0f}"
            ax.text(x, (v + s) * 1.15, label, ha="center", fontsize=8)
    ax.set_yscale("log")
    ax.minorticks_off()
    ax.set_ylim(10, 300000)
    ax.set_yticks([10, 100, 1000, 10000, 100000])
    ax.set_yticklabels(["10", "100", "1,000", "10,000", "100,000"])
    ax.set_xticks(range(len(ops)))
    ax.set_xticklabels(["Key generation", "Signing", "Verification"])
    ax.set_ylabel("Mean time per operation (µs, log scale)")
    ax.set_title("Asymmetric algorithms: time per operation\n(mean ± 1 SD, 30 runs; lower is faster)", fontsize=11)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=200)
    plt.close(fig)


throughput_chart("hash_results.csv", "Hash algorithms: throughput by input size", "fig_hashing.png")
throughput_chart("symmetric_results.csv", "Symmetric ciphers: encryption throughput by input size", "fig_symmetric.png")
asymmetric_chart("asymmetric_results.csv", "fig_asymmetric.png")
print("saved fig_hashing.png, fig_symmetric.png, fig_asymmetric.png")
