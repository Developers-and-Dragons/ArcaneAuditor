# Docker — Arcane Auditor CLI

Definition files only. No image publishing or registry integration is configured.

## Source-run vs binary-run

| Image | Description | Use case |
|-------|-------------|----------|
| **cli-src** | Runs the CLI from source using `uv` and project dependencies baked into the image. | Development, CI experimentation, or environments where you do not want to prebuild the Linux binary. |
| **cli-binary** | Runs the built Linux CLI executable as a single binary. | CI, production-style usage, or minimal runtime images. |

## Build examples

From the repository root:

```bash
# Source-run (no prebuilt binary required)
docker build -f docker/Dockerfile.cli-src -t arcane-auditor-cli .

# Binary-run (requires a Linux-built CLI binary first)
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
docker run --rm -v "$PWD:/work" -w /work arcane-auditor-cli --help

# Analyze a zip file
docker run --rm -v "$PWD:/work" -w /work arcane-auditor-cli review-app /work/samples/templates.zip

# CI preset (quiet, JSON, default output file)
docker run --rm -v "$PWD:/work" -w /work arcane-auditor-cli review-app /work/samples/templates.zip --ci
```

These are definition files only: you build and run images locally or in your own CI. No Docker registry or publish step is included in this repo.
