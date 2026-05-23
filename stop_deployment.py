#!/usr/bin/env python3
"""Stop all project deployment services on this computer."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENV_FILE = ".env.production"
COMPOSE_FILE = "docker-compose.prod.yml"
CLOUDFLARED_CONTAINER = "airbnb_tax-cloudflared"


def run_cmd(args: list[str], label: str, check: bool = True) -> int:
    print(f"\n[{label}] {' '.join(args)}")
    completed = subprocess.run(args, cwd=ROOT, check=False)
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, args)
    return completed.returncode


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
    try:
        docker = get_docker_command()
        run_cmd([docker, "info"], "Check Docker")

        # Stop and remove the production stack containers (keeps DB volume/data).
        run_cmd(compose_base(docker) + ["down"], "Stop Production Stack")

        # Stop/remove the quick Cloudflare tunnel container if present.
        run_cmd([docker, "rm", "-f", CLOUDFLARED_CONTAINER], "Stop Cloudflare Tunnel", check=False)

        print("\nDeployment stopped. Database data is preserved in Docker volumes.")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\nCommand failed with exit code {exc.returncode}.")
        return exc.returncode
    except FileNotFoundError as exc:
        print(f"\n{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
