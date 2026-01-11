# In-Dashboard Onboarding Experience Implementation Plan

## Overview

Implement a step-by-step onboarding experience integrated directly into the dashboard (no separate onboarding flow). The system will track 5 essential setup steps with persistent progress storage in the database.

**Onboarding Steps:**
1. Create Company Profile
2. Design Pay Groups
3. Add Employees
4. Assign Employees to Pay Groups
5. Run First Payroll

## Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Progress Storage** | `companies.onboarding_progress` JSONB column | One-to-one with company, no joins needed, simpler queries |
| **Detection Method** | Completion-based (check database state) | No explicit flag needed, auto-detects progress |
| **Dismissal** | Always dismissible, reappears on next visit | User choice with persistent reminder |
| **Dashboard Placement** | Hybrid: AlertBanner + Progress Card | Banner for visibility, Card for detailed progress |

---

## Phase 1: Backend - Database Schema

### 1.1 Create Migration

**File:** `backend/supabase/migrations/20260110100000_onboarding_progress.sql`

```sql
-- Add onboarding_progress JSONB column to companies table
ALTER TABLE companies
ADD COLUMN onboarding_progress JSONB DEFAULT '{
  "completedSteps": [],
  "dismissedAt": null,
  "lastUpdated": null
}'::JSONB;

-- Create index for efficient querying
CREATE INDEX idx_companies_onboarding ON companies
  USING GIN ((onboarding_progress->'completedSteps'));

COMMENT ON COLUMN companies.onboarding_progress IS
  'Tracks onboarding progress: completedSteps array, dismissedAt timestamp, lastUpdated timestamp';
```

### 1.2 Run Migration

```bash
cd backend
uv run supabase db push
```

---

## Phase 2: Frontend - Core Types & Configuration

### 2.1 Create Onboarding Types

**File:** `frontend/src/lib/types/onboarding.ts`

```typescript
export type OnboardingStep =
  | 'company_profile'
  | 'pay_groups'
  | 'employees'
  | 'employee_assignment'
  | 'payroll_run';

export interface OnboardingProgress {
  completedSteps: OnboardingStep[];
  dismissedAt: string | null;
  lastUpdated: string | null;
}

export interface OnboardingStepConfig {
  id: OnboardingStep;
  title: string;
  description: string;
  icon: string;
  route: string;
  checkCompletion: (companyId: string) => Promise<boolean>;
}
```

### 2.2 Create Step Configuration

**File:** `frontend/src/lib/config/onboardingSteps.ts`

```typescript
import { supabase } from '$lib/api/supabase';
import type { OnboardingStepConfig } from '$lib/types/onboarding';

export const ONBOARDING_STEPS: OnboardingStepConfig[] = [
  {
    id: 'company_profile',
    title: 'Create Company Profile',
    description: 'Set up your company information and CRA remittance details',
    icon: 'fa-building',
    route: '/company?tab=profile',
    checkCompletion: async (companyId: string) => {
      const { data } = await supabase
        .from('companies')
        .select('company_name, business_number, payroll_account_number, province')
        .eq('id', companyId)
        .single();
      return !!data?.company_name && !!data?.business_number &&
             !!data?.payroll_account_number && !!data?.province;
    }
  },
  {
    id: 'pay_groups',
    title: 'Design Pay Groups',
    description: 'Create pay groups to organize employees by pay frequency',
    icon: 'fa-clipboard-list',
    route: '/company?tab=pay-groups',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('pay_groups')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId);
      return (count ?? 0) > 0;
    }
  },
  {
    id: 'employees',
    title: 'Add Employees',
    description: 'Add your employees to the system',
    icon: 'fa-user-plus',
    route: '/employees/new',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('employees')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .is('termination_date', null);
      return (count ?? 0) > 0;
    }
  },
  {
    id: 'employee_assignment',
    title: 'Assign to Pay Groups',
    description: 'Assign employees to their appropriate pay groups',
    icon: 'fa-users-cog',
    route: '/employees',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('employees')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .not('pay_group_id', 'is', null)
        .is('termination_date', null);
      return (count ?? 0) > 0;
    }
  },
  {
    id: 'payroll_run',
    title: 'Run First Payroll',
    description: 'Complete your first payroll run',
    icon: 'fa-play-circle',
    route: '/payroll',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('payroll_runs')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .in('status', ['paid', 'approved']);
      return (count ?? 0) > 0;
    }
  }
];
```

---

## Phase 3: Frontend - State Management

### 3.1 Create Onboarding Store

**File:** `frontend/src/lib/stores/onboarding.svelte.ts`

```typescript
import { browser } from '$app/environment';
import { supabase } from '$lib/api/supabase';
import { getCurrentCompanyId } from './company.svelte';
import type { OnboardingProgress, OnboardingStep } from '$lib/types/onboarding';

let _progress = $state<OnboardingProgress | null>(null);
let _isLoading = $state(false);
let _error = $state<string | null>(null);

export async function loadOnboardingProgress(): Promise<void> {
  if (!browser) return;
  _isLoading = true;
  _error = null;

  try {
    const companyId = getCurrentCompanyId();
    const { data, error } = await supabase
      .from('companies')
      .select('onboarding_progress')
      .eq('id', companyId)
      .single();

    if (error) throw error;
    _progress = data?.onboarding_progress || {
      completedSteps: [],
      dismissedAt: null,
      lastUpdated: null
    };
  } catch (err) {
    _error = err instanceof Error ? err.message : 'Failed to load onboarding progress';
  } finally {
    _isLoading = false;
  }
}

export async function markStepComplete(stepId: OnboardingStep): Promise<void> {
  if (!browser) return;
  const companyId = getCurrentCompanyId();

  if (!_progress) await loadOnboardingProgress();
  if (_progress?.completedSteps.includes(stepId)) return;

  const updatedProgress: OnboardingProgress = {
    completedSteps: [...(_progress?.completedSteps || []), stepId],
    dismissedAt: null,
    lastUpdated: new Date().toISOString()
  };

  const { error } = await supabase
    .from('companies')
    .update({ onboarding_progress: updatedProgress })
    .eq('id', companyId);

  if (error) throw error;
  _progress = updatedProgress;
}

export async function dismissOnboarding(): Promise<void> {
  if (!browser || !_progress) return;
  const companyId = getCurrentCompanyId();

  const updatedProgress: OnboardingProgress = {
    ..._progress,
    dismissedAt: new Date().toISOString(),
    lastUpdated: new Date().toISOString()
  };

  const { error } = await supabase
    .from('companies')
    .update({ onboarding_progress: updatedProgress })
    .eq('id', companyId);

  if (error) throw error;
  _progress = updatedProgress;
}

export async function refreshOnboardingStatus(): Promise<void> {
  if (!browser) return;
  const companyId = getCurrentCompanyId();
  const { ONBOARDING_STEPS } = await import('$lib/config/onboardingSteps');

  const { data: currentProgress } = await supabase
    .from('companies')
    .select('onboarding_progress')
    .eq('id', companyId)
    .single();

  const completedSteps = currentProgress?.onboarding_progress?.completedSteps || [];

  for (const step of ONBOARDING_STEPS) {
    if (!completedSteps.includes(step.id)) {
      const isComplete = await step.checkCompletion(companyId);
      if (isComplete) completedSteps.push(step.id);
    }
  }

  const newProgress: OnboardingProgress = {
    completedSteps,
    dismissedAt: null,
    lastUpdated: new Date().toISOString()
  };

  await supabase
    .from('companies')
    .update({ onboarding_progress: newProgress })
    .eq('id', companyId);

  _progress = newProgress;
}

export function clearOnboardingState(): void {
  _progress = null;
  _isLoading = false;
  _error = null;
}

export const onboardingState = {
  get progress() { return _progress; },
  get isLoading() { return _isLoading; },
  get error() { return _error; },
  get isCompleted() { return _progress?.completedSteps.length === 5; },
  get completionPercentage() {
    if (!_progress) return 0;
    return (_progress.completedSteps.length / 5) * 100;
  },
  get isDismissed() { return !!_progress?.dismissedAt; }
};
```

---

## Phase 4: Frontend - UI Components

### 4.1 OnboardingBanner Component

**File:** `frontend/src/lib/components/onboarding/OnboardingBanner.svelte`

```svelte
<script lang="ts">
  import type { OnboardingProgress } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onDismiss: () => void;
    onContinue: () => void;
  }

  let { progress, onDismiss, onContinue }: Props = $props();

  const completedCount = progress.completedSteps.length;
  const nextStep = ONBOARDING_STEPS.find(s => !progress.completedSteps.includes(s.id));
</script>

<div class="onboarding-banner">
  <div class="banner-content">
    <i class="fas fa-rocket banner-icon"></i>
    <div class="banner-text">
      <span class="banner-title">
        Setup in Progress: {completedCount} of 5 steps completed
      </span>
      <span class="banner-description">
        {nextStep ? `Next: ${nextStep.title}` : 'Almost done!'}
      </span>
    </div>
  </div>
  <div class="banner-actions">
    <button class="btn-continue" onclick={onContinue}>
      Continue Setup
    </button>
    <button class="btn-dismiss" onclick={onDismiss}>
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>

<style>
  .onboarding-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-4) var(--spacing-5);
    background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-6);
  }
  .banner-content { display: flex; align-items: center; gap: var(--spacing-4); }
  .banner-icon { font-size: 24px; color: var(--color-primary-600); }
  .banner-text { display: flex; flex-direction: column; }
  .banner-title { font-weight: var(--font-weight-semibold); color: var(--color-surface-800); }
  .banner-description { font-size: var(--font-size-small); color: var(--color-surface-600); }
  .banner-actions { display: flex; gap: var(--spacing-3); }
  .btn-continue {
    padding: var(--spacing-2) var(--spacing-4);
    background: var(--color-primary-600);
    color: white;
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
  }
  .btn-dismiss {
    padding: var(--spacing-2);
    background: transparent;
    color: var(--color-surface-500);
    border-radius: var(--radius-md);
  }
</style>
```

### 4.2 OnboardingProgressCard Component

**File:** `frontend/src/lib/components/onboarding/OnboardingProgressCard.svelte`

```svelte
<script lang="ts">
  import type { OnboardingProgress, OnboardingStep } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onStepClick?: (stepId: OnboardingStep) => void;
  }

  let { progress, onStepClick }: Props = $props();

  function getStatus(stepId: string): 'completed' | 'pending' {
    return progress.completedSteps.includes(stepId as OnboardingStep) ? 'completed' : 'pending';
  }
</script>

<div class="stat-card onboarding-card">
  <div class="card-header">
    <div class="stat-icon onboarding">
      <i class="fas fa-tasks"></i>
    </div>
    <div class="card-title">
      <span class="stat-label">Setup Progress</span>
      <span class="stat-value">{progress.completedSteps.length}/5</span>
    </div>
  </div>
  <div class="steps-list">
    {#each ONBOARDING_STEPS as step}
      {@const status = getStatus(step.id)}
      <div
        class="step-item {status}"
        onclick={() => onStepClick?.(step.id)}
        role="button"
      >
        <i class="fas fa-{status === 'completed' ? 'check-circle' : 'circle'} step-icon"></i>
        <span class="step-text">{step.title}</span>
      </div>
    {/each}
  </div>
</div>

<style>
  .onboarding-card { cursor: pointer; }
  .card-header { display: flex; align-items: center; gap: var(--spacing-4); }
  .stat-icon.onboarding { background: var(--color-primary-100); color: var(--color-primary-600); }
  .card-title { display: flex; flex-direction: column; }
  .steps-list { display: flex; flex-direction: column; gap: var(--spacing-2); margin-top: var(--spacing-4); }
  .step-item { display: flex; align-items: center; gap: var(--spacing-2); padding: var(--spacing-2); border-radius: var(--radius-md); transition: var(--transition-fast); }
  .step-item:hover { background: var(--color-surface-50); }
  .step-item.completed .step-icon { color: var(--color-success-500); }
  .step-item.pending .step-icon { color: var(--color-surface-300); }
  .step-text { font-size: var(--font-size-small); color: var(--color-surface-700); }
</style>
```

### 4.3 Export Components

**File:** `frontend/src/lib/components/onboarding/index.ts`

```typescript
export { default as OnboardingBanner } from './OnboardingBanner.svelte';
export { default as OnboardingProgressCard } from './OnboardingProgressCard.svelte';
```

---

## Phase 5: Frontend - Dashboard Integration

### 5.1 Modify Dashboard Page

**File:** `frontend/src/routes/(app)/dashboard/+page.svelte`

Add after line 9:
```typescript
import { onboardingState, loadOnboardingProgress, dismissOnboarding } from '$lib/stores/onboarding.svelte';
import { OnboardingBanner, OnboardingProgressCard } from '$lib/components/onboarding';
import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';
import { goto } from '$app/navigation';
```

Add in state section (after line 20):
```typescript
let showOnboarding = $state(false);
```

Add in `$effect` block (after line 68):
```typescript
if (company) {
  loadOnboardingProgress();
  showOnboarding = !onboardingState.isCompleted;
}
```

Add banner after page header (after line 129):
```svelte
{#if showOnboarding && !onboardingState.isDismissed && onboardingState.progress}
  <OnboardingBanner
    progress={onboardingState.progress}
    onDismiss={() => dismissOnboarding()}
    onContinue={() => {
      const nextStep = ONBOARDING_STEPS.find(s => !onboardingState.progress?.completedSteps.includes(s.id));
      if (nextStep) goto(nextStep.route);
    }}
  />
{/if}
```

Add onboarding card as 5th stat card (after line 189):
```svelte
{#if showOnboarding && onboardingState.progress}
  <OnboardingProgressCard
    progress={onboardingState.progress}
    onStepClick={(stepId) => {
      const step = ONBOARDING_STEPS.find(s => s.id === stepId);
      if (step) goto(step.route);
    }}
  />
{/if}
```

---

## Phase 6: Frontend - Auto-Completion Integration

### 6.1 Company Profile Save
**File:** `frontend/src/lib/components/company/ProfileTab.svelte`

After successful company update:
```typescript
import { markStepComplete } from '$lib/stores/onboarding.svelte';
// ... after save success
await markStepComplete('company_profile');
```

### 6.2 Pay Group Creation
**File:** `frontend/src/lib/components/company/PayGroupsTab.svelte`

After successful pay group creation:
```typescript
await markStepComplete('pay_groups');
```

### 6.3 Employee Creation
**File:** `frontend/src/routes/(app)/employees/new/+page.svelte`

After successful employee creation:
```typescript
await markStepComplete('employees');
if (newEmployee.payGroupId) {
  await markStepComplete('employee_assignment');
}
```

### 6.4 Employee Pay Group Assignment
**File:** `frontend/src/routes/(app)/employees/[id]/+page.svelte`

After updating pay_group_id:
```typescript
await markStepComplete('employee_assignment');
```

### 6.5 Payroll Completion
**File:** `frontend/src/routes/(app)/payroll/run/[periodEnd]/+page.svelte`

When status changes to 'paid' or 'approved':
```typescript
await markStepComplete('payroll_run');
```

### 6.6 Auto-Refresh on Load
**File:** `frontend/src/routes/(app)/+layout.svelte`

In the auth initialization, after company context loads:
```typescript
import { refreshOnboardingStatus } from '$lib/stores/onboarding.svelte';
// ... after company context initialized
await refreshOnboardingStatus();
```

---

## Critical Files Summary

| File | Purpose |
|------|---------|
| `backend/supabase/migrations/20260110100000_onboarding_progress.sql` | Database schema |
| `frontend/src/lib/stores/onboarding.svelte.ts` | State management |
| `frontend/src/routes/(app)/dashboard/+page.svelte` | Main integration |
| `frontend/src/lib/components/onboarding/OnboardingBanner.svelte` | Banner UI |
| `frontend/src/lib/config/onboardingSteps.ts` | Step definitions |

---

## Verification Steps

1. **Database**: Run migration, verify column exists with correct default
2. **New Company**: Create company, verify onboarding shows (0/5)
3. **Step Completion**: Complete each step, verify progress updates
4. **Dismissal**: Dismiss banner, refresh page, verify it reappears
5. **Multi-Company**: Complete onboarding for Company A, switch to Company B, verify onboarding shows
6. **Completion**: Complete all 5 steps, verify banner disappears

### Test Commands

```bash
# Run migration
cd backend && uv run supabase db push

# Start dev servers
./start-dev.sh

# Test flow:
# 1. Login as new user
# 2. Create company → should see onboarding (0/5)
# 3. Fill company profile → should update to (1/5)
# 4. Create pay group → should update to (2/5)
# 5. Add employee → should update to (3/5)
# 6. Assign pay group → should update to (4/5)
# 7. Run payroll → should complete (5/5) and hide banner
```
