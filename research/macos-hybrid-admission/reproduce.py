"""Exercise cold assembly and warm reuse with the real, inventory-pinned SDK."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'work/scoped-proof'
OUT.mkdir(parents=True, exist_ok=True)
assert sys.platform == 'darwin' and platform.machine() == 'arm64'
CACHE = ROOT / 'work/bootstrap-proof-cache'
assert not CACHE.exists(), 'proof requires its own fresh cache'
env = dict(os.environ, PUMP_RECON_HOME=str(CACHE))
os.environ['PUMP_RECON_HOME'] = str(CACHE)
SCRIPT = ROOT / 'reconstruction/toolchain/bootstrap.py'


def run(name, command):
    completed = subprocess.run(command, cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=600)
    (OUT / (name + '.log')).write_text(completed.stdout, encoding='utf-8')
    return completed.returncode


command = [sys.executable, '-B', str(SCRIPT), '--sdk-check', 'full']
codes = {name: run(name, command) for name in ('cold', 'reuse')}
result = {'platform': sys.platform, 'machine': platform.machine(),
          'cli_returncodes': codes, 'fresh_cache': str(CACHE)}
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
if any(codes.values()):
    raise SystemExit('real bootstrap failed; inspect retained cold/reuse logs')

spec = importlib.util.spec_from_file_location('actual_bootstrap', SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
assert bootstrap.hybrid_ok()
assert not bootstrap.check_linux_libs(bootstrap.HYBRID)
count, problems = bootstrap.check_sdk('full')
assert not problems
result['sdk_inventory_entries'] = count
result['target_libraries'] = len(bootstrap.MANIFEST.read_text().splitlines())
rustc = bootstrap.HYBRID / 'rust/bin/rustc'
assert run('compiler-version', [str(rustc), '-vV']) == 0
assert run('compiler-sysroot', [str(rustc), '--print', 'sysroot']) == 0

# Only the proof's private copied hybrid is changed; never the official SDK.
library = next((bootstrap.HYBRID / 'rust/lib/rustlib/sbpf-solana-solana/lib').glob('*.rlib'))
saved = library.read_bytes()
try:
    library.write_bytes(bytes([saved[0] ^ 1]) + saved[1:])
    assert bootstrap.hybrid_ok() is False
    result['changed_private_library_rejected'] = True
finally:
    library.write_bytes(saved)
assert bootstrap.hybrid_ok()
assert not bootstrap.check_sdk('full')[1]
result['restored_hybrid_accepted'] = True
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
