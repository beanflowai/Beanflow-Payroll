# CLAUDE.md - Beanflow-Payroll Project Configuration

> **Note**: This project uses Claude Code Skill system. Development standards are managed through modular Skills for on-demand loading and better token efficiency.

---

## Project Overview

**Beanflow-Payroll** is a comprehensive Canadian payroll management system with a modern frontend-backend separation architecture.

- **Version**: 0.1.0
- **Backend**: Python 3.11+ / FastAPI / Pydantic / Supabase
- **Frontend**: Svelte 5 / SvelteKit / TypeScript / TailwindCSS 4
- **Database**: Supabase (PostgreSQL)
- **Package Management**: Python uses `uv`, Frontend uses `npm`

---

## Skill System Architecture

This project uses Claude Code's Skill system to manage development standards. Skills are located in `.claude/skills/` directory, and Claude will automatically load relevant standards based on task type.

### Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| **core-architecture** | Core architecture principles - frontend-backend separation, stateless backend, explicit parameters | API design, architecture decisions |
| **workflow-policies** | Workflow policies - plan approval, single-task focus, Git commit policies | Task management, Git operations |
| **backend-development** | Backend development guide - Python/FastAPI, type safety, camelCase fields | Python code, FastAPI development |
| **frontend-development** | Frontend development guide - Svelte 5 Runes, TypeScript strict mode, TailwindCSS | Svelte components, UI development |
| **payroll-domain** | Canadian payroll domain knowledge - CPP, EI, tax calculations, vacation pay | Payroll calculations, tax rules |
| **tax-rates-2025** | 2025 tax rates quick reference - CPP/EI/federal/provincial rates and brackets | Tax rates, brackets, quick lookup |
| **vacation-holidays** | Statutory holidays and vacation pay quick reference by province | Holidays, vacation pay, stat days |
| **error-handling** | Error handling transparency - prohibit hiding errors, transparent degradation, graceful failures | Error handling, fallback strategies |
| **supabase-patterns** | Supabase usage patterns - database queries, RLS policies, migrations, real-time | Supabase, database operations, auth |

---

## Quick Reference

### Development Commands

```bash
# Start development servers (both frontend and backend)
./start-dev.sh

# Backend only
cd backend
uv sync                    # Install dependencies
uv run uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend
npm install               # Install dependencies
npm run dev               # Start dev server
npm run check             # Type check
npm run lint              # Lint check
```

### Package Management

```bash
# Backend (Python + uv)
cd backend
uv sync              # Install dependencies
uv add <package>     # Add new package
uv run <command>     # Run command

# Frontend (npm)
cd frontend
npm install          # Install dependencies
npm install <pkg>    # Add new package
npm run dev          # Dev server
```

---

## Key Development Principles

### Rule-09: Plan Approval Requirements

**Requires approval**:
- New UI features, API contract changes, architecture modifications
- External integrations, database schema changes

**No approval needed**:
- Bug fixes, refactoring, documentation, tests, UI improvements

### Rule-10: Single-Task Focus

- Strictly follow single-task principle
- When discovering unrelated issues, record them to TODO list
- Only process new tasks after completing current task

### Rule-11: No Backward Compatibility in Development Stage

- Project is in development stage, not in production
- Can make breaking changes directly
- No need for optional parameter transitions

### Rule-12: Git Commit Policy

**Auto-commit is strictly prohibited**. Only create Git commits when user explicitly requests:
- User says "please commit these changes"
- User says "create a commit"

---

## Project Structure

```
Beanflow-Payroll/
├── .claude/
│   ├── settings.local.json     # Claude Code permissions
│   └── skills/                  # Development standards
│       ├── core-architecture/
│       ├── workflow-policies/
│       ├── backend-development/
│       ├── frontend-development/
│       ├── payroll-domain/
│       ├── tax-rates-2025/
│       ├── vacation-holidays/
│       ├── error-handling/
│       └── supabase-patterns/
├── backend/                     # Python FastAPI backend
│   ├── .venv/                  # Python virtual environment
│   ├── app/
│   │   ├── api/                # API routes
│   │   ├── services/           # Business logic
│   │   ├── models/             # Data models
│   │   └── utils/              # Utilities
│   ├── supabase/               # Supabase migrations
│   └── tests/                  # Backend tests
├── frontend/                    # Svelte frontend
│   ├── src/
│   │   ├── routes/             # SvelteKit routes
│   │   └── lib/                # Components and utilities
│   └── static/                 # Static assets
├── docs/                        # Project documentation
│   └── ui/                     # UI specifications
└── CLAUDE.md                   # This file
```

---

## Tech Stack Overview

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Frontend | Svelte 5 + TypeScript + TailwindCSS | UI, forms, data visualization |
| Backend | FastAPI + Pydantic + async | Business logic, payroll calculations |
| Database | Supabase (PostgreSQL) | Data persistence, auth |
| Auth | Supabase Auth | User authentication |

---

## Development Checklist

Before starting any development task:

- [ ] Does this require plan approval? (Rule-09)
- [ ] Am I in the correct environment? (backend/.venv or frontend/node_modules)
- [ ] Am I focusing only on the current task? (Rule-10)
- [ ] Do my changes follow type safety requirements?
- [ ] Have I tested the changes appropriately?

---

## Extended Reading

- **Detailed Standards**: See SKILL.md files under `.claude/skills/`
- **Project Documentation**: See `docs/` directory
- **UI Specifications**: See `docs/ui/` directory

---

_Last updated: 2025-12-18 - Added tax-rates-2025 and vacation-holidays quick reference skills_
