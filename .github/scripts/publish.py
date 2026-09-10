"""Build AMD64 no GitHub e envio de imagens ao receptor restrito da Nautilus."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def gate(config):
    def get(path):
        request = urllib.request.Request(
            "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + "/" + path,
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    validation = get("actions/runs/" + os.environ["VALIDATION_RUN_ID"])
    expected = {"head_sha": os.environ["RELEASE_SHA"], "head_branch": config["branch"],
                "event": "push", "status": "completed", "conclusion": "success",
                "path": ".github/workflows/validar.yml"}
    if any(validation.get(k) != v for k, v in expected.items()):
        raise RuntimeError("As validações básicas deste commit não foram aprovadas.")
    for key in ("repository", "head_repository"):
        if (validation.get(key) or {}).get("full_name") != os.environ["GITHUB_REPOSITORY"]:
            raise RuntimeError("Validação de outro repositório.")
    if get("commits/" + config["branch"])["sha"] != os.environ["RELEASE_SHA"]:
        raise RuntimeError("A branch avançou; esta publicação ficou obsoleta.")


def select_components(config, revisions, sha):
    selected = []
    for component, service in config["services"].items():
        base = revisions.get(component, "")
        if not re.fullmatch(r"[0-9a-f]{40}", base):
            raise RuntimeError("Referência de produção inválida.")
        # Se a referência saiu do histórico, reconstruir o componente inteiro.
        exists = subprocess.run(["git", "cat-file", "-e", base + "^{commit}"], capture_output=True)
        if exists.returncode:
            selected.append(component)
            continue
        diff = subprocess.check_output(["git", "diff", "--name-only", "-z", base, sha, "--"])
        paths = [p.decode() for p in diff.split(b"\0") if p]
        if any(relevant(path, service) for path in paths):
            selected.append(component)
    return selected


def relevant(path, service):
    if path.startswith(".github/"):
        return True
    if path.endswith(".md") or any(part in {"docs", "tests", "__tests__"} for part in Path(path).parts):
        return False
    return any(prefix == "." or path == prefix or path.startswith(prefix + "/") for prefix in service["watch"])


def build_package(directory, config, revisions, selected, parts):
    identifier = "-".join(parts)
    images = {}
    for component in selected:
        service = config["services"][component]
        tag = service["image"] + ":git-" + identifier
        print("Construindo " + component + " em linux/amd64.", flush=True)
        run(["docker", "build", "--platform", "linux/amd64", "--label",
             "org.opencontainers.image.revision=" + parts[0], "--label",
             "org.opencontainers.image.source=https://github.com/" + os.environ["GITHUB_REPOSITORY"],
             "-t", tag, service["context"]])
        info = json.loads(subprocess.check_output(["docker", "image", "inspect", tag]))[0]
        images[component] = {"tag": tag, "id": info["Id"]}
    archive = directory / "images.tar.gz"
    save = subprocess.Popen(["docker", "image", "save", *[i["tag"] for i in images.values()]], stdout=subprocess.PIPE)
    try:
        with gzip.open(archive, "wb", compresslevel=1) as output:
            shutil.copyfileobj(save.stdout, output, length=1024 * 1024)
    finally:
        save.stdout.close()
    if save.wait(timeout=60) or archive.stat().st_size > 2 * 1024**3:
        raise RuntimeError("Falha ao empacotar imagens ou limite de 2 GiB excedido.")
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    manifest = {"format": 1, "project": config["project"], "sha": parts[0], "run_id": parts[1],
                "attempt": parts[2], "validation_run_id": os.environ["VALIDATION_RUN_ID"],
                "baselines": {c: revisions[c] for c in selected}, "images": images, "archive_sha256": digest}
    (directory / "release.json").write_text(json.dumps(manifest))
    (directory / "authorization.json").write_text(json.dumps({"token": os.environ["GH_TOKEN"]}))


def main():
    os.umask(0o077)
    config = json.loads(Path(".github/nautilus.json").read_text())
    parts = [os.environ["RELEASE_SHA"], os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"]]
    if not re.fullmatch(r"[0-9a-f]{40}", parts[0]) or any(not re.fullmatch(r"[1-9][0-9]*", p) for p in parts[1:]):
        raise RuntimeError("Identificação de publicação inválida.")
    gate(config)
    with tempfile.TemporaryDirectory(prefix="nautilus-publish-") as temporary:
        directory = Path(temporary)
        key, known_hosts = directory / "key", directory / "known_hosts"
        key.write_text(os.environ["NAUTILUS_DEPLOY_SSH_KEY"].rstrip() + "\n")
        known_hosts.write_text(os.environ["NAUTILUS_DEPLOY_KNOWN_HOSTS"].rstrip() + "\n")
        host = os.environ["NAUTILUS_DEPLOY_HOST"]
        if not re.fullmatch(r"[a-zA-Z0-9.-]+", host):
            raise RuntimeError("Host inválido.")
        ssh = ["ssh", "-i", str(key), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
               "-o", "StrictHostKeyChecking=yes", "-o", "UserKnownHostsFile=" + str(known_hosts),
               "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3", "root@" + host]
        current = json.loads(subprocess.check_output(ssh + ["current"], timeout=45))
        if current.get("blocked") or current.get("project") != config["project"]:
            raise RuntimeError("O servidor exige conferência antes de outra publicação.")
        selected = select_components(config, current["revisions"], parts[0])
        if not selected:
            print("Nenhuma alteração de aplicação desde a última publicação.")
            return 0
        build_package(directory, config, current["revisions"], selected, parts)
        gate(config)
        upload = subprocess.Popen(ssh + ["receive", *parts], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            with tarfile.open(fileobj=upload.stdin, mode="w|") as bundle:
                for name in ("release.json", "authorization.json", "images.tar.gz"):
                    bundle.add(directory / name, arcname=name)
            upload.stdin.close()
            upload.stdin = None
            output, _ = upload.communicate(timeout=60)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            upload.kill()
            upload.wait()
            raise RuntimeError("Transferência não confirmada; conferir o servidor.") from None
        if upload.returncode or json.loads(output).get("release") != "-".join(parts):
            raise RuntimeError("O servidor não confirmou o recebimento.")
        deadline, previous = time.monotonic() + 3900, None
        while time.monotonic() < deadline:
            try:
                result = subprocess.run(ssh + ["status", *parts], capture_output=True, timeout=45)
            except subprocess.TimeoutExpired:
                time.sleep(10)
                continue
            if result.returncode:
                time.sleep(10)
                continue
            state = json.loads(result.stdout)
            if state != previous:
                print(json.dumps(state, ensure_ascii=False), flush=True)
                previous = state
            if state.get("status") == "success":
                return 0
            if state.get("status") in {"rejected", "blocked", "rolled_back", "rollback_failed"}:
                return 1
            time.sleep(10)
        raise RuntimeError("Acompanhamento excedeu o prazo; conferir o servidor antes de repetir.")


if __name__ == "__main__":
    raise SystemExit(main())
