# BeanFlow Payroll - Standalone Frontend Architecture

**Duration**: Phase 0 (Before Phase 1)
**Complexity**: Medium
**Prerequisites**: None

> **Last Updated**: 2025-12-07
> **Architecture Version**: v3.0 (Standalone Product)

---

## 🎯 Overview

BeanFlow Payroll is a **standalone product** with its own frontend application, separate from BeanFlow Bookkeeping. This document defines the architecture for the independent payroll frontend.

### Product Positioning

```
┌─────────────────────────────────────────────────────────────────┐
│                         BeanFlow Suite                           │
├─────────────────────────────┬───────────────────────────────────┤
│   BeanFlow Payroll          │   BeanFlow Bookkeeping            │
│   payroll.beanflow.com      │   app.beanflow.com                │
├─────────────────────────────┼───────────────────────────────────┤
│   Target: HR, Payroll       │   Target: Accountants,            │
│   admins, Small biz owners  │   Bookkeepers, CFOs               │
├─────────────────────────────┼───────────────────────────────────┤
│   Features:                 │   Features:                       │
│   • Employee management     │   • Transaction recording         │
│   • Payroll calculations    │   • Invoice management            │
│   • Paystub generation      │   • Financial reports             │
│   • CRA compliance          │   • AI assistant                  │
│   • Remittance tracking     │   • Beancount ledgers             │
└─────────────────────────────┴───────────────────────────────────┘
                    │
                    ▼
         [Optional Integration]
         "Run Payroll" → Journal Entry
```

---

## 🏗️ Repository Structure

### Option A: Monorepo with Separate Apps (Recommended)

```
BeanFlow-LLM/
├── backend/                      # Shared FastAPI backend
│   └── app/
│       ├── api/v1/
│       │   ├── payroll.py       # Payroll endpoints
│       │   └── ...              # Bookkeeping endpoints
│       └── services/payroll/    # Payroll business logic
│
├── frontend/                     # BeanFlow Bookkeeping
│   ├── src/
│   │   ├── routes/(app)/        # Bookkeeping routes
│   │   └── lib/
│   │       ├── styles/design-system/  # Shared design system
│   │       └── components/v2-current/ # Shared components
│   └── package.json
│
├── payroll-frontend/             # NEW: BeanFlow Payroll (standalone)
│   ├── src/
│   │   ├── routes/              # Payroll routes
│   │   └── lib/
│   │       ├── components/      # Payroll-specific components
│   │       └── shared/          # Links to frontend/src/lib
│   ├── package.json
│   └── svelte.config.js
│
└── shared/                       # NEW: Shared packages (optional)
    ├── ui-components/           # Extracted shared components
    └── design-tokens/           # Design system tokens
```

### Option B: Separate Repository

```
# Separate repo: beanflow-payroll
beanflow-payroll/
├── src/
│   ├── routes/
│   └── lib/
├── package.json
└── ...

# Install shared components as npm package
npm install @beanflow/ui-components
```

**Recommendation**: Start with **Option A (Monorepo)** for faster development, migrate to Option B later if needed.

---

## 📁 Payroll Frontend Structure

```
payroll-frontend/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte              # Root layout
│   │   ├── +layout.ts                  # Root load function
│   │   ├── +page.svelte                # Landing / Marketing page
│   │   │
│   │   ├── (auth)/                     # Auth group (no layout)
│   │   │   ├── login/
│   │   │   │   └── +page.svelte        # Google OAuth login
│   │   │   └── callback/
│   │   │       └── +page.svelte        # OAuth callback handler
│   │   │
│   │   └── (app)/                      # Authenticated app group
│   │       ├── +layout.svelte          # App shell layout
│   │       ├── +layout.ts              # Auth guard
│   │       │
│   │       ├── dashboard/
│   │       │   └── +page.svelte        # Overview dashboard
│   │       │
│   │       ├── employees/
│   │       │   ├── +page.svelte        # Employee list
│   │       │   ├── new/
│   │       │   │   └── +page.svelte    # Add employee form
│   │       │   └── [id]/
│   │       │       ├── +page.svelte    # Employee detail
│   │       │       └── edit/
│   │       │           └── +page.svelte
│   │       │
│   │       ├── payroll/
│   │       │   ├── +page.svelte        # Current pay period (main view)
│   │       │   ├── run/
│   │       │   │   └── +page.svelte    # Run payroll wizard
│   │       │   └── history/
│   │       │       ├── +page.svelte    # Past payroll runs
│   │       │       └── [id]/
│   │       │           └── +page.svelte # Run detail
│   │       │
│   │       ├── reports/
│   │       │   ├── +page.svelte        # Reports hub
│   │       │   ├── remittance/
│   │       │   │   └── +page.svelte    # CRA remittance report
│   │       │   └── ytd/
│   │       │       └── +page.svelte    # Year-to-date summary
│   │       │
│   │       └── settings/
│   │           ├── +page.svelte        # General settings
│   │           ├── company/
│   │           │   └── +page.svelte    # Company info
│   │           └── integration/
│   │               └── +page.svelte    # Link to Bookkeeping
│   │
│   ├── lib/
│   │   ├── components/                 # Payroll-specific components
│   │   │   ├── employees/
│   │   │   │   ├── EmployeeTable.svelte
│   │   │   │   ├── EmployeeForm.svelte
│   │   │   │   └── EmployeeCard.svelte
│   │   │   ├── payroll/
│   │   │   │   ├── PayrollTable.svelte
│   │   │   │   ├── PayPeriodNavigator.svelte
│   │   │   │   ├── DeductionBreakdown.svelte
│   │   │   │   └── PayrollSummary.svelte
│   │   │   ├── paystub/
│   │   │   │   └── PaystubPreview.svelte
│   │   │   └── layout/
│   │   │       ├── AppShell.svelte
│   │   │       ├── Sidebar.svelte
│   │   │       └── Header.svelte
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.ts                 # Auth state
│   │   │   ├── employees.ts            # Employee data
│   │   │   ├── payroll.ts              # Payroll state
│   │   │   └── company.ts              # Company settings
│   │   │
│   │   ├── api/
│   │   │   ├── client.ts               # Base API client
│   │   │   ├── auth.ts                 # Auth API
│   │   │   ├── employees.ts            # Employee API
│   │   │   └── payroll.ts              # Payroll API
│   │   │
│   │   ├── types/
│   │   │   ├── employee.ts
│   │   │   ├── payroll.ts
│   │   │   └── api.ts
│   │   │
│   │   └── utils/
│   │       ├── formatters.ts           # Currency, date formatters
│   │       └── validators.ts           # SIN, form validators
│   │
│   ├── app.css                         # Main styles (imports design system)
│   ├── app.html                        # HTML template
│   └── hooks.server.ts                 # Server hooks (auth)
│
├── static/
│   ├── favicon.svg
│   └── logo.svg
│
├── package.json
├── svelte.config.js
├── tailwind.config.js
├── vite.config.ts
└── tsconfig.json
```

---

## 🔗 Shared Resources Strategy

### Design System Sharing

The payroll frontend will share the design system from the main frontend:

```javascript
// payroll-frontend/tailwind.config.js
import sharedConfig from '../frontend/tailwind.config.js';

export default {
  ...sharedConfig,
  content: [
    './src/**/*.{html,js,svelte,ts}',
    // Include shared components
    '../frontend/src/lib/styles/design-system/**/*.css',
  ],
};
```

```css
/* payroll-frontend/src/app.css */
/* Import shared design system */
@import '../../frontend/src/lib/styles/design-system/index.css';

/* Payroll-specific overrides (if any) */
```

### Component Sharing: Symlink + Build-time Copy

**Strategy**: Use symlinks for development, copy files during Docker build.

This approach provides:
- ✅ Fast development with symlinks (changes reflect immediately)
- ✅ No deployment issues (files are physically copied during build)
- ✅ No Windows compatibility concerns for solo developer on Mac

#### Development: Symlinks

```bash
# Create symlinks to shared components
cd payroll-frontend/src/lib
ln -s ../../../frontend/src/lib/styles styles-shared
ln -s ../../../frontend/src/lib/components/v2-current/base shared-base
ln -s ../../../frontend/src/lib/components/v2-current/icons shared-icons
```

#### Production: Build Script Copies Files

Docker cannot follow symlinks to files outside the build context. The build script resolves this by copying files before Docker build.

See [Docker Build Strategy](#-docker-build-strategy) section below for details.

### Components to Share

| Component Category | Path | Share? |
|-------------------|------|--------|
| Design System | `styles/design-system/` | ✅ Yes |
| Base components | `v2-current/base/` | ✅ Yes |
| Icons | `v2-current/icons/` | ✅ Yes |
| Modals | `v2-current/modals/` | ✅ Yes |
| Forms | `v2-current/forms/` | ⚠️ Some |
| Layout | `v2-current/layout/` | ❌ Payroll has own |

---

## 🔐 Authentication Architecture

### Shared Auth Flow

Both products use the same Google OAuth flow and user database:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Payroll Login  │     │  Shared OAuth   │     │  Bookkeeping    │
│  payroll.beanflow│────►│  Google OAuth   │◄────│  app.beanflow   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Supabase Auth  │
                        │  + users table  │
                        │  + feature flags│
                        └─────────────────┘
```

### Feature Flags

```sql
-- users table (shared)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT,
  -- Feature flags
  has_payroll_access BOOLEAN DEFAULT false,
  has_bookkeeping_access BOOLEAN DEFAULT false,
  -- Subscription info
  payroll_subscription_tier TEXT,  -- 'free', 'pro', 'enterprise'
  bookkeeping_subscription_tier TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Auth Implementation

```typescript
// payroll-frontend/src/lib/api/auth.ts
import { supabase } from './client';

export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/callback`,
      scopes: 'email profile',
    },
  });
  return { data, error };
}

export async function checkPayrollAccess(userId: string): Promise<boolean> {
  const { data } = await supabase
    .from('users')
    .select('has_payroll_access')
    .eq('id', userId)
    .single();

  return data?.has_payroll_access ?? false;
}
```

---

## 🌐 API Architecture

### Shared Backend with Route Prefix

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter

# Existing routes
from .invoices import router as invoices_router
from .transactions import router as transactions_router

# Payroll routes (new)
from .payroll import router as payroll_router

api_router = APIRouter()

# Bookkeeping routes
api_router.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])

# Payroll routes
api_router.include_router(payroll_router, prefix="/payroll", tags=["payroll"])
```

### CORS Configuration

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

allowed_origins = [
    "https://app.beanflow.com",      # Bookkeeping
    "https://payroll.beanflow.com",  # Payroll
    "http://localhost:5173",          # Dev: Bookkeeping
    "http://localhost:5174",          # Dev: Payroll
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Client

```typescript
// payroll-frontend/src/lib/api/client.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const response = await fetch(`${API_BASE}/api/v1${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Payroll-specific API calls
export const payrollApi = {
  listEmployees: () => apiClient<Employee[]>('/payroll/employees'),
  createEmployee: (data: CreateEmployee) =>
    apiClient<Employee>('/payroll/employees', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  // ... more endpoints
};
```

---

## 🎨 UI Layout Differences

### Payroll Layout (Simplified)

Unlike Bookkeeping which has AI panel and complex navigation, Payroll has a simpler layout:

```
┌─────────────────────────────────────────────────────┐
│  Header (Logo, Company Name, User Menu)             │
├──────────────┬──────────────────────────────────────┤
│   Sidebar    │                                      │
│   (200px)    │          Main Content                │
│              │                                      │
│  • Dashboard │                                      │
│  • Employees │                                      │
│  • Payroll   │                                      │
│  • Reports   │                                      │
│  • Settings  │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

### No AI Panel

Payroll does not include the AI assistant panel (that's a Bookkeeping feature).

### Navigation Items

```typescript
// payroll-frontend/src/lib/components/layout/navigation.ts
export const navigationItems = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: 'dashboard'
  },
  {
    label: 'Employees',
    href: '/employees',
    icon: 'users'
  },
  {
    label: 'Run Payroll',
    href: '/payroll',
    icon: 'calculator'
  },
  {
    label: 'History',
    href: '/payroll/history',
    icon: 'history'
  },
  {
    label: 'Reports',
    href: '/reports',
    icon: 'chart'
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: 'settings'
  },
];
```

---

## 🔄 Bookkeeping Integration (Optional)

### Integration Settings Page

Users can optionally link their Payroll account to a Bookkeeping company:

```svelte
<!-- payroll-frontend/src/routes/(app)/settings/integration/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';

  let linkedCompany = $state<Company | null>(null);
  let availableCompanies = $state<Company[]>([]);

  onMount(async () => {
    // Fetch available Bookkeeping companies for this user
    availableCompanies = await fetchBookkeepingCompanies();
    linkedCompany = await getLinkedCompany();
  });
</script>

<div class="integration-settings">
  <h2>Link to BeanFlow Bookkeeping</h2>

  {#if linkedCompany}
    <div class="linked-company">
      <p>Currently linked to: <strong>{linkedCompany.name}</strong></p>
      <button onclick={unlinkCompany}>Unlink</button>
    </div>
  {:else}
    <p>Link your payroll to a BeanFlow Bookkeeping company to automatically
       generate journal entries when you run payroll.</p>

    {#if availableCompanies.length > 0}
      <select onchange={linkCompany}>
        <option value="">Select a company...</option>
        {#each availableCompanies as company}
          <option value={company.id}>{company.name}</option>
        {/each}
      </select>
    {:else}
      <p>No Bookkeeping companies found.
         <a href="https://app.beanflow.com">Create one</a> first.</p>
    {/if}
  {/if}
</div>
```

### Run Payroll → Journal Entry

When user runs payroll and is linked to Bookkeeping:

```typescript
// backend/app/services/payroll/payroll_service.py
async def run_payroll_with_integration(
    payroll_run_id: UUID,
    user_id: str,
    linked_ledger_id: str | None = None
) -> PayrollRunResult:
    """
    Run payroll and optionally create Bookkeeping journal entry.
    """
    # 1. Calculate payroll
    result = await self.calculate_payroll(payroll_run_id)

    # 2. Generate paystubs
    await self.generate_paystubs(payroll_run_id)

    # 3. If linked to Bookkeeping, create journal entry
    if linked_ledger_id:
        journal_entry = self._build_payroll_journal_entry(result)
        await beancount_service.create_transaction(
            ledger_id=linked_ledger_id,
            transaction=journal_entry
        )

    return result
```

---

## 🚀 Development Setup

### Initial Setup

```bash
# 1. Create payroll frontend directory
mkdir -p payroll-frontend
cd payroll-frontend

# 2. Initialize SvelteKit
npm create svelte@latest .
# Choose: Skeleton project, TypeScript, ESLint, Prettier

# 3. Install dependencies
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 4. Install shared dependencies
npm install @supabase/supabase-js

# 5. Create symlinks to shared resources
cd src/lib
ln -s ../../../frontend/src/lib/styles styles-shared
ln -s ../../../frontend/src/lib/components/v2-current/base shared-base
ln -s ../../../frontend/src/lib/components/v2-current/icons shared-icons
```

### Development Scripts

```json
// payroll-frontend/package.json
{
  "name": "beanflow-payroll",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite dev --port 5174",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "lint": "eslint .",
    "format": "prettier --write ."
  }
}
```

### Running Both Apps

```bash
# Terminal 1: Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Bookkeeping Frontend
cd frontend
npm run dev  # Port 5173

# Terminal 3: Payroll Frontend
cd payroll-frontend
npm run dev  # Port 5174
```

---

## 📋 Implementation Checklist

### Phase 0: Frontend Setup

- [ ] Create `payroll-frontend/` directory structure
- [ ] Initialize SvelteKit project
- [ ] Configure Tailwind with shared design system
- [ ] Set up symlinks to shared components
- [ ] Create base layout components
- [ ] Implement auth flow (Google OAuth)
- [ ] Create API client
- [ ] Add basic routing structure

### Phase 0.5: Shared Infrastructure

- [ ] Update CORS in backend for payroll domain
- [ ] Add feature flags to users table
- [ ] Create payroll subscription tier logic
- [ ] Test auth flow between both apps

---

## 🔧 Configuration Files

### Vite Config

```typescript
// payroll-frontend/vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5174,
  },
  resolve: {
    alias: {
      '$shared': '../frontend/src/lib',
    },
  },
});
```

### SvelteKit Config

```javascript
// payroll-frontend/svelte.config.js
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    alias: {
      '$lib': './src/lib',
      '$shared': '../frontend/src/lib',
    },
  },
};

export default config;
```

### Environment Variables

```bash
# payroll-frontend/.env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_GOOGLE_CLIENT_ID=your-client-id
```

---

## 🐳 Docker Build Strategy

### Problem: Symlinks Don't Work in Docker

Docker's `COPY` command does not follow symlinks to files outside the build context. If `payroll-frontend/src/lib/shared-base` is a symlink to `../frontend/src/lib/...`, Docker will copy the symlink itself, not the actual files.

### Solution: Build Script Pre-processing

The build script resolves symlinks by copying actual files before Docker build, then optionally restores symlinks after.

### Updated Build Script

Add to `deploy/scripts/build-images.sh`:

```bash
# ==============================================================================
# 构建 Payroll Frontend 镜像
# ==============================================================================
echo -e "${BLUE}[4/4] 构建 Payroll Frontend 镜像...${NC}"
echo -e "  路径: ${PROJECT_ROOT}/payroll-frontend"
echo -e "  镜像: ${REGISTRY_URL}/${PROJECT_NAME}/payroll:${VERSION}"
echo ""

cd "$PROJECT_ROOT"

# ----------------------------------------------------------------------------
# Pre-build: Resolve symlinks by copying actual files
# ----------------------------------------------------------------------------
echo -e "${BLUE}  解析 symlinks，复制共享资源...${NC}"

PAYROLL_LIB="$PROJECT_ROOT/payroll-frontend/src/lib"
FRONTEND_LIB="$PROJECT_ROOT/frontend/src/lib"

# Backup and remove symlinks, copy actual directories
resolve_symlink() {
    local link_path="$1"
    local source_path="$2"
    local link_name=$(basename "$link_path")

    if [ -L "$link_path" ]; then
        echo -e "    Resolving: $link_name"
        rm "$link_path"
        cp -r "$source_path" "$link_path"
    elif [ -d "$link_path" ]; then
        echo -e "    Already resolved: $link_name (skipping)"
    else
        echo -e "    Creating: $link_name"
        cp -r "$source_path" "$link_path"
    fi
}

# Resolve each shared resource
resolve_symlink "$PAYROLL_LIB/styles-shared" "$FRONTEND_LIB/styles"
resolve_symlink "$PAYROLL_LIB/shared-base" "$FRONTEND_LIB/components/v2-current/base"
resolve_symlink "$PAYROLL_LIB/shared-icons" "$FRONTEND_LIB/components/v2-current/icons"

echo -e "${GREEN}  ✓ 共享资源已复制${NC}"
echo ""

# ----------------------------------------------------------------------------
# Docker Build
# ----------------------------------------------------------------------------
docker buildx build \
    --platform linux/amd64 \
    --load \
    --build-arg VITE_API_URL="${VITE_API_URL}" \
    --build-arg VITE_PAYROLL_URL="${VITE_PAYROLL_URL:-https://payroll.beanflow.ai}" \
    -t "${REGISTRY_URL}/${PROJECT_NAME}/payroll:${VERSION}" \
    -t "${REGISTRY_URL}/${PROJECT_NAME}/payroll:latest" \
    -f deploy/nginx/Dockerfile.payroll \
    .

BUILD_RESULT=$?

# ----------------------------------------------------------------------------
# Post-build: Restore symlinks for development
# ----------------------------------------------------------------------------
echo -e "${BLUE}  恢复 symlinks...${NC}"

restore_symlink() {
    local link_path="$1"
    local target_path="$2"

    if [ -d "$link_path" ] && [ ! -L "$link_path" ]; then
        rm -rf "$link_path"
        ln -s "$target_path" "$link_path"
        echo -e "    Restored: $(basename $link_path)"
    fi
}

restore_symlink "$PAYROLL_LIB/styles-shared" "../../../frontend/src/lib/styles"
restore_symlink "$PAYROLL_LIB/shared-base" "../../../frontend/src/lib/components/v2-current/base"
restore_symlink "$PAYROLL_LIB/shared-icons" "../../../frontend/src/lib/components/v2-current/icons"

echo -e "${GREEN}  ✓ Symlinks 已恢复${NC}"

if [ $BUILD_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Payroll Frontend 镜像构建成功${NC}"
else
    echo -e "${RED}✗ Payroll Frontend 镜像构建失败${NC}"
    exit 1
fi
```

### Payroll Dockerfile

Create `deploy/nginx/Dockerfile.payroll`:

```dockerfile
# Payroll Frontend Production Dockerfile
# Multi-stage build: Build stage + Production stage

# ==================== Build Stage ====================
FROM node:20-slim AS builder

WORKDIR /app

# Accept build arguments
ARG VITE_API_URL=https://api.beanflow.ai
ARG VITE_PAYROLL_URL=https://payroll.beanflow.ai

# Set environment variables for Vite build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_PAYROLL_URL=$VITE_PAYROLL_URL

# Install dependencies
COPY payroll-frontend/package*.json ./
RUN npm ci

# Copy source code (symlinks already resolved by build script)
COPY payroll-frontend/ ./

# Build for production
RUN npm run build

# ==================== Production Stage ====================
FROM nginx:alpine

# Create non-root user
RUN addgroup -g 1000 -S appgroup && \
    adduser -u 1000 -S appuser -G appgroup

# Copy nginx configuration
COPY deploy/nginx/nginx-payroll.conf /etc/nginx/nginx.conf

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Set ownership
RUN chown -R appuser:appgroup /usr/share/nginx/html && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget -qO- http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### Build Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    build-images.sh                           │
├─────────────────────────────────────────────────────────────┤
│  1. Pre-build: Resolve symlinks                              │
│     ┌─────────────────┐    ┌─────────────────────────────┐  │
│     │ styles-shared   │ ─► │ Copy from frontend/styles   │  │
│     │ (symlink)       │    │ (actual files)              │  │
│     └─────────────────┘    └─────────────────────────────┘  │
│                                                              │
│  2. Docker Build                                             │
│     ┌─────────────────────────────────────────────────────┐ │
│     │ COPY payroll-frontend/ ./                           │ │
│     │ (now includes actual files, not symlinks)           │ │
│     │ npm run build                                       │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  3. Post-build: Restore symlinks                             │
│     ┌─────────────────┐    ┌─────────────────────────────┐  │
│     │ styles-shared   │ ◄─ │ Restore symlink for dev     │  │
│     │ (actual files)  │    │ (symlink to frontend/)      │  │
│     └─────────────────┘    └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Advantages of This Approach

| Aspect | Benefit |
|--------|---------|
| **Development** | Symlinks work normally, changes reflect immediately |
| **Build** | No symlink issues, files are physically present |
| **Git** | Symlinks are tracked, not duplicated files |
| **Maintenance** | Single source of truth for shared components |
| **Rollback** | Symlinks restored after build, dev continues normally |

### Alternative: .dockerignore + Explicit COPY

If you prefer not to modify the build script, you can use multi-stage COPY in Dockerfile:

```dockerfile
# Alternative approach in Dockerfile
FROM node:20-slim AS builder
WORKDIR /app

# Copy shared resources first
COPY frontend/src/lib/styles ./src/lib/styles-shared
COPY frontend/src/lib/components/v2-current/base ./src/lib/shared-base
COPY frontend/src/lib/components/v2-current/icons ./src/lib/shared-icons

# Then copy payroll code
COPY payroll-frontend/package*.json ./
RUN npm ci
COPY payroll-frontend/ ./

RUN npm run build
```

This works but requires the build context to be the project root.

---

**Next**: After setting up the frontend structure, proceed to [Phase 1: Data Layer](./01_phase1_data_layer.md)
