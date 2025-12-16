# Shared UI Components

> **Last Updated**: 2025-12-07
> **Location**: `payroll-frontend/src/lib/components/shared/`

---

## 1. StatusBadge Component

Displays status with appropriate color coding.

### Usage

```svelte
<StatusBadge status="approved" />
<StatusBadge status="active" type="employee" />
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `status` | string | required | Status value |
| `type` | `'payroll'` \| `'employee'` | `'payroll'` | Context for color mapping |

### Color Mappings

#### Payroll Status
| Status | Colors |
|--------|--------|
| `draft` | `bg-gray-100 text-gray-800` |
| `pending_approval` | `bg-yellow-100 text-yellow-800` |
| `approved` | `bg-blue-100 text-blue-800` |
| `paid` | `bg-green-100 text-green-800` |
| `cancelled` | `bg-red-100 text-red-800` |

#### Employee Status
| Status | Colors |
|--------|--------|
| `active` | `bg-green-100 text-green-800` |
| `terminated` | `bg-red-100 text-red-800` |

### Implementation

```svelte
<!-- StatusBadge.svelte -->
<script lang="ts">
  type PayrollStatus = 'draft' | 'pending_approval' | 'approved' | 'paid' | 'cancelled';
  type EmployeeStatus = 'active' | 'terminated';

  interface Props {
    status: PayrollStatus | EmployeeStatus;
    type?: 'payroll' | 'employee';
  }

  let { status, type = 'payroll' }: Props = $props();

  const colorMap = {
    payroll: {
      draft: 'bg-gray-100 text-gray-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    },
    employee: {
      active: 'bg-green-100 text-green-800',
      terminated: 'bg-red-100 text-red-800',
    },
  };

  const labelMap = {
    draft: 'Draft',
    pending_approval: 'Pending',
    approved: 'Approved',
    paid: 'Paid',
    cancelled: 'Cancelled',
    active: 'Active',
    terminated: 'Terminated',
  };

  const colors = $derived(colorMap[type][status] ?? 'bg-gray-100 text-gray-800');
  const label = $derived(labelMap[status] ?? status);
</script>

<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {colors}">
  {label}
</span>
```

---

## 2. MoneyDisplay Component

Formats and displays monetary values consistently.

### Usage

```svelte
<MoneyDisplay amount={6000000} />          <!-- $60,000.00 -->
<MoneyDisplay amount={4200} type="hourly" /> <!-- $42.00/hr -->
<MoneyDisplay amount={-50000} />           <!-- -$500.00 (red) -->
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `amount` | number | required | Amount in cents |
| `type` | `'default'` \| `'hourly'` \| `'compact'` | `'default'` | Display format |
| `showSign` | boolean | `false` | Always show +/- sign |
| `colorNegative` | boolean | `true` | Red color for negative amounts |

### Implementation

```svelte
<!-- MoneyDisplay.svelte -->
<script lang="ts">
  interface Props {
    amount: number;
    type?: 'default' | 'hourly' | 'compact';
    showSign?: boolean;
    colorNegative?: boolean;
  }

  let { amount, type = 'default', showSign = false, colorNegative = true }: Props = $props();

  const formatted = $derived(() => {
    const dollars = amount / 100;
    const formatter = new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: type === 'compact' ? 0 : 2,
      maximumFractionDigits: type === 'compact' ? 0 : 2,
    });

    let result = formatter.format(Math.abs(dollars));

    if (amount < 0) result = `-${result}`;
    else if (showSign && amount > 0) result = `+${result}`;

    if (type === 'hourly') result += '/hr';

    return result;
  });

  const colorClass = $derived(
    colorNegative && amount < 0 ? 'text-red-600' : ''
  );
</script>

<span class="tabular-nums {colorClass}">{formatted()}</span>
```

---

## 3. SummaryCard Component

Displays a metric with label and optional trend indicator.

### Usage

```svelte
<SummaryCard
  label="Total Gross"
  value={2307690}
  format="currency"
/>

<SummaryCard
  label="Employees"
  value={12}
  format="number"
/>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | string | required | Card label |
| `value` | number | required | Primary value |
| `format` | `'currency'` \| `'number'` \| `'percent'` | `'currency'` | Value format |
| `trend` | number | `undefined` | Percent change (shows arrow) |
| `size` | `'sm'` \| `'md'` \| `'lg'` | `'md'` | Card size |

### Implementation

```svelte
<!-- SummaryCard.svelte -->
<script lang="ts">
  interface Props {
    label: string;
    value: number;
    format?: 'currency' | 'number' | 'percent';
    trend?: number;
    size?: 'sm' | 'md' | 'lg';
  }

  let { label, value, format = 'currency', trend, size = 'md' }: Props = $props();

  const formattedValue = $derived(() => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-CA', {
          style: 'currency',
          currency: 'CAD',
        }).format(value / 100);
      case 'percent':
        return `${value.toFixed(1)}%`;
      default:
        return value.toLocaleString();
    }
  });

  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const valueSizes = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  };
</script>

<div class="bg-white rounded-lg border border-gray-200 {sizeClasses[size]}">
  <p class="text-sm text-gray-600">{label}</p>
  <p class="font-semibold {valueSizes[size]} text-gray-900 mt-1">
    {formattedValue()}
  </p>
  {#if trend !== undefined}
    <div class="flex items-center mt-2 text-sm">
      {#if trend > 0}
        <span class="text-green-600">↑ {trend.toFixed(1)}%</span>
      {:else if trend < 0}
        <span class="text-red-600">↓ {Math.abs(trend).toFixed(1)}%</span>
      {:else}
        <span class="text-gray-500">— 0%</span>
      {/if}
    </div>
  {/if}
</div>
```

---

## 4. DataTable Component

Reusable table with sorting, filtering, and pagination.

### Usage

```svelte
<DataTable
  data={employees}
  columns={[
    { key: 'name', label: 'Name', sortable: true },
    { key: 'province', label: 'Province', sortable: true },
    { key: 'salary', label: 'Salary', sortable: true, format: 'currency' },
  ]}
  onRowClick={(row) => openDetail(row)}
/>
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `data` | T[] | Array of data objects |
| `columns` | Column[] | Column definitions |
| `sortable` | boolean | Enable sorting |
| `selectable` | boolean | Enable row selection |
| `onRowClick` | (row: T) => void | Row click handler |
| `emptyMessage` | string | Message when no data |

### Column Definition

```typescript
interface Column<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  format?: 'text' | 'currency' | 'date' | 'custom';
  render?: (value: any, row: T) => string | SnippetResult;
  width?: string;
  align?: 'left' | 'center' | 'right';
}
```

---

## 5. Modal Component

Base modal component for dialogs.

### Usage

```svelte
<Modal open={showForm} onClose={() => showForm = false} title="Add Employee">
  <EmployeeForm />
</Modal>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | boolean | required | Modal visibility |
| `onClose` | () => void | required | Close handler |
| `title` | string | `''` | Modal title |
| `size` | `'sm'` \| `'md'` \| `'lg'` \| `'xl'` | `'md'` | Modal width |
| `closeOnBackdrop` | boolean | `true` | Close on backdrop click |

### Sizes

| Size | Max Width |
|------|-----------|
| `sm` | 400px |
| `md` | 560px |
| `lg` | 720px |
| `xl` | 960px |

---

## 6. SlidePanel Component

Slide-out panel for detail views.

### Usage

```svelte
<SlidePanel open={showDetail} onClose={() => showDetail = false}>
  <EmployeeDetailPanel employee={selectedEmployee} />
</SlidePanel>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | boolean | required | Panel visibility |
| `onClose` | () => void | required | Close handler |
| `position` | `'left'` \| `'right'` | `'right'` | Slide direction |
| `width` | string | `'400px'` | Panel width |

---

## 7. LoadingSpinner Component

Loading indicator.

### Usage

```svelte
<LoadingSpinner />
<LoadingSpinner size="lg" label="Calculating..." />
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `size` | `'sm'` \| `'md'` \| `'lg'` | `'md'` | Spinner size |
| `label` | string | `undefined` | Loading text |

---

## 8. EmptyState Component

Displayed when data is empty.

### Usage

```svelte
<EmptyState
  icon="users"
  title="No employees yet"
  description="Add your first employee to get started"
  action={{ label: 'Add Employee', onClick: () => openForm() }}
/>
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `icon` | string | Icon name |
| `title` | string | Main message |
| `description` | string | Secondary message |
| `action` | { label: string, onClick: () => void } | Optional action button |

---

## 9. AlertBanner Component

Contextual alert messages.

### Usage

```svelte
<AlertBanner type="info" icon="calendar">
  Christmas Day (Dec 25) falls in this period
  <a href="#" on:click={manageHoliday}>Manage Holiday Hours</a>
</AlertBanner>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `'info'` \| `'warning'` \| `'error'` \| `'success'` | `'info'` | Alert type |
| `icon` | string | `undefined` | Optional icon |
| `dismissible` | boolean | `false` | Show close button |

### Colors

| Type | Background | Text |
|------|------------|------|
| `info` | `bg-blue-50` | `text-blue-800` |
| `warning` | `bg-yellow-50` | `text-yellow-800` |
| `error` | `bg-red-50` | `text-red-800` |
| `success` | `bg-green-50` | `text-green-800` |

---

## 10. Component File Structure

```
payroll-frontend/src/lib/components/shared/
├── StatusBadge.svelte
├── MoneyDisplay.svelte
├── SummaryCard.svelte
├── DataTable.svelte
├── Modal.svelte
├── SlidePanel.svelte
├── LoadingSpinner.svelte
├── EmptyState.svelte
├── AlertBanner.svelte
└── index.ts          # Re-exports all components
```

### Index File

```typescript
// index.ts
export { default as StatusBadge } from './StatusBadge.svelte';
export { default as MoneyDisplay } from './MoneyDisplay.svelte';
export { default as SummaryCard } from './SummaryCard.svelte';
export { default as DataTable } from './DataTable.svelte';
export { default as Modal } from './Modal.svelte';
export { default as SlidePanel } from './SlidePanel.svelte';
export { default as LoadingSpinner } from './LoadingSpinner.svelte';
export { default as EmptyState } from './EmptyState.svelte';
export { default as AlertBanner } from './AlertBanner.svelte';
```
