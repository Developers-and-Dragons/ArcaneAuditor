# Docker — Arcane Auditor CLI

Definition files only. No image publishing or registry integration is configured.

## Source-run vs binary-run

| Image | Description | Use case |
|-------|--------------|----------|
| **cli-src** | Runs the CLI from source with `uv` and project dependencies. | CI, development, or when you don't have a built binary. |
| **cli-binary** | Runs the built Linux CLI executable (single binary). Best for production-style runs or minimal images; uses local Linux build output or an extracted release binary. |

## Build examples

From the repository root:

```bash
# Source-run (no pre-built binary needed)
docker build -f docker/Dockerfile.cli-src -t arcane-auditor-cli-src .

# Binary-run (requires dist/ArcaneAuditorCLI from a Linux build first)
./scripts/build-linux-cli.sh
docker build -f docker/Dockerfile.cli-binary -t arcane-auditor-cli .
```

To use a specific binary path for the binary image:

```bash
docker build -f docker/Dockerfile.cli-binary --build-arg BINARY_PATH=path/to/ArcaneAuditorCLI -t arcane-auditor-cli .
```

## Run examples

```bash
# Help
docker run --rm arcane-auditor-cli-src --help
docker run --rm arcane-auditor-cli --help

# Analyze an app directory (mount it read-only)
docker run --rm -v /path/to/myapp:/app/in:ro arcane-auditor-cli-src review-app /app/in
docker run --rm -v /path/to/myapp:/app/in:ro arcane-auditor-cli review-app /app/in

# CI preset (quiet, JSON, default output file)
docker run --rm -v /path/to/myapp:/app/in:ro arcane-auditor-cli review-app /app/in --ci
```

These are definition files only: you build and run images locally or in your own CI. No Docker registry or publish step is included in this repo.
