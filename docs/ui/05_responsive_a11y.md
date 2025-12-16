# Responsive Design & Accessibility

> **Last Updated**: 2025-12-07

---

## Responsive Design (Tailwind CSS)

### Breakpoint Strategy

| Breakpoint | Width | Description |
|------------|-------|-------------|
| `sm` | ≥640px | Small tablets |
| `md` | ≥768px | **Minimum supported** |
| `lg` | ≥1024px | Desktop |
| `xl` | ≥1280px | Large desktop |

**Minimum Supported Width**: `768px` (Tailwind `md` breakpoint)

### Mobile Fallback

Below 768px, show an informational message instead of the full interface:

```html
<!-- Show only on screens < 768px -->
<div class="block md:hidden min-h-screen flex items-center justify-center p-6 bg-gray-50">
  <div class="max-w-md text-center">
    <ComputerDesktopIcon class="w-20 h-20 mx-auto text-gray-400 mb-6" />
    <h2 class="text-2xl font-semibold text-gray-900 mb-3">
      Desktop Required
    </h2>
    <p class="text-gray-600 mb-6">
      The Payroll management system requires a desktop or tablet device
      (minimum 768px width) for optimal functionality.
    </p>
    <p class="text-sm text-gray-500">
      Please access this page on a larger screen.
    </p>
  </div>
</div>

<!-- Main content: hidden on small screens -->
<div class="hidden md:block">
  <!-- Payroll interface here -->
</div>
```

### Responsive Column Visibility

Hide less important columns on smaller screens:

```html
<!-- Always visible -->
<th>Employee</th>
<th>Gross Pay</th>
<th>Net Pay</th>
<th>Actions</th>

<!-- Visible on medium screens and up (≥768px) -->
<th class="hidden md:table-cell">Province</th>

<!-- Visible on large screens and up (≥1024px) -->
<th class="hidden lg:table-cell">CPP</th>
<th class="hidden lg:table-cell">EI</th>
<th class="hidden lg:table-cell">Federal Tax</th>
<th class="hidden lg:table-cell">Provincial Tax</th>
```

### Adaptive Layouts

#### Header Actions

Stack buttons on tablet, inline on desktop:

```html
<div class="flex flex-col md:flex-row items-stretch md:items-center gap-3">
  <button class="btn-secondary w-full md:w-auto">
    Export CSV
  </button>
  <button class="btn-primary w-full md:w-auto">
    Confirm Payroll
  </button>
</div>
```

#### Summary Cards

2 columns on tablet, 4 on desktop:

```html
<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
  <SummaryCard label="Total Gross" value={totalGross} />
  <SummaryCard label="Total Deductions" value={totalDeductions} />
  <SummaryCard label="Total Net" value={totalNet} />
  <SummaryCard label="Employer Cost" value={employerCost} />
</div>
```

#### Form Layout

Single column on mobile, 2 columns on desktop:

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
  <div>
    <label>First Name</label>
    <input type="text" />
  </div>
  <div>
    <label>Last Name</label>
    <input type="text" />
  </div>
</div>
```

### Horizontal Scroll Fallback

For data-dense tables, allow horizontal scrolling:

```html
<div class="overflow-x-auto">
  <table class="min-w-full">
    <!-- Table content -->
  </table>
</div>
```

With scroll hint indicator:

```html
<div class="md:hidden overflow-x-auto relative">
  <div class="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none"></div>
  <table class="min-w-[1200px]">
    <!-- Full table with all columns -->
  </table>
</div>
```

---

## Accessibility (a11y)

### Keyboard Navigation

#### Tab Order

1. Pay period navigation (left arrow, date, right arrow)
2. Header action buttons
3. Table rows (each row focusable)
4. Editable cells (Enter to edit, Escape to cancel)
5. Action buttons in each row

#### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Move to next focusable element |
| `Shift + Tab` | Move to previous element |
| `Enter` | Activate button/link, start editing cell |
| `Escape` | Cancel editing, close modal/panel |
| `Arrow keys` | Navigate within table cells (when editing) |

### ARIA Attributes

#### Data Table

```html
<table role="grid" aria-label="Employee payroll records">
  <thead>
    <tr role="row">
      <th role="columnheader" scope="col">Employee</th>
      <th role="columnheader" scope="col" aria-sort="ascending">Gross Pay</th>
    </tr>
  </thead>
  <tbody>
    <tr role="row" tabindex="0">
      <td role="gridcell">Jane Doe</td>
      <td role="gridcell">$2,307.69</td>
    </tr>
  </tbody>
</table>
```

#### Editable Cell

```html
<input
  type="text"
  role="spinbutton"
  aria-label="Gross pay for Jane Doe"
  aria-valuemin="0"
  aria-valuenow="2307.69"
/>
```

#### Icon Buttons

```html
<button aria-label="View paystub for Jane Doe">
  <DocumentIcon class="w-5 h-5" />
</button>

<button aria-label="Calculate payroll" aria-busy="true" disabled>
  <SpinnerIcon class="w-5 h-5 animate-spin" />
</button>
```

#### Modal Dialog

```html
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Add New Employee</h2>
  <!-- Modal content -->
</div>
```

### Focus States

All interactive elements must have visible focus indicators:

```html
<!-- Button -->
<button class="focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none">
  Save
</button>

<!-- Input -->
<input class="focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:outline-none" />

<!-- Table row -->
<tr class="focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-inset" tabindex="0">
  <!-- cells -->
</tr>
```

### Touch Targets

**Minimum size**: `44px × 44px` (WCAG 2.1 Level AAA)

```html
<!-- Icon button with proper touch target -->
<button class="w-11 h-11 flex items-center justify-center rounded-lg hover:bg-gray-100">
  <DocumentIcon class="w-5 h-5" />
</button>
```

### Screen Reader Support

#### Descriptive Labels

```html
<input
  type="text"
  id="gross-pay-emp-001"
  name="grossPay"
  aria-label="Gross pay for Jane Doe"
/>

<button aria-label="Download paystub as PDF">
  <DownloadIcon class="w-5 h-5" />
</button>
```

#### Live Regions

For dynamic updates that should be announced:

```html
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  class="sr-only"
>
  {calculationStatus}
</div>
```

Example status messages:
- "Calculating payroll for Jane Doe..."
- "Payroll calculation complete"
- "Error: Failed to calculate payroll"

#### Skip Links

Allow users to skip navigation:

```html
<a
  href="#main-content"
  class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg"
>
  Skip to main content
</a>

<main id="main-content">
  <!-- Page content -->
</main>
```

### Color Contrast

All text must meet WCAG AA contrast requirements:

| Element | Requirement | Min Ratio |
|---------|-------------|-----------|
| Normal text | AA | 4.5:1 |
| Large text (≥18pt) | AA | 3:1 |
| UI components | AA | 3:1 |

**Examples of compliant combinations**:
- `text-gray-900` on `bg-white` ✅
- `text-gray-600` on `bg-white` ✅
- `text-white` on `bg-blue-600` ✅

**Avoid**:
- `text-gray-400` on `bg-white` ❌ (insufficient contrast)

### Reduced Motion

Respect user preferences for reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

In Svelte:

```svelte
<script>
  import { browser } from '$app/environment';

  const prefersReducedMotion = browser
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;
</script>

<div class={prefersReducedMotion ? '' : 'transition-all duration-200'}>
  <!-- content -->
</div>
```

---

## Loading States

### Skeleton Loaders

```html
<div class="animate-pulse">
  <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div class="h-4 bg-gray-200 rounded w-1/2"></div>
</div>
```

### Calculating Spinner

```html
<div class="flex items-center gap-2 text-gray-500">
  <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
  <span>Calculating...</span>
</div>
```

### Screen Reader Announcements

```html
<div role="status" aria-live="polite" class="sr-only">
  Loading payroll data...
</div>
```

---

## Error States

### Inline Validation Error

```html
<div class="relative">
  <input
    type="text"
    class="border-red-500 focus:ring-red-500"
    aria-invalid="true"
    aria-describedby="gross-pay-error"
  />
  <p id="gross-pay-error" class="mt-1 text-sm text-red-600">
    Gross pay must be a positive number
  </p>
</div>
```

### API Error Alert

```html
<div role="alert" class="bg-red-50 border-l-4 border-red-500 p-4">
  <div class="flex">
    <ExclamationIcon class="h-5 w-5 text-red-400" />
    <div class="ml-3">
      <p class="text-sm text-red-700">
        Failed to calculate payroll. Please try again.
      </p>
    </div>
  </div>
</div>
```

---

## Empty States

```html
<div class="text-center py-12">
  <UsersIcon class="mx-auto h-12 w-12 text-gray-400" />
  <h3 class="mt-2 text-sm font-medium text-gray-900">No employees</h3>
  <p class="mt-1 text-sm text-gray-500">
    Get started by adding your first employee.
  </p>
  <div class="mt-6">
    <button class="btn-primary">
      <PlusIcon class="w-5 h-5 mr-2" />
      Add Employee
    </button>
  </div>
</div>
```

---

## Checklist

### Responsive Design
- [ ] Minimum 768px width supported
- [ ] Mobile fallback message displayed < 768px
- [ ] Columns hide/show appropriately at breakpoints
- [ ] Forms stack to single column on smaller screens
- [ ] Touch targets minimum 44×44px

### Keyboard Navigation
- [ ] All interactive elements focusable via Tab
- [ ] Focus order follows logical reading order
- [ ] Focus indicator visible on all elements
- [ ] Escape closes modals/panels
- [ ] Enter activates buttons and editable cells

### Screen Reader
- [ ] All images have alt text
- [ ] Form fields have labels
- [ ] Buttons have descriptive labels
- [ ] Tables have proper roles and headers
- [ ] Live regions announce dynamic updates
- [ ] Skip link available

### Color & Contrast
- [ ] Text contrast ≥ 4.5:1 (normal) or 3:1 (large)
- [ ] Color not the only way to convey information
- [ ] Focus states visible
- [ ] Error states identifiable without color
