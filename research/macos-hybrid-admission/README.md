# Admit the actual macOS identity toolchain

At base `1043a51e8798c5974a84ecaed5c85e9d6938cfce`, `hybrid_ok()`
checks the real macOS rustc, both copied dylibs and host-library link, then
passes an undefined `root` to the target-library verifier. Correct cold
assembly and reuse therefore reach `NameError`. The Linux admission helper
has its own valid `root` parameter; only the macOS helper needs `HYBRID`.

This is an on-chain reconstruction toolchain fix. SDK inventory admission,
target-library hashes, compiler bytes, flags and reconstruction source are
unchanged. It does not claim a new program match or runtime acceptance.

## Real reproduction

Use macOS arm64, Python 3.12 and the unmodified official platform-tools
v1.44 macOS archive in `~/.cache/solana/v1.44/platform-tools`. The proof
does not download or execute unpinned tools. The fork-only runner verifies
archive SHA-256
`66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`
before extracting it; bootstrap then verifies the repository SDK inventory.

From a fresh checkout, without an existing `work/bootstrap-proof-cache`:

```sh
python -B research/macos-hybrid-admission/reproduce.py
```

The same proof script at the base revision invokes real cold assembly and
reuse, retaining both CLI logs and their actual return codes before failing.
Before run:
<https://github.com/miracle2044/pumpfun-source/actions/runs/41082184168>.

With the fix, both full-inventory CLI invocations must exit zero. The proof
also calls the actual compiler for its version and sysroot, verifies the
target libraries, changes only a private copied target library to check
rejection, restores it, and rechecks the hybrid and untouched official SDK.
It retains results under `work/scoped-proof`. The proof uses real SDK files
and compiler execution, with no mocked compiler or platform checks.

Run required saved-evidence checks separately:

```sh
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```
