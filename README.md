# Google Cloud Workflow for Alfred

[![Latest Release](https://img.shields.io/github/v/release/ndpete/alfred-gcloud-workflow?style=flat-square&color=blue)](https://github.com/ndpete/alfred-gcloud-workflow/releases/latest)
[![Download Workflow](https://img.shields.io/badge/Download-.alfredworkflow-success?style=flat-square&logo=apple)](https://github.com/ndpete/alfred-gcloud-workflow/releases/latest/download/alfred-gcloud-workflow.alfredworkflow)
[![CI](https://github.com/ndpete/alfred-gcloud-workflow/actions/workflows/test.yml/badge.svg)](https://github.com/ndpete/alfred-gcloud-workflow/actions/workflows/test.yml)

Fast shortcuts to Google Cloud Console products and projects in Alfred, powered by a lightweight, zero-dependency pure Python engine.

*Created by Nathan Peterson. Built with a fast, zero-dependency Python 3 standard library engine featuring sub-millisecond fuzzy search, native macOS Gatekeeper compatibility, and automatic update checks.*

## Highlights

- **Zero Gatekeeper Friction**: Runs on macOS built-in `/usr/bin/python3` (Apple-signed), eliminating quarantine warnings and developer verification blocks.
- **Featherweight**: Tiny ~24 KB bundle (down from 35 MB compiled Go binaries).
- **Sub-Millisecond Search**: Custom subsequence fuzzy matcher with consecutive-character bonuses and recency scoring.
- **Automatic Background Updates**: Non-blocking checks against GitHub Releases notify you directly inside Alfred when updates are published.

## Download

Download the latest `.alfredworkflow` bundle from [Releases](https://github.com/ndpete/alfred-gcloud-workflow/releases/latest) and double-click to install into Alfred.

## Usage

Commands:
- `g <project>` ↩️ `<product>` ➡️ Opens the selected GCP product in that project.
- `g-refresh` ➡️ Updates cached GCP projects via `gcloud` CLI.
- `g -` or `g update` / `g version` / `g refresh` ➡️ Displays workflow utility commands and version info.

### Refresh projects list

Run `g-refresh` (or type `g -refresh`) in Alfred to update your cached projects.

### Open product page

1. Type `g <project query>` (e.g. `g prod` or `g terraform`).
2. Press ↩️ to select the project.
3. Type `<product query>` (e.g. `run`, `storage`, `gke`, `bigquery`).
4. Press ↩️ to open the console in your default browser.

### Configuration

- **`hotkey`**: Trigger keyword in Alfred (default: `g`). Change to `gcp` for commands like `gcp <query>` and `gcp-refresh`.
- **`authuser`**: Useful when logged into multiple Google accounts (e.g., `1` or `user@domain.com`). Appends `&authuser=...` to console URLs.

## Requirements

- **macOS** with system Python 3 (`/usr/bin/python3`, pre-installed on macOS 12+).
- **Google Cloud SDK** (`gcloud`) authenticated (`gcloud auth login`).

## Development

```bash
# Run linting with ruff
make lint

# Run unit tests with pytest
make test

# Package the workflow zip into target/
make workflow

# Build and trigger installation in Alfred
make install
```
