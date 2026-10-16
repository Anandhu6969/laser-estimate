# Laser Estimate

A Windows desktop application built with Python to simplify quotation generation for laser-cutting work.

## Overview

Laser Estimate helps calculate material and cutting costs, manage estimates, and generate PDF quotations through a desktop interface.

## Features

- **Simple Cutting:** Calculate quotations using area-based pricing.
- **Design Heavy:** Calculate quotations using material weight and cutting time.
- **Material and Pricing Management:** Configure material densities and pricing rates.
- **Estimate Management:** Save and review previous estimates.
- **PDF Quotations:** Generate professional quotation documents.
- **Local Data Storage:** Store estimates locally using SQLite.
- **Windows Application:** Package the application as a standalone executable and installer.

## Tech Stack

- **Python 3.11** — Core application logic
- **PySide6 / Qt** — Desktop graphical user interface
- **SQLite** — Local database
- **pytest** — Automated testing
- **PyInstaller** — Executable packaging
- **Inno Setup** — Windows installer creation

## Project Structure

```text
laser-estimate/
├── app/
│   ├── calculations/
│   ├── database/
│   ├── models/
│   ├── services/
│   ├── ui/
│   └── utils/
├── assets/
├── installer/
├── tests/
├── requirements.txt
├── requirements-build.txt
├── LaserEstimate.spec
└── README.md
```

## Getting Started

1. Install Python 3.11.
2. Clone the repository.
3. Create and activate a virtual environment.
4. Install the application dependencies.
5. Run the application using the project's entry point.

```powershell
git clone https://github.com/Anandhu6969/laser-estimate.git
cd laser-estimate

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m app.main
```

## Testing

Run the automated test suite with:

```powershell
pytest
```

## Packaging

The project includes PyInstaller and Inno Setup configuration files for building a Windows executable and installer.

## License

No license has been added yet.
