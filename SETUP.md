# Setup and verification (for the instructor)

The student-facing guide is in [README.md](README.md). This file covers hosting the site and confirming the numbers.

## Publish with GitHub Pages

1. Create a repository, add these files, and push to the `main` branch.
2. In the repository, open **Settings**, then **Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Choose branch **main** and folder **/ (root)**, then **Save**.
5. Wait about a minute. The site appears at the URL shown at the top of the Pages settings, in the form `https://<your-username>.github.io/<your-repo>/`.
6. Paste that URL into the "Open the walkthrough here" line near the top of `README.md` so students can click straight through.

The empty `.nojekyll` file tells Pages to serve the files as is, with no Jekyll processing. If the GitHub web uploader skips it (it sometimes drops files whose names begin with a dot), recreate it with Add file, then Create new file, name it `.nojekyll`, leave it empty, and commit.

## Run locally

Open `index.html` in any modern browser. To serve it over HTTP, which mirrors exactly what Pages will serve:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Verification and reproducibility

Every numeric value in the walkthrough is verified. The DES and AES examples were computed by from scratch reference implementations and then checked byte for byte against the PyCryptodome library and against the published NIST FIPS-197 test vectors, including the Appendix B intermediate round states, so the round by round values in the app are verified and not only the final ciphertext. The classic DES textbook vector reproduces exactly.

To confirm this yourself:

```bash
pip install -r requirements.txt
python verify/verify_vectors.py
```

The script recomputes all 25 examples, prints each vector, and ends with `ALL VECTORS VERIFIED`. It can also regenerate the exact data blob embedded in `index.html` with `python verify/verify_vectors.py --emit cipherdata.json`, which is byte identical to what the app already contains.

Note that this script needs Python and PyCryptodome, so it runs on your own machine or in continuous integration, not on GitHub Pages (Pages only serves static files).

## What the files are

- `index.html` is the whole application: one self contained HTML file with inline CSS and vanilla JavaScript, no build step and no runtime dependencies. Fonts load from Google Fonts when online and fall back to system fonts offline.
- `assets/preview.svg` is the banner shown in the README.
- `verify/verify_vectors.py` recomputes and checks every vector.
- `requirements.txt` lists the one Python package the verifier needs.

## License

MIT. See [LICENSE](LICENSE). Free to reuse and adapt for teaching. Remember to put your name on the copyright line.

## Acknowledgements

Test vectors come from NIST FIPS-197 (AES) and NIST SP 800-38A, and the DES worked example follows the classic published walkthrough. Cross checking during development used the PyCryptodome library.
