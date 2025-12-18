<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Employee, ColumnGroup, EmployeeFilters, EmployeeStatusCounts } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		DEFAULT_EMPLOYEE_FILTERS
	} from '$lib/types/employee';
	import type { PayGroup } from '$lib/types/pay-group';
	import { EmployeeTable, EmployeeDetailSidebar, EmployeeFilters as EmployeeFiltersComponent } from '$lib/components/employees';
	import { listEmployees } from '$lib/services/employeeService';
	import { listPayGroups } from '$lib/services/payGroupService';

	// ===========================================
	// State
	// ===========================================
	let employees = $state<Employee[]>([]);
	let payGroups = $state<PayGroup[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let selectedIds = $state<Set<string>>(new Set());
	let filters = $state<EmployeeFilters>({ ...DEFAULT_EMPLOYEE_FILTERS });
	let activeColumnGroup = $state<ColumnGroup>('personal');
	let selectedEmployeeId = $state<string | null>(null);
	let showSidebarSIN = $state(false);

	// ===========================================
	// Data Loading
	// ===========================================
	async function loadEmployees() {
		isLoading = true;
		error = null;
		try {
			const result = await listEmployees({ activeOnly: false });
			if (result.error) {
				error = result.error;
			} else {
				employees = result.data;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load employees';
		} finally {
			isLoading = false;
		}
	}

	async function loadPayGroups() {
		try {
			const result = await listPayGroups();
			if (!result.error) {
				payGroups = result.data;
			}
		} catch (err) {
			console.warn('Failed to load pay groups for filter:', err);
		}
	}

	// Load employees and pay groups on mount
	$effect(() => {
		loadEmployees();
		loadPayGroups();
	});

	// ===========================================
	// Computed
	// ===========================================
	const filteredEmployees = $derived(() => {
		return employees.filter((emp) => {
			// Status filter
			if (filters.status !== 'all' && emp.status !== filters.status) return false;

			// Province filter
			if (filters.province !== 'all' && emp.provinceOfEmployment !== filters.province) return false;

			// Pay frequency filter
			if (filters.payFrequency !== 'all' && emp.payFrequency !== filters.payFrequency) return false;

			// Employment type filter
			if (filters.employmentType !== 'all' && emp.employmentType !== filters.employmentType) return false;

			// Compensation type filter
			if (filters.compensationType !== 'all') {
				const isSalaried = emp.annualSalary !== null && emp.annualSalary !== undefined;
				if (filters.compensationType === 'salaried' && !isSalaried) return false;
				if (filters.compensationType === 'hourly' && isSalaried) return false;
			}

			// Pay group filter
			if (filters.payGroupId !== 'all') {
				if (filters.payGroupId === 'unassigned') {
					// Show only employees without a pay group
					if (emp.payGroupId) return false;
				} else {
					// Show only employees in the selected pay group
					if (emp.payGroupId !== filters.payGroupId) return false;
				}
			}

			// Search filter (enhanced)
			if (filters.searchQuery) {
				const query = filters.searchQuery.toLowerCase();
				const fullName = `${emp.firstName} ${emp.lastName}`.toLowerCase();
				const email = emp.email?.toLowerCase() || '';
				const provinceName = PROVINCE_LABELS[emp.provinceOfEmployment].toLowerCase();
				const sinLast3 = emp.sin?.slice(-3) || '';

				return (
					fullName.includes(query) ||
					email.includes(query) ||
					provinceName.includes(query) ||
					sinLast3.includes(query)
				);
			}
			return true;
		});
	});

	const statusCounts = $derived<EmployeeStatusCounts>({
		total: employees.length,
		draft: employees.filter((e) => e.status === 'draft').length,
		active: employees.filter((e) => e.status === 'active').length,
		terminated: employees.filter((e) => e.status === 'terminated').length
	});

	// Summary statistics for cards
	const summaryCounts = $derived({
		total: employees.length,
		active: employees.filter((e) => e.status === 'active').length,
		salaried: employees.filter((e) => e.annualSalary !== null && e.annualSalary !== undefined).length,
		hourly: employees.filter((e) => e.hourlyRate !== null && e.hourlyRate !== undefined).length,
		unassigned: employees.filter((e) => !e.payGroupId).length
	});

	const selectedEmployee = $derived(() => {
		if (!selectedEmployeeId) return null;
		return employees.find((e) => e.id === selectedEmployeeId) || null;
	});

	// ===========================================
	// Actions
	// ===========================================
	function toggleSelectAll() {
		const filtered = filteredEmployees();
		if (selectedIds.size === filtered.length) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(filtered.map((e) => e.id));
		}
	}

	function toggleSelect(id: string) {
		const newSet = new Set(selectedIds);
		if (newSet.has(id)) {
			newSet.delete(id);
		} else {
			newSet.add(id);
		}
		selectedIds = newSet;
	}

	function handleRowClick(id: string) {
		selectedEmployeeId = id;
	}

	function closeDetails() {
		selectedEmployeeId = null;
		showSidebarSIN = false;
	}

	function toggleSidebarSIN() {
		showSidebarSIN = !showSidebarSIN;
	}

	function handleAddEmployee() {
		goto('/employees/new');
	}
</script>

<svelte:head>
	<title>Employees - BeanFlow Payroll</title>
</svelte:head>

<div class="employees-page" class:has-sidebar={selectedEmployeeId}>
	<!-- Main Content -->
	<div class="main-content">
		<!-- Header -->
		<header class="page-header">
			<div class="header-content">
				<h1 class="page-title">Employees</h1>
				<p class="page-subtitle">Manage your team and payroll information</p>
			</div>
			<div class="header-actions">
				<button class="btn-secondary">
					<i class="fas fa-file-import"></i>
					<span>Import</span>
				</button>
				<button class="btn-primary" onclick={handleAddEmployee}>
					<i class="fas fa-plus"></i>
					<span>Add Employee</span>
				</button>
			</div>
		</header>

		<!-- Error Message -->
		{#if error}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button class="error-dismiss" onclick={() => error = null}>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Summary Cards -->
		{#if !isLoading}
			<div class="summary-cards">
				<div class="summary-card">
					<div class="summary-icon total">
						<i class="fas fa-users"></i>
					</div>
					<div class="summary-content">
						<span class="summary-value">{summaryCounts.total}</span>
						<span class="summary-label">Total Employees</span>
					</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon active">
						<i class="fas fa-user-check"></i>
					</div>
					<div class="summary-content">
						<span class="summary-value">{summaryCounts.active}</span>
						<span class="summary-label">Active</span>
					</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon salaried">
						<i class="fas fa-money-bill-wave"></i>
					</div>
					<div class="summary-content">
						<span class="summary-value">{summaryCounts.salaried}</span>
						<span class="summary-label">Salaried</span>
					</div>
				</div>
				<div class="summary-card">
					<div class="summary-icon hourly">
						<i class="fas fa-clock"></i>
					</div>
					<div class="summary-content">
						<span class="summary-value">{summaryCounts.hourly}</span>
						<span class="summary-label">Hourly</span>
					</div>
				</div>
				{#if summaryCounts.unassigned > 0}
					<div class="summary-card warning">
						<div class="summary-icon unassigned">
							<i class="fas fa-exclamation-triangle"></i>
						</div>
						<div class="summary-content">
							<span class="summary-value">{summaryCounts.unassigned}</span>
							<span class="summary-label">Unassigned</span>
						</div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Loading State -->
		{#if isLoading}
			<div class="loading-container">
				<div class="loading-spinner"></div>
				<p>Loading employees...</p>
			</div>
		{:else}
			<!-- Employee Filters -->
			<EmployeeFiltersComponent
				{filters}
				{statusCounts}
				{payGroups}
				onFiltersChange={(newFilters) => (filters = newFilters)}
			/>

			<!-- Employee Table -->
			<EmployeeTable
				employees={filteredEmployees()}
				{selectedIds}
				{activeColumnGroup}
				onToggleSelectAll={toggleSelectAll}
				onToggleSelect={toggleSelect}
				onRowClick={handleRowClick}
			/>

			<!-- Results Summary -->
			<div class="results-summary">
				<span class="results-count">
					Showing {filteredEmployees().length} of {employees.length} employee{employees.length !== 1 ? 's' : ''}
				</span>
			</div>
		{/if}
	</div>

	<!-- Detail Sidebar -->
	{#if selectedEmployee()}
		<EmployeeDetailSidebar
			employee={selectedEmployee()!}
			showSIN={showSidebarSIN}
			onToggleSIN={toggleSidebarSIN}
			onClose={closeDetails}
		/>
	{/if}
</div>

<style>
	.employees-page {
		display: flex;
		gap: var(--spacing-6);
		max-width: 1400px;
	}

	.main-content {
		flex: 1;
		min-width: 0;
	}

	.employees-page.has-sidebar .main-content {
		max-width: calc(100% - 380px);
	}

	/* Summary Cards */
	.summary-cards {
		display: flex;
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-5);
		flex-wrap: wrap;
	}

	.summary-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-1);
		min-width: 140px;
		flex: 1;
		max-width: 200px;
	}

	.summary-card.warning {
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
	}

	.summary-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: var(--radius-md);
		font-size: 1rem;
	}

	.summary-icon.total {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.summary-icon.active {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.summary-icon.salaried {
		background: var(--color-info-100, #e0f2fe);
		color: var(--color-info-600, #0284c7);
	}

	.summary-icon.hourly {
		background: var(--color-secondary-100, #f5f3ff);
		color: var(--color-secondary-600, #7c3aed);
	}

	.summary-icon.unassigned {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.summary-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.summary-value {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
		line-height: 1;
	}

	.summary-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
		flex-wrap: wrap;
		gap: var(--spacing-4);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.page-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.header-actions {
		display: flex;
		gap: var(--spacing-3);
	}

	.btn-primary,
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.btn-primary:disabled,
	.btn-secondary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Error Banner */
	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-danger-50, #fef2f2);
		border: 1px solid var(--color-danger-200, #fecaca);
		border-radius: var(--radius-lg);
		color: var(--color-danger-700, #b91c1c);
		margin-bottom: var(--spacing-4);
	}

	.error-banner i:first-child {
		font-size: 1.25rem;
	}

	.error-banner span {
		flex: 1;
	}

	.error-dismiss {
		background: none;
		border: none;
		color: var(--color-danger-500, #ef4444);
		cursor: pointer;
		padding: var(--spacing-1);
		opacity: 0.7;
	}

	.error-dismiss:hover {
		opacity: 1;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12) var(--spacing-6);
		gap: var(--spacing-4);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500, #3b82f6);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-container p {
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Results Summary */
	.results-summary {
		display: flex;
		justify-content: flex-end;
		padding: var(--spacing-3) 0;
		margin-top: var(--spacing-2);
	}

	.results-count {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.employees-page.has-sidebar {
			flex-direction: column;
		}

		.employees-page.has-sidebar .main-content {
			max-width: 100%;
		}
	}

	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
		}

		.header-actions {
			width: 100%;
		}

		.btn-primary,
		.btn-secondary {
			flex: 1;
			justify-content: center;
		}
	}
</style>
