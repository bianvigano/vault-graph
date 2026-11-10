"""Install a checkout-backed launcher: python3 install-cli.py."""
import os
import shlex
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent
uv = shutil.which('uv')
if not uv:
    raise SystemExit('uv belum tersedia; instal uv dahulu.')
launcher = Path.home() / '.local/bin/vault-graph'
launcher.parent.mkdir(parents=True, exist_ok=True)
content = '#!/bin/sh\nexec ' + shlex.quote(uv) + ' run --directory ' + shlex.quote(str(root)) + ' python -m vault_graph.main "$@"\n'
if launcher.exists():
    backup = launcher.with_suffix('.backup')
    if not backup.exists():
        shutil.copy2(launcher, backup)
temporary = launcher.with_suffix('.new')
temporary.write_text(content)
temporary.chmod(0o755)
os.replace(temporary, launcher)
print(f'Launcher terpasang: {launcher}')
