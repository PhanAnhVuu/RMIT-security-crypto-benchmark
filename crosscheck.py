import hashlib
import random
import subprocess
from pathlib import Path

OPENSSL = r"C:\Program Files\Git\usr\bin\openssl.exe"

folder = Path(__file__).resolve().parent
sample = folder / "sample.bin"
sample.write_bytes(random.Random(42).randbytes(1_000_000))
data = sample.read_bytes()

version = subprocess.run([OPENSSL, "version"], capture_output=True, text=True)
print("OpenSSL:", version.stdout.strip())

algorithms = {"md5": "md5", "sha1": "sha1", "sha256": "sha256", "sha3_256": "sha3-256"}

for py_name, ossl_name in algorithms.items():
    py_digest = hashlib.new(py_name, data).hexdigest()
    result = subprocess.run(
        [OPENSSL, "dgst", "-" + ossl_name, str(sample)],
        capture_output=True,
        text=True,
    )
    out = result.stdout.strip()
    ossl_digest = out.split()[-1] if out else "ERROR " + result.stderr.strip()
    status = "MATCH" if py_digest == ossl_digest else "DIFF"
    print(f"{py_name:9} {status}  python={py_digest[:16]}...  openssl={ossl_digest[:16]}...")