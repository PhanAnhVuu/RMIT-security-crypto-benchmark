import random
import time
from pathlib import Path

import cryptography
import pandas as pd
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

RUNS = 30
WARMUP = 3
SIGN_VERIFY_REPS = 200

rng = random.Random(42)
MESSAGE = rng.randbytes(32)
TAMPERED = bytes([MESSAGE[0] ^ 1]) + MESSAGE[1:]
PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32)


def rsa_keygen():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def rsa_sign(key, msg):
    return key.sign(msg, PSS, hashes.SHA256())


def rsa_verify(pub, sig, msg):
    pub.verify(sig, msg, PSS, hashes.SHA256())


def ecdsa_keygen():
    return ec.generate_private_key(ec.SECP256R1())


def ecdsa_sign(key, msg):
    return key.sign(msg, ec.ECDSA(hashes.SHA256()))


def ecdsa_verify(pub, sig, msg):
    pub.verify(sig, msg, ec.ECDSA(hashes.SHA256()))


def ed_keygen():
    return ed25519.Ed25519PrivateKey.generate()


def ed_sign(key, msg):
    return key.sign(msg)


def ed_verify(pub, sig, msg):
    pub.verify(sig, msg)


ALGOS = {
    "rsa2048": (rsa_keygen, rsa_sign, rsa_verify, 1),
    "ecdsa_p256": (ecdsa_keygen, ecdsa_sign, ecdsa_verify, 200),
    "ed25519": (ed_keygen, ed_sign, ed_verify, 200),
}
OPERATIONS = ["keygen", "sign", "verify"]

print("cryptography:", cryptography.__version__)

setup = {}
for name, (keygen, sign, verify, keygen_reps) in ALGOS.items():
    key = keygen()
    pub = key.public_key()
    sig = sign(key, MESSAGE)
    verify(pub, sig, MESSAGE)
    try:
        verify(pub, sig, TAMPERED)
        print(name, "WARNING: tampered message accepted")
    except InvalidSignature:
        print(name, "OK: valid signature accepted, tampered message rejected")
    setup[name] = (keygen, sign, verify, key, pub, sig, keygen_reps)


def timed(name, op):
    keygen, sign, verify, key, pub, sig, keygen_reps = setup[name]
    reps = keygen_reps if op == "keygen" else SIGN_VERIFY_REPS
    start = time.perf_counter()
    if op == "keygen":
        for _ in range(reps):
            keygen()
    elif op == "sign":
        for _ in range(reps):
            sign(key, MESSAGE)
    else:
        for _ in range(reps):
            verify(pub, sig, MESSAGE)
    return (time.perf_counter() - start) / reps


for name in ALGOS:
    for op in OPERATIONS:
        for _ in range(WARMUP):
            timed(name, op)

rows = []
for run in range(1, RUNS + 1):
    order = [(n, o) for n in ALGOS for o in OPERATIONS]
    rng.shuffle(order)
    for name, op in order:
        rows.append({
            "algorithm": name,
            "operation": op,
            "run": run,
            "time_s": timed(name, op),
        })
    print("done run", run)

df = pd.DataFrame(rows)
out = Path(__file__).resolve().parent / "asymmetric_results.csv"
df.to_csv(out, index=False)
print("saved to", out)
print("mean time in microseconds:")
print((df.groupby(["operation", "algorithm"])["time_s"].mean() * 1_000_000).round(1))