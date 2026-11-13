import os
import random
import time
from pathlib import Path

import cryptography
import pandas as pd
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.primitives.ciphers import Cipher, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

SIZES = [1_000, 100_000, 1_000_000, 10_000_000, 100_000_000]
RUNS = 30
WARMUP = 3

KEY_3DES = os.urandom(24)
KEY_AES = os.urandom(32)
KEY_CHACHA = os.urandom(32)


def enc_3des(data, nonce):
    enc = Cipher(TripleDES(KEY_3DES), modes.CBC(nonce[:8])).encryptor()
    ct = enc.update(data)
    enc.finalize()
    return ct


def dec_3des(ct, nonce):
    dec = Cipher(TripleDES(KEY_3DES), modes.CBC(nonce[:8])).decryptor()
    pt = dec.update(ct)
    dec.finalize()
    return pt


def enc_aes(data, nonce):
    return AESGCM(KEY_AES).encrypt(nonce, data, None)


def dec_aes(ct, nonce):
    return AESGCM(KEY_AES).decrypt(nonce, ct, None)


def enc_chacha(data, nonce):
    return ChaCha20Poly1305(KEY_CHACHA).encrypt(nonce, data, None)


def dec_chacha(ct, nonce):
    return ChaCha20Poly1305(KEY_CHACHA).decrypt(nonce, ct, None)


CIPHERS = {
    "3des_cbc": (enc_3des, dec_3des),
    "aes256_gcm": (enc_aes, dec_aes),
    "chacha20_poly1305": (enc_chacha, dec_chacha),
}

print("cryptography:", cryptography.__version__)

rng = random.Random(42)
rows = []

for size in SIZES:
    data = rng.randbytes(size)
    reps = max(1, 10_000_000 // size)
    nonces = [os.urandom(12) for _ in range(reps)]

    for name, (enc, dec) in CIPHERS.items():
        ct = enc(data, nonces[0])
        assert ct != data and dec(ct, nonces[0]) == data, name
        for _ in range(WARMUP):
            enc(data, nonces[0])
    print("round-trip OK for size", size)

    for run in range(1, RUNS + 1):
        order = list(CIPHERS)
        rng.shuffle(order)
        for name in order:
            enc = CIPHERS[name][0]
            start = time.perf_counter()
            for n in nonces:
                enc(data, n)
            elapsed = (time.perf_counter() - start) / reps
            rows.append({
                "algorithm": name,
                "size_bytes": size,
                "run": run,
                "time_s": elapsed,
                "throughput_mb_s": size / 1_000_000 / elapsed,
            })
    print("done size", size)

df = pd.DataFrame(rows)
out = Path(__file__).resolve().parent / "symmetric_results.csv"
df.to_csv(out, index=False)
print("saved to", out)
print(df.groupby(["size_bytes", "algorithm"])["throughput_mb_s"].mean().round(1))