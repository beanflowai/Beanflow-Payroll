# Beanflow Payroll

> Open-source Canadian payroll management system

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20%2B-brightgreen.svg)](https://nodejs.org)

Beanflow Payroll is a complete, open-source payroll management system designed specifically for Canadian businesses. Handle employee payroll, calculate CPP/EI deductions, manage federal and provincial taxes, and stay compliant with CRA requirements—all in one modern, self-hosted platform.

## Why Beanflow Payroll?

- **Complete Canadian Payroll Calculations** – Accurate CPP (including CPP2), EI, federal tax, and provincial tax calculations for all Canadian provinces and territories (excluding Quebec)
- **Modern Tech Stack** – Built with Svelte 5, FastAPI, and Supabase for a fast, responsive user experience
- **Self-Hosted & Privacy-Focused** – Keep your sensitive payroll data on your own infrastructure
- **CRA Compliant** – Remittance tracking, YTD calculations, and proper deduction handling

## Features

### Core Payroll

- **Employee Management** – Track employee profiles, employment status, and tax information
- **Payroll Runs** – Draft, review, and approve payroll with an intuitive workflow
- **Pay Frequencies** – Support for weekly, bi-weekly, semi-monthly, and monthly pay periods
- **YTD Tracking** – Automatic year-to-date calculations for accurate deductions

### Deductions & Taxes

- **CPP & EI Calculations** – Including CPP2 enhanced contributions and EI premium rates
- **Federal Tax** – Current year tax brackets and basic personal amounts
- **Provincial Tax** – All provinces and territories supported (excluding Quebec)
- **Multiple Deductions** – Support for custom deductions and company-specific benefits

### Compliance & Reporting

- **CRA Remittance Tracking** – Track remittance amounts with due date alerts
- **Payroll Register** – Comprehensive reports for each pay run
- **Paystub Generation** – Professional, CRA-compliant paystubs (PDF export coming soon)

### Employee Self-Service

- **Paystub Access** – Employees can view and download their paystubs
- **Profile Management** – Employees can update their personal and tax information
- **Leave Balances** – Track vacation and leave accruals

### Developer Experience

- **Type-Safe Frontend** – TypeScript strict mode with Svelte 5 Runes
- **Well-Documented API** – RESTful endpoints built on FastAPI
- **Modern UI** – Clean, responsive interface built with TailwindCSS 4

## Tech Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Frontend | Svelte 5, SvelteKit, TypeScript, TailwindCSS 4 |
| Backend  | Python 3.11+, FastAPI, Pydantic               |
| Database | Supabase (PostgreSQL)                         |
| Auth     | Supabase Auth (Google OAuth)                  |

## Screenshots

> Screenshots coming soon

## Quick Start

### Prerequisites

- **Node.js** 20 or higher
- **Python** 3.11 or higher
- **uv** (Python package manager) – [Installation guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- **Supabase account** – [Sign up free](https://supabase.com)

### 1. Clone the Repository

```bash
git clone https://github.com/beanflow/payroll.git
cd payroll
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Run development server
uv run uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env with your API endpoints

# Run development server
npm run dev
```

### 4. Initialize Database

```bash
# Link to your Supabase project
supabase link

# Push migrations
supabase db push
```

Visit `http://localhost:5173` to see the application.

## Supported Provinces

Beanflow Payroll supports all Canadian provinces and territories:

- Alberta (AB)
- British Columbia (BC)
- Manitoba (MB)
- New Brunswick (NB)
- Newfoundland and Labrador (NL)
- Northwest Territories (NT)
- Nova Scotia (NS)
- Nunavut (NU)
- Ontario (ON)
- Prince Edward Island (PE)
- Saskatchewan (SK)
- Yukon (YT)

> **Note:** Quebec (QC) is not currently supported due to its unique tax system (QPP and QST). Support is planned for a future release.

## Roadmap

| Phase | Feature                   | Status         |
|-------|---------------------------|----------------|
| 1     | Data Layer & Schema       | Complete       |
| 2     | Payroll Calculations      | Complete       |
| 3     | Paystub PDF Generation    | In Progress    |
| 4     | API Integration           | Complete       |
| 5     | Testing & Validation      | Planned        |
| 6     | T4 Year-End Processing    | Planned        |
| 7     | ROE Generation            | Planned        |
| 8     | Quebec Support            | Planned        |

## Contributing

We welcome contributions from the community! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:

- You are free to use, modify, and distribute this software
- Any modifications must be released under the same license
- If you use this software to provide a service over a network, you must provide the source code to your users

For more details, see the [LICENSE](LICENSE) file.

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/beanflow/payroll/issues)
- **Discussions:** [GitHub Discussions](https://github.com/beanflow/payroll/discussions)

---

Made with care by the Beanflow team
