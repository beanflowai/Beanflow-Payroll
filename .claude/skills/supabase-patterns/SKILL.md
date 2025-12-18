---
name: supabase-patterns
description: Supabase usage patterns for Beanflow-Payroll - database queries, authentication, real-time subscriptions, RLS policies, migrations, and best practices
owner: Backend Team
last_updated: 2025-12-18
triggers:
  - Supabase
  - database queries
  - authentication
  - RLS policies
  - migrations
  - real-time
  - PostgreSQL
related_skills:
  - backend-development
  - core-architecture
  - error-handling
agent_hints:
  token_budget_hint: "Load for Supabase-specific operations and patterns"
  write_scope: ["writes-backend", "writes-frontend"]
  plan_shape: ["Design table schema", "Implement RLS policies", "Write queries"]
  approval_required_if: ["Database schema changes (Rule-09)"]
---

# Quick Reference Card
- When to use: Database operations, authentication, real-time features, migrations
- 3-step approach:
  1) Design table with proper camelCase column naming
  2) Implement RLS policies for row-level security
  3) Use typed queries with proper error handling
- How to verify: RLS policies tested, queries return expected data, migrations applied cleanly

---

# Supabase Usage Patterns

## Project Structure

```
backend/
├── supabase/
│   ├── migrations/           # Database migrations
│   │   ├── 20241216_initial_schema.sql
│   │   └── 20241217_add_payroll_tables.sql
│   ├── seed.sql              # Test data seeding
│   └── config.toml           # Supabase local config
└── app/
    ├── core/
    │   └── supabase.py       # Supabase client initialization
    └── services/
        └── *_service.py      # Services using Supabase
```

---

## Client Initialization

### Backend (Python)

```python
# app/core/supabase.py
from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Client | None = None

def get_supabase_client() -> Client:
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY  # Use service key for backend
        )
    return _supabase_client

# FastAPI dependency
async def get_supabase() -> Client:
    return get_supabase_client()
```

### Frontend (TypeScript)

```typescript
// $lib/supabase.ts
import { createClient } from '@supabase/supabase-js';
import type { Database } from '$lib/types/database';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey);
```

---

## Table Naming Conventions

### Column Names: camelCase

```sql
-- Correct: camelCase column names
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companyId UUID NOT NULL REFERENCES companies(id),
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    payRate NUMERIC(10,2) NOT NULL,
    payGroupId UUID REFERENCES pay_groups(id),
    isActive BOOLEAN DEFAULT true,
    hireDate DATE NOT NULL,
    terminationDate DATE,
    createdAt TIMESTAMPTZ DEFAULT NOW(),
    updatedAt TIMESTAMPTZ DEFAULT NOW()
);

-- Wrong: snake_case column names
CREATE TABLE employees (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,      -- Should be companyId
    first_name TEXT NOT NULL,      -- Should be firstName
    pay_rate NUMERIC(10,2),        -- Should be payRate
    created_at TIMESTAMPTZ         -- Should be createdAt
);
```

### Table Names: snake_case (PostgreSQL convention)

```sql
-- Table names use snake_case (PostgreSQL standard)
CREATE TABLE pay_groups (...);
CREATE TABLE payroll_runs (...);
CREATE TABLE employee_deductions (...);
```

---

## Query Patterns

### Basic Select

```python
async def get_employees_by_company(
    supabase: Client,
    company_id: str,
    active_only: bool = True
) -> list[dict[str, Any]]:
    """Get all employees for a company."""
    query = supabase.table("employees") \
        .select("*") \
        .eq("companyId", company_id)

    if active_only:
        query = query.eq("isActive", True)

    response = query.order("lastName", desc=False).execute()
    return response.data
```

### Select with Joins

```python
async def get_employee_with_pay_group(
    supabase: Client,
    employee_id: str
) -> dict[str, Any] | None:
    """Get employee with their pay group details."""
    response = supabase.table("employees") \
        .select("""
            *,
            payGroup:pay_groups(
                id,
                name,
                payFrequency,
                nextPayDate
            )
        """) \
        .eq("id", employee_id) \
        .single() \
        .execute()

    return response.data
```

### Insert

```python
async def create_employee(
    supabase: Client,
    employee_data: dict[str, Any]
) -> dict[str, Any]:
    """Create a new employee."""
    now = datetime.utcnow().isoformat()
    data = {
        **employee_data,
        "createdAt": now,
        "updatedAt": now,
        "isActive": True
    }

    response = supabase.table("employees") \
        .insert(data) \
        .execute()

    return response.data[0]
```

### Update

```python
async def update_employee(
    supabase: Client,
    employee_id: str,
    updates: dict[str, Any]
) -> dict[str, Any]:
    """Update an employee."""
    updates["updatedAt"] = datetime.utcnow().isoformat()

    response = supabase.table("employees") \
        .update(updates) \
        .eq("id", employee_id) \
        .execute()

    if not response.data:
        raise ValueError(f"Employee {employee_id} not found")

    return response.data[0]
```

### Delete (Soft Delete Preferred)

```python
async def deactivate_employee(
    supabase: Client,
    employee_id: str
) -> dict[str, Any]:
    """Soft delete an employee by deactivating."""
    return await update_employee(
        supabase,
        employee_id,
        {
            "isActive": False,
            "terminationDate": datetime.utcnow().date().isoformat()
        }
    )

# Hard delete (use sparingly)
async def delete_employee(
    supabase: Client,
    employee_id: str
) -> None:
    """Hard delete an employee. Use with caution."""
    supabase.table("employees") \
        .delete() \
        .eq("id", employee_id) \
        .execute()
```

### Upsert

```python
async def upsert_payroll_run(
    supabase: Client,
    payroll_data: dict[str, Any]
) -> dict[str, Any]:
    """Create or update a payroll run."""
    now = datetime.utcnow().isoformat()
    data = {
        **payroll_data,
        "updatedAt": now
    }

    # Upsert based on unique constraint
    response = supabase.table("payroll_runs") \
        .upsert(data, on_conflict="companyId,payGroupId,payDate") \
        .execute()

    return response.data[0]
```

---

## RLS (Row Level Security) Policies

### Enable RLS on Tables

```sql
-- Always enable RLS
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;
```

### Company-Based Access Control

```sql
-- Users can only access their company's employees
CREATE POLICY "Users can view their company's employees"
ON employees FOR SELECT
USING (
    companyId IN (
        SELECT companyId FROM company_users
        WHERE userId = auth.uid()
    )
);

-- Users can insert employees for their company
CREATE POLICY "Users can create employees for their company"
ON employees FOR INSERT
WITH CHECK (
    companyId IN (
        SELECT companyId FROM company_users
        WHERE userId = auth.uid()
    )
);

-- Users can update their company's employees
CREATE POLICY "Users can update their company's employees"
ON employees FOR UPDATE
USING (
    companyId IN (
        SELECT companyId FROM company_users
        WHERE userId = auth.uid()
    )
);
```

### Service Role Bypass

```python
# Backend uses service role key which bypasses RLS
# This is intentional for server-side operations
supabase = create_client(url, service_role_key)

# Frontend uses anon key which respects RLS
supabase = createClient(url, anon_key)
```

---

## Authentication Patterns

### Get Current User

```typescript
// Frontend: Get current authenticated user
async function getCurrentUser() {
  const { data: { user }, error } = await supabase.auth.getUser();

  if (error) {
    console.error('Auth error:', error);
    return null;
  }

  return user;
}
```

### Auth State Listener

```typescript
// Frontend: Listen for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('User signed in:', session?.user);
  } else if (event === 'SIGNED_OUT') {
    console.log('User signed out');
    // Redirect to login
  }
});
```

### Backend Token Verification

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> dict[str, Any]:
    """Verify JWT and get current user."""
    token = credentials.credentials

    try:
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

---

## Real-Time Subscriptions

### Subscribe to Table Changes

```typescript
// Frontend: Subscribe to payroll run updates
function subscribeToPayrollRuns(companyId: string, callback: (payload: any) => void) {
  const subscription = supabase
    .channel(`payroll_runs:${companyId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'payroll_runs',
        filter: `companyId=eq.${companyId}`
      },
      callback
    )
    .subscribe();

  return subscription;
}

// Usage
const subscription = subscribeToPayrollRuns(companyId, (payload) => {
  console.log('Payroll run changed:', payload);
  // Update UI
});

// Cleanup
subscription.unsubscribe();
```

---

## Migration Best Practices

### Migration File Naming

```
migrations/
├── 20241216000000_create_companies.sql
├── 20241216000001_create_pay_groups.sql
├── 20241216000002_create_employees.sql
├── 20241217000000_add_payroll_tables.sql
└── 20241218000000_add_vacation_tracking.sql
```

### Migration Template

```sql
-- migrations/20241217000000_add_payroll_tables.sql

-- Create payroll_runs table
CREATE TABLE IF NOT EXISTS payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companyId UUID NOT NULL REFERENCES companies(id),
    payGroupId UUID NOT NULL REFERENCES pay_groups(id),
    payDate DATE NOT NULL,
    payPeriodStart DATE NOT NULL,
    payPeriodEnd DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    totalGrossPay NUMERIC(12,2) DEFAULT 0,
    totalNetPay NUMERIC(12,2) DEFAULT 0,
    employeeCount INTEGER DEFAULT 0,
    submittedAt TIMESTAMPTZ,
    submittedBy UUID REFERENCES auth.users(id),
    createdAt TIMESTAMPTZ DEFAULT NOW(),
    updatedAt TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(companyId, payGroupId, payDate)
);

-- Enable RLS
ALTER TABLE payroll_runs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Company users can view payroll runs"
ON payroll_runs FOR SELECT
USING (
    companyId IN (
        SELECT companyId FROM company_users
        WHERE userId = auth.uid()
    )
);

-- Create indexes
CREATE INDEX idx_payroll_runs_company ON payroll_runs(companyId);
CREATE INDEX idx_payroll_runs_pay_date ON payroll_runs(payDate);
CREATE INDEX idx_payroll_runs_status ON payroll_runs(status);

-- Add trigger for updatedAt
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW."updatedAt" = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER payroll_runs_updated_at
    BEFORE UPDATE ON payroll_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### Running Migrations

```bash
# Push migrations to Supabase
cd backend
supabase db push

# Check migration status
supabase migration list

# Create new migration
supabase migration new add_vacation_tracking
```

---

## Error Handling with Supabase

```python
from postgrest.exceptions import APIError

async def safe_query(
    supabase: Client,
    table: str,
    query_fn
) -> dict[str, Any]:
    """Execute Supabase query with proper error handling."""
    try:
        response = query_fn(supabase.table(table)).execute()
        return {"success": True, "data": response.data}
    except APIError as e:
        logger.error(f"Supabase API error", extra={
            "table": table,
            "error": str(e),
            "code": e.code
        })
        return {
            "success": False,
            "error": str(e),
            "errorCode": e.code
        }
    except Exception as e:
        logger.error(f"Unexpected Supabase error", extra={
            "table": table,
            "error": str(e)
        })
        return {
            "success": False,
            "error": "Database operation failed"
        }
```

---

## TypeScript Database Types

### Generate Types from Schema

```bash
# Generate TypeScript types from Supabase schema
npx supabase gen types typescript --project-id your-project-id > src/lib/types/database.ts
```

### Using Generated Types

```typescript
// $lib/types/database.ts (generated)
export interface Database {
  public: {
    Tables: {
      employees: {
        Row: {
          id: string;
          companyId: string;
          firstName: string;
          lastName: string;
          email: string;
          payRate: number;
          isActive: boolean;
          createdAt: string;
          updatedAt: string;
        };
        Insert: Omit<Row, 'id' | 'createdAt' | 'updatedAt'>;
        Update: Partial<Insert>;
      };
      // ... other tables
    };
  };
}

// Usage with typed client
import { supabase } from '$lib/supabase';
import type { Database } from '$lib/types/database';

type Employee = Database['public']['Tables']['employees']['Row'];

const { data, error } = await supabase
  .from('employees')
  .select('*')
  .eq('companyId', companyId)
  .returns<Employee[]>();
```

---

## Validation Checklist

When working with Supabase:

- [ ] Table columns use camelCase naming?
- [ ] RLS enabled on all tables?
- [ ] RLS policies properly restrict access?
- [ ] Migrations include rollback plan?
- [ ] Indexes added for frequently queried columns?
- [ ] Error handling follows transparency principles?
- [ ] TypeScript types generated and up to date?
- [ ] Service role key only used in backend?

---

## Related Resources

- **Supabase Documentation**: https://supabase.com/docs
- **Backend Development**: See `backend-development` skill
- **Error Handling**: See `error-handling` skill
- **Core Architecture**: See `core-architecture` skill
