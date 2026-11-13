import hashlib
import platform
import random
import ssl
import sys
import time
from pathlib import Path


import pandas as pd

ALGORITHMS = ["md5", "sha1", "sha256", "sha3_256"]
SIZES = [1_000, 100_000, 1_000_000, 10_000_000, 100_000_000]
RUNS = 30
WARMUP = 3

print("Python:", sys.version.split()[0])
print("OpenSSL (Python):", ssl.OPENSSL_VERSION)
print("Platform:", platform.platform())
print("CPU:", platform.processor())

rng = random.Random(42)
rows = []

for size in SIZES:
    data = rng.randbytes(size)
    reps = max(1, 10_000_000 // size)

    for algo in ALGORITHMS:
        for _ in range(WARMUP):
            hashlib.new(algo, data).digest()

    for run in range(1, RUNS + 1):
        order = ALGORITHMS[:]
        rng.shuffle(order)
        for algo in order:
            start = time.perf_counter()
            for _ in range(reps):
                hashlib.new(algo, data).digest()
            elapsed = (time.perf_counter() - start) / reps
            rows.append({
                "algorithm": algo,
                "size_bytes": size,
                "run": run,
                "time_s": elapsed,
                "throughput_mb_s": size / 1_000_000 / elapsed,
            })
    print("done size", size)

df = pd.DataFrame(rows)
out = Path(__file__).resolve().parent / "hash_results.csv"
df.to_csv(out, index=False)
print("saved to", out)
print(df.groupby(["size_bytes", "algorithm"])["throughput_mb_s"].mean().round(1))