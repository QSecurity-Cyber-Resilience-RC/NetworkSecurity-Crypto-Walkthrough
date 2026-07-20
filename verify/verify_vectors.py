#!/usr/bin/env python3
"""
Verify every numeric vector used in the cryptography walkthrough.

This script recomputes, from scratch:
  - primitive roots for the five primes used in the app,
  - the five DES encryptions (full intermediates),
  - the five AES-128 encryptions (full intermediates),
and checks the block cipher outputs byte for byte against PyCryptodome and
against the published FIPS-197 test vectors, including the Appendix B
intermediate round states.

Usage:
    pip install -r requirements.txt
    python verify/verify_vectors.py                 # verify and print
    python verify/verify_vectors.py --emit out.json # also write the data blob

The app (index.html) embeds exactly the data this script produces. Running the
script lets anyone confirm that the numbers shown in the app are correct.
"""
import json
import argparse
from Crypto.Cipher import DES as PDES, AES as PAES

# ============================================================ PRIMITIVE ROOTS
def factor(n):
    f = {}; d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f

def order(g, p):
    x = 1
    for k in range(1, p):
        x = (x * g) % p
        if x == 1:
            return k
    return None

def primitive_roots(p):
    return [g for g in range(1, p) if order(g, p) == p - 1]

def euler_phi(n):
    res = n
    for q in factor(n):
        res -= res // q
    return res

def prim_example(p):
    pm1 = p - 1
    fac = factor(pm1)
    qs = sorted(fac.keys())
    trail = []
    found = None
    for g in range(2, p):
        tests = []; ok = True
        for q in qs:
            e = pm1 // q
            val = pow(g, e, p)
            tests.append({"q": q, "exp": e, "val": val, "one": val == 1})
            if val == 1:
                ok = False
        trail.append({"g": g, "tests": tests, "prim": ok})
        if ok:
            found = g; break
    cycle = []; x = 1
    for _ in range(1, pm1 + 1):
        x = (x * found) % p
        cycle.append(x)
    roots = primitive_roots(p)
    assert sorted(set(cycle)) == list(range(1, p)), "cycle must cover all residues"
    assert len(roots) == euler_phi(pm1)
    assert found == roots[0]
    return {
        "p": p, "pm1": pm1,
        "fac": [{"q": q, "k": fac[q]} for q in qs],
        "facStr": " x ".join((f"{q}^{fac[q]}" if fac[q] > 1 else f"{q}") for q in qs),
        "trail": trail, "g": found, "cycle": cycle,
        "phi": euler_phi(pm1), "roots": roots,
    }

PRIMES = [11, 17, 23, 29, 37]

# ============================================================ DES
IP = [58,50,42,34,26,18,10,2,60,52,44,36,28,20,12,4,62,54,46,38,30,22,14,6,64,56,48,40,32,24,16,8,
      57,49,41,33,25,17,9,1,59,51,43,35,27,19,11,3,61,53,45,37,29,21,13,5,63,55,47,39,31,23,15,7]
FP = [40,8,48,16,56,24,64,32,39,7,47,15,55,23,63,31,38,6,46,14,54,22,62,30,37,5,45,13,53,21,61,29,
      36,4,44,12,52,20,60,28,35,3,43,11,51,19,59,27,34,2,42,10,50,18,58,26,33,1,41,9,49,17,57,25]
E = [32,1,2,3,4,5,4,5,6,7,8,9,8,9,10,11,12,13,12,13,14,15,16,17,
     16,17,18,19,20,21,20,21,22,23,24,25,24,25,26,27,28,29,28,29,30,31,32,1]
P = [16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25]
PC1 = [57,49,41,33,25,17,9,1,58,50,42,34,26,18,10,2,59,51,43,35,27,19,11,3,
       60,52,44,36,63,55,47,39,31,23,15,7,62,54,46,38,30,22,14,6,61,53,45,37,29,21,13,5,28,20,12,4]
PC2 = [14,17,11,24,1,5,3,28,15,6,21,10,23,19,12,4,26,8,16,7,27,20,13,2,
       41,52,31,37,47,55,30,40,51,45,33,48,44,49,39,56,34,53,46,42,50,36,29,32]
SHIFT = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]
SBOX = [
[[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],[0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
 [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]],
[[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],[3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
 [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]],
[[10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8],[13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1],
 [13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7],[1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12]],
[[7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15],[13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9],
 [10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4],[3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14]],
[[2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9],[14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6],
 [4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14],[11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3]],
[[12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11],[10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8],
 [9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6],[4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13]],
[[4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1],[13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6],
 [1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2],[6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12]],
[[13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7],[1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2],
 [7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8],[2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]]]

def bits(x, n):
    return [(x >> (n - 1 - i)) & 1 for i in range(n)]

def frombits(b):
    x = 0
    for bit in b:
        x = (x << 1) | bit
    return x

def perm(inp, table):
    return [inp[i - 1] for i in table]

def xor(a, b):
    return [x ^ y for x, y in zip(a, b)]

def hx(b):
    n = len(b); x = frombits(b)
    return format(x, "0" + str((n + 3) // 4) + "x").upper()

def des_keys(key64):
    k = perm(key64, PC1)
    C, D = k[:28], k[28:]
    rk = []
    for i in range(16):
        C = C[SHIFT[i]:] + C[:SHIFT[i]]
        D = D[SHIFT[i]:] + D[:SHIFT[i]]
        rk.append(perm(C + D, PC2))
    return rk

def feistel(R, K, detail=False):
    ER = perm(R, E)
    x = xor(ER, K)
    out = []; groups = []
    for i in range(8):
        six = x[i * 6:i * 6 + 6]
        row = (six[0] << 1) | six[5]
        col = (six[1] << 3) | (six[2] << 2) | (six[3] << 1) | six[4]
        val = SBOX[i][row][col]
        vb = bits(val, 4)
        out += vb
        groups.append({"in": "".join(map(str, six)), "row": row, "col": col,
                       "out": "".join(map(str, vb)), "val": val})
    pout = perm(out, P)
    if detail:
        return pout, {"ER": hx(ER), "K": hx(K), "x": hx(x), "groups": groups,
                      "sboxOut": hx(out), "P": hx(pout)}
    return pout, None

def des_encrypt(pt64, key64):
    rk = des_keys(key64)
    b = perm(pt64, IP)
    L, R = b[:32], b[32:]
    L0, R0 = L[:], R[:]
    rounds = []; detail1 = None
    for i in range(16):
        f, dt = feistel(R, rk[i], detail=(i == 0))
        newR = xor(L, f)
        L, R = R, newR
        rounds.append({"i": i + 1, "L": hx(L), "R": hx(R)})
        if i == 0:
            detail1 = dt
    pre = R + L
    ct = perm(pre, FP)
    return {"ct": hx(ct), "rk": [hx(k) for k in rk], "L0": hx(L0), "R0": hx(R0),
            "rounds": rounds, "detail": detail1, "pre": hx(pre)}

def des_case(pt_hex, key_hex):
    pt = bits(int(pt_hex, 16), 64); key = bits(int(key_hex, 16), 64)
    r = des_encrypt(pt, key)
    ref = PDES.new(bytes.fromhex(key_hex), PDES.MODE_ECB).encrypt(bytes.fromhex(pt_hex)).hex().upper()
    assert r["ct"] == ref, f"DES mismatch {r['ct']} vs {ref}"
    r["pt"] = pt_hex.upper(); r["key"] = key_hex.upper()
    return r

DES_INPUTS = [
    ("0123456789ABCDEF", "133457799BBCDFF1"),
    ("4E6F772069732074", "0123456789ABCDEF"),
    ("0000000000000000", "0000000000000000"),
    ("FFFFFFFFFFFFFFFF", "0123456789ABCDEF"),
    ("0123456789ABCDEF", "AABB09182736CCDD"),
]

# ============================================================ AES-128
AES_SBOX = [
0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16]
RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36]

def gmul(a, b):
    r = 0
    for _ in range(8):
        if b & 1:
            r ^= a
        hi = a & 0x80; a = (a << 1) & 0xff
        if hi:
            a ^= 0x1b
        b >>= 1
    return r

def key_expansion(key):
    w = [tuple(key[4 * i:4 * i + 4]) for i in range(4)]
    for i in range(4, 44):
        t = list(w[i - 1])
        if i % 4 == 0:
            t = t[1:] + t[:1]
            t = [AES_SBOX[b] for b in t]
            t[0] ^= RCON[i // 4 - 1]
        w.append(tuple(w[i - 4][j] ^ t[j] for j in range(4)))
    return w

def rk_bytes(w, r):
    out = []
    for c in range(4):
        out += list(w[4 * r + c])
    return out

def st_hex(state):
    return "".join(format(b, "02x") for b in state).upper()

def sub_bytes(s):
    return [AES_SBOX[b] for b in s]

def shift_rows(s):
    o = [0] * 16
    for r in range(4):
        for c in range(4):
            o[c * 4 + r] = s[((c + r) % 4) * 4 + r]
    return o

def mix_columns(s):
    o = [0] * 16
    for c in range(4):
        col = s[c * 4:c * 4 + 4]
        o[c * 4 + 0] = gmul(col[0], 2) ^ gmul(col[1], 3) ^ col[2] ^ col[3]
        o[c * 4 + 1] = col[0] ^ gmul(col[1], 2) ^ gmul(col[2], 3) ^ col[3]
        o[c * 4 + 2] = col[0] ^ col[1] ^ gmul(col[2], 2) ^ gmul(col[3], 3)
        o[c * 4 + 3] = gmul(col[0], 3) ^ col[1] ^ col[2] ^ gmul(col[3], 2)
    return o

def add_round_key(s, rk):
    return [a ^ b for a, b in zip(s, rk)]

def aes_encrypt(pt, key):
    w = key_expansion(key)
    state = list(pt)
    rks = [rk_bytes(w, r) for r in range(11)]
    state = add_round_key(state, rks[0])
    init = st_hex(state)
    rounds = []; detail = None
    for r in range(1, 11):
        b_sub = sub_bytes(state)
        b_shift = shift_rows(b_sub)
        if r != 10:
            b_mix = mix_columns(b_shift)
            state = add_round_key(b_mix, rks[r])
            mixhex = st_hex(b_mix)
        else:
            b_mix = None
            state = add_round_key(b_shift, rks[r])
            mixhex = None
        rounds.append({"i": r, "sub": st_hex(b_sub), "shift": st_hex(b_shift),
                       "mix": mixhex, "out": st_hex(state)})
        if r == 1:
            first = int(init[0:2], 16)
            detail = {
                "inState": init, "sub": st_hex(b_sub), "shift": st_hex(b_shift),
                "mix": st_hex(b_mix), "out": st_hex(state), "rk": st_hex(rks[1]),
                "sbEx": {"in": format(first, "02x").upper(),
                         "out": format(AES_SBOX[first], "02x").upper()},
                "mixCol": {"in": [format(v, "02x").upper() for v in b_shift[0:4]],
                           "out": [format(v, "02x").upper() for v in b_mix[0:4]]},
            }
    return {"ct": st_hex(state), "rks": [st_hex(r) for r in rks],
            "init": init, "rounds": rounds, "detail": detail}

def aes_case(pt_hex, key_hex):
    pt = bytes.fromhex(pt_hex); key = bytes.fromhex(key_hex)
    r = aes_encrypt(list(pt), list(key))
    ref = PAES.new(key, PAES.MODE_ECB).encrypt(pt).hex().upper()
    assert r["ct"] == ref, f"AES mismatch {r['ct']} vs {ref}"
    r["pt"] = pt_hex.upper(); r["key"] = key_hex.upper()
    return r

AES_INPUTS = [
    ("00112233445566778899aabbccddeeff", "000102030405060708090a0b0c0d0e0f"),
    ("3243f6a8885a308d313198a2e0370734", "2b7e151628aed2a6abf7158809cf4f3c"),
    ("6bc1bee22e409f96e93d7e117393172a", "2b7e151628aed2a6abf7158809cf4f3c"),
    ("00000000000000000000000000000000", "00000000000000000000000000000000"),
    ("000102030405060708090a0b0c0d0e0f", "000102030405060708090a0b0c0d0e0f"),
]

# ============================================================ RUN
def main():
    ap = argparse.ArgumentParser(description="Verify all walkthrough vectors.")
    ap.add_argument("--emit", metavar="PATH", default=None,
                    help="also write the verified data blob as JSON to PATH")
    args = ap.parse_args()

    print("Primitive roots")
    PRIM = [prim_example(p) for p in PRIMES]
    for e in PRIM:
        print(f"  p={e['p']:>3}  p-1={e['pm1']} = {e['facStr']:<8}  smallest g={e['g']:>2}"
              f"  count=phi(p-1)={e['phi']:>2}  roots={e['roots']}")

    print("\nDES (checked against PyCryptodome)")
    DES = [des_case(p, k) for p, k in DES_INPUTS]
    assert DES[0]["ct"] == "85E813540F0AB405", "classic DES vector must reproduce"
    for d in DES:
        print(f"  pt={d['pt']}  key={d['key']}  ->  ct={d['ct']}")

    print("\nAES-128 (checked against PyCryptodome and FIPS-197)")
    AES = [aes_case(p, k) for p, k in AES_INPUTS]
    assert AES[0]["ct"] == "69C4E0D86A7B0430D8CDB78070B4C55A", "FIPS-197 vector must reproduce"
    assert AES[1]["ct"] == "3925841D02DC09FBDC118597196A0B32", "FIPS-197 appendix B vector"
    # Appendix B intermediate round-1 states validate the round by round extraction:
    assert AES[1]["init"].lower() == "193de3bea0f4e22b9ac68d2ae9f84808"
    assert AES[1]["rounds"][0]["sub"].lower() == "d42711aee0bf98f1b8b45de51e415230"
    assert AES[1]["rounds"][0]["shift"].lower() == "d4bf5d30e0b452aeb84111f11e2798e5"
    assert AES[1]["rounds"][0]["mix"].lower() == "046681e5e0cb199a48f8d37a2806264c"
    for a in AES:
        print(f"  pt={a['pt']}  key={a['key']}  ->  ct={a['ct']}")

    if args.emit:
        blob = {"PRIM": PRIM, "DES": DES, "AES": AES}
        with open(args.emit, "w") as f:
            json.dump(blob, f, separators=(",", ":"))
        print(f"\nwrote data blob to {args.emit}")

    print("\nALL VECTORS VERIFIED")

if __name__ == "__main__":
    main()
