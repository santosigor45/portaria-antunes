"""Valida sintaxe/configuração sem importar a aplicação ou acessar bancos."""
import json
import subprocess
from pathlib import Path

config = json.loads(Path(".github/nautilus.json").read_text())
paths = [Path(p.decode()) for p in subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0") if p]
python_count = php_count = 0
for path in paths:
    if not path.is_file() or any(part in {"tests", "__tests__", "vendor"} for part in path.parts):
        continue
    if path.suffix == ".py":
        compile(path.read_bytes(), str(path), "exec")
        python_count += 1
    if path.suffix == ".json" and (str(path).startswith(".github/") or path.name in {"package.json", "package-lock.json"}):
        json.loads(path.read_text())
    if path.suffix == ".sh":
        subprocess.run(["bash", "-n", str(path)], check=True)
    if config["project"] == "estoque" and path.suffix == ".php" and (
        (str(path).startswith(tuple(config["phpLintPaths"])) and not str(path).startswith(tuple(config["phpLintExcluded"]))) or str(path) == "index.php"
    ):
        result = subprocess.run(["php", "-d", "short_open_tag=1", "-l", str(path)], capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        php_count += 1
print(f"Sintaxe conferida: {python_count} arquivos Python, {php_count} arquivos PHP; JSON e shell válidos.")
