import hashlib
import os
import subprocess
from pathlib import Path

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

OPENSSL = r"C:\Program Files\Git\usr\bin\openssl.exe"
folder = Path(__file__).resolve().parent
plain_file = folder / "report.txt"
enc_file = folder / "report.enc"

plain_file.write_text("Confidential: demo file for the cryptography comparison.\n")
data = plain_file.read_bytes()

print("DEMO: protecting one file with hashing, symmetric and asymmetric cryptography")
print("File:", plain_file.name, "|", len(data), "bytes")

input("\nPress Enter for PART 1: HASHING (integrity)")
py_hash = hashlib.sha256(data).hexdigest()
try:
    out = subprocess.run([OPENSSL, "dgst", "-sha256", str(plain_file)], capture_output=True, text=True).stdout
    ossl_hash = out.strip().split()[-1]
except (FileNotFoundError, IndexError):
    ossl_hash = "OpenSSL not found"
print("Python  SHA-256:", py_hash)
print("OpenSSL SHA-256:", ossl_hash)
print("Same result in both tools:", py_hash == ossl_hash)
modified = data + b" "
print("SHA-256 after adding one space:", hashlib.sha256(modified).hexdigest())
print("MD5 (legacy, broken):", hashlib.md5(data).hexdigest())

input("\nPress Enter for PART 2: SYMMETRIC ENCRYPTION (confidentiality + integrity)")
key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
aes = AESGCM(key)
ciphertext = aes.encrypt(nonce, data, None)
enc_file.write_bytes(nonce + ciphertext)
print("AES-256-GCM key (first 16 hex chars):", key.hex()[:16] + "...")
print("Ciphertext (first 32 bytes, hex):", ciphertext[:32].hex())
print("Decrypts back to the original:", aes.decrypt(nonce, ciphertext, None) == data)
tampered = bytearray(ciphertext)
tampered[0] ^= 1
try:
    aes.decrypt(nonce, bytes(tampered), None)
    print("WARNING: tampering was not detected")
except InvalidTag:
    print("One flipped bit in the ciphertext was rejected (InvalidTag)")

input("\nPress Enter for PART 3: ASYMMETRIC SIGNATURE (authentication + non-repudiation)")
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()
digest = hashlib.sha256(data).digest()
signature = private_key.sign(digest)
print("Signature of the file's SHA-256 (first 32 bytes, hex):", signature[:32].hex())
public_key.verify(signature, digest)
print("Signature verifies for the original file")
try:
    public_key.verify(signature, hashlib.sha256(modified).digest())
    print("WARNING: modified file was accepted")
except InvalidSignature:
    print("Signature rejected for the modified file (InvalidSignature)")

print("\nSUMMARY")
print("Integrity: SHA-256 hash, checked in Python and OpenSSL")
print("Confidentiality + integrity: AES-256-GCM")
print("Authentication + non-repudiation: Ed25519 signature")