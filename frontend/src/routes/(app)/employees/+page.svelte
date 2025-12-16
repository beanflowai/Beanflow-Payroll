<script lang="ts">
	import type { Employee, ColumnGroup, EmployeeFilters, EmployeeStatusCounts } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		DEFAULT_EMPLOYEE_FILTERS,
		FEDERAL_BPA_2025,
		PROVINCIAL_BPA_2025
	} from '$lib/types/employee';
	import { EmployeeTable, EmployeeDetailSidebar, EmployeeFilters as EmployeeFiltersComponent } from '$lib/components/employees';
	import {
		listEmployees,
		createEmployee,
		updateEmployee,
		deleteEmployee as deleteEmployeeService
	} from '$lib/services/employeeService';
	import type { EmployeeCreateInput, EmployeeUpdateInput } from '$lib/types/employee';

	// ===========================================
	// State
	// ===========================================
	let employees = $state<Employee[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let isSaving = $state(false);
	let selectedIds = $state<Set<string>>(new Set());
	let filters = $state<EmployeeFilters>({ ...DEFAULT_EMPLOYEE_FILTERS });
	let activeColumnGroup = $state<ColumnGroup>('personal');
	let showSINMap = $state<Record<string, boolean>>({});
	let editingCell = $state<{ id: string; field: string } | null>(null);
	let selectedEmployeeId = $state<string | null>(null);

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

	// Load employees on mount
	$effect(() => {
		loadEmployees();
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

	const selectedEmployee = $derived(() => {
		if (!selectedEmployeeId) return null;
		return employees.find((e) => e.id === selectedEmployeeId) || null;
	});

	// ===========================================
	// Actions
	// ===========================================
	function toggleSIN(id: string) {
		showSINMap[id] = !showSINMap[id];
	}

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

	function startEdit(id: string, field: string) {
		editingCell = { id, field };
	}

	function stopEdit() {
		editingCell = null;
	}

	function openDetails(id: string) {
		selectedEmployeeId = id;
	}

	function closeDetails() {
		selectedEmployeeId = null;
	}

	function addNewRow() {
		const newEmployee: Employee = {
			id: `new-${Date.now()}`,
			firstName: '',
			lastName: '',
			sin: '',
			email: '',
			provinceOfEmployment: 'ON',
			payFrequency: 'bi_weekly',
			employmentType: 'full_time',
			status: 'draft',
			hireDate: new Date().toISOString().split('T')[0],
			terminationDate: null,
			annualSalary: 0,
			hourlyRate: null,
			federalClaimAmount: 16129,
			provincialClaimAmount: 12399,
			isCppExempt: false,
			isEiExempt: false,
			cpp2Exempt: false,
			rrspPerPeriod: 0,
			unionDuesPerPeriod: 0,
			vacationConfig: { payoutMethod: 'accrual', vacationRate: '0.04' },
			vacationBalance: 0
		};
		employees = [...employees, newEmployee];
	}

	function toggleCompensationType(id: string) {
		employees = employees.map((emp) => {
			if (emp.id === id) {
				// Switch between salary and hourly
				const isCurrentlyHourly = emp.hourlyRate !== null && emp.hourlyRate !== undefined;
				if (isCurrentlyHourly) {
					// Currently hourly -> switch to salary
					const salary = Math.round((emp.hourlyRate || 0) * 2080);
					return { ...emp, annualSalary: salary, hourlyRate: null };
				} else {
					// Currently salary -> switch to hourly
					const hourly = Number(((emp.annualSalary || 0) / 2080).toFixed(2));
					return { ...emp, hourlyRate: hourly, annualSalary: null };
				}
			}
			return emp;
		});
	}

	async function handleDeleteEmployee(id: string) {
		const emp = employees.find((e) => e.id === id);
		if (!emp) return;

		if (!confirm(`Are you sure you want to delete ${emp.firstName} ${emp.lastName}?`)) return;

		// For new (unsaved) employees, just remove locally
		if (id.startsWith('new-')) {
			employees = employees.filter((e) => e.id !== id);
			return;
		}

		// Delete from Supabase
		isSaving = true;
		const result = await deleteEmployeeService(id);
		isSaving = false;

		if (result.error) {
			alert(`Failed to delete employee: ${result.error}`);
			return;
		}

		// Remove from local state
		employees = employees.filter((e) => e.id !== id);

		// Also remove from selection if selected
		if (selectedIds.has(id)) {
			const newSet = new Set(selectedIds);
			newSet.delete(id);
			selectedIds = newSet;
		}

		// Close detail sidebar if this employee was selected
		if (selectedEmployeeId === id) {
			selectedEmployeeId = null;
		}
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
				<button class="btn-primary" onclick={addNewRow} disabled={isSaving}>
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
				onFiltersChange={(newFilters) => (filters = newFilters)}
			/>

			<!-- Employee Table -->
			<EmployeeTable
				employees={filteredEmployees()}
				{selectedIds}
				{activeColumnGroup}
				{showSINMap}
				{editingCell}
				onToggleSelectAll={toggleSelectAll}
				onToggleSelect={toggleSelect}
				onToggleSIN={toggleSIN}
				onStartEdit={startEdit}
				onStopEdit={stopEdit}
				onOpenDetails={openDetails}
				onAddNewRow={addNewRow}
				onToggleCompensationType={toggleCompensationType}
				onDeleteEmployee={handleDeleteEmployee}
			/>

			<!-- Results Summary -->
			<div class="results-summary">
				<span class="results-count">
					Showing {filteredEmployees().length} of {employees.length} employee{employees.length !== 1 ? 's' : ''}
				</span>
				{#if isSaving}
					<span class="saving-indicator">
						<i class="fas fa-spinner fa-spin"></i> Saving...
					</span>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Detail Sidebar -->
	{#if selectedEmployee()}
		<EmployeeDetailSidebar
			employee={selectedEmployee()!}
			showSIN={showSINMap[selectedEmployee()?.id || ''] || false}
			onToggleSIN={() => toggleSIN(selectedEmployee()?.id || '')}
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

	/* Saving Indicator */
	.saving-indicator {
		font-size: var(--font-size-body-small);
		color: var(--color-primary-600, #2563eb);
		margin-left: var(--spacing-4);
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
