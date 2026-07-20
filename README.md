# Cryptography, worked step by step

An interactive, single page visual walkthrough of five core cryptography topics, built for a Network Security course. Each topic comes with five real, fully verified worked examples that animate one step at a time, so students can follow every number by hand.

Topics: **finding primitive roots, Diffie-Hellman key exchange, RSA, DES, and AES.**

![Preview of the walkthrough](assets/preview.svg)

## Live demo

After you enable GitHub Pages (steps below), the site is served at:

```
https://<your-username>.github.io/<your-repo-name>/
```

## What it covers

| Section | Examples | What the student sees |
| --- | --- | --- |
| Primitive root | 5 primes (11, 17, 23, 29, 37) | Factor p-1, apply the order test to g = 2, 3, ..., watch a live residue grid light up. A failing candidate covers only part of the group; the primitive root sweeps all of it. Then verify the full cycle, count roots as phi(p-1), and list them. |
| Diffie-Hellman | 5 exchanges | Two parties build a shared secret over an open channel while an eavesdropper watches. The generator g is a primitive root from the first section. |
| RSA | 5 key pairs | Pick primes, build the public and private keys, encrypt, and decrypt back to the original message. |
| DES | 5 blocks | A 64 bit block through the key schedule, the initial permutation, one full Feistel round (expansion, key XOR, all eight S-boxes, the P permutation), the round by round trail, and the final permutation. |
| AES-128 | 5 blocks | A 128 bit block as a 4 by 4 byte grid through key expansion, the initial key add, one full round (SubBytes, ShiftRows, MixColumns, AddRoundKey), all ten rounds, and the ciphertext. |

That is 25 complete walkthroughs in one file.

## Features

- Step, play, back, and reset controls; keyboard support (left and right arrows to step, space to play, Home to reset).
- Meaning coded colors: public values, secret values, the shared result, and what the eavesdropper sees. Every value also carries a text tag, so it does not rely on color alone.
- A live residue grid for primitive roots, and a state pipeline for the block ciphers (Feistel halves for DES, the 4 by 4 byte grid for AES) that updates as you step.
- Collapsible "compute by hand" panels: square and multiply for modular exponentiation, the eight DES S-box lookups, all sixteen DES round keys, the AES round keys, and the full AES round table.
- Single self contained HTML file. No build step and no runtime dependencies. Fonts load from Google Fonts when online and fall back to system fonts offline.
- Responsive layout, respects the reduce motion setting, and has visible keyboard focus rings.

## Run locally

Open `index.html` in any modern browser. That is all it needs.

To serve it over HTTP instead (useful for testing exactly what Pages will serve):

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Publish with GitHub Pages

1. Create a new repository and add these files, then push to the `main` branch.
2. In the repository, go to **Settings** then **Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Choose branch **main** and folder **/ (root)**, then **Save**.
5. Wait about a minute. Your site appears at the URL shown at the top of the Pages settings.

The included empty `.nojekyll` file tells Pages to serve the files as is, with no Jekyll processing.

## Verification and reproducibility

Every numeric value in the walkthrough is verified. The DES and AES examples were computed by from scratch reference implementations and then checked byte for byte against a well known crypto library and against the published FIPS-197 test vectors, including the Appendix B intermediate round states (so the round by round values shown in the app are verified, not only the final ciphertext). The classic DES textbook vector reproduces exactly.

To reproduce the verification yourself:

```bash
pip install -r requirements.txt
python verify/verify_vectors.py
```

Expected output: each primitive root, DES, and AES vector printed, ending with `ALL VECTORS VERIFIED`. The same script can regenerate the embedded data blob with `python verify/verify_vectors.py --emit cipherdata.json` if you ever want to rebuild it.

## Teaching notes and honest caveats

Worth stating clearly to students:

- These are the raw cipher cores. Real systems wrap them in a mode of operation (never a single ECB block) and, for the public key parts, use padding such as OAEP. A man in the middle defence for Diffie-Hellman needs authentication.
- DES is included for how clearly it teaches Feistel structure. Its 56 bit key is broken by brute force in practice and it should not be used to protect real data.
- The number theory sections use small primes on purpose, so the arithmetic is checkable by hand. Real keys use the same operations at hundreds of digits, and that size is the whole defence.

## Suggested exercises

- Change an RSA message and predict the ciphertext, then step through to check it.
- For a prime in the primitive root section, pick a non primitive g and predict how many residues it will reach before stepping through.
- Trace one AES round on paper for the FIPS-197 example and compare against the app.
- Explain why the two Diffie-Hellman parties reach the same secret by different routes.

## Tech

One HTML file with inline CSS and vanilla JavaScript. No frameworks, no bundler, no package install required to view it.

## License

MIT. See [LICENSE](LICENSE). Free to reuse and adapt for teaching.

## Acknowledgements

Test vectors come from NIST FIPS-197 (AES) and NIST SP 800-38A, and the DES worked example follows the classic published walkthrough. Cross checking during development used the PyCryptodome library.
