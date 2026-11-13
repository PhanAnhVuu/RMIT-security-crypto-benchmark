import hashlib
import os
import time
import statistics

data = os.urandom(1024 * 1024)

times = []
for _ in range(30):
    start = time.perf_counter()
    hashlib.sha256(data).hexdigest()
    end = time.perf_counter()
    times.append((end - start) * 1000)

print("runs:", len(times))
print("mean ms:", round(statistics.mean(times), 3))
print("stdev ms:", round(statistics.stdev(times), 3))
print("throughput MB/s:", round(1 / (statistics.mean(times) / 1000), 1))