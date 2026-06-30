# 🎬 HyperDeck Pipeline

This repository provides a modular, extensible pipeline for syncing, processing, and archiving recordings from Blackmagic HyperDeck Studio recorders. It is designed to run on macOS or Linux servers (e.g., Mac Studio) with scheduled cron jobs.

## Features

- 🔍 Scan HyperDeck storage (SD1, SD2, USB) over the network
- 🗂️ Filter and export file inventories by type
- ☁️ Upload recordings to Google Drive or other remote storage
- 📨 Email summary reports to the media team
- 🧹 Clean up SD cards after confirmation
- 🛠️ Modular architecture for clean maintenance

## Directory Layout

- `bin/`: CLI entry points
- `lib/`: Core functionality
- `config/`: Configurable YAML settings
- `cron/`: Sample cron job triggers
- `logs/`: Runtime logs and diagnostics
- `tests/`: Unit tests

## Getting Started

1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/hyperdeck_pipeline.git
   cd hyperdeck_pipeline