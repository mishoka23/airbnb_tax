#!/usr/bin/env python3
"""Refresh production containers with latest code without deleting the database."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENV_FILE = ".env.production"
COMPOSE_FILE = "docker-compose.prod.yml"


def run_cmd(args: list[str], label: str) -> None:
    print(f"\n[{label}] {' '.join(args)}")
    subprocess.run(args, cwd=ROOT, check=True)


def get_docker_command() -> str:
    docker = shutil.which("docker")
    if docker:
        return docker

    fallback = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")
    if fallback.exists():
        return str(fallback)

    raise FileNotFoundError(
        "Docker CLI was not found. Install Docker Desktop or add docker.exe to PATH."
    )


def compose_base(docker: str) -> list[str]:
    return [docker, "compose", "--env-file", ENV_FILE, "-f", COMPOSE_FILE]


def main() -> int:
    docker = get_docker_command()

    try:
        run_cmd([docker, "info"], "Check Docker")

        base = compose_base(docker)
        run_cmd(base + ["up", "-d", "--build"], "Rebuild And Restart Services")
        run_cmd(base + ["exec", "backend", "python", "manage.py", "migrate"], "Apply Migrations")
        run_cmd(base + ["exec", "backend", "python", "manage.py", "collectstatic", "--noinput"], "Collect Static")
        run_cmd(["powershell", "-Command", "Invoke-WebRequest http://localhost/api/health/ -UseBasicParsing"], "Health Check")

        print("\nRefresh complete. Database volume was preserved.")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\nCommand failed with exit code {exc.returncode}.")
        return exc.returncode
    except FileNotFoundError as exc:
        print(f"\n{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
