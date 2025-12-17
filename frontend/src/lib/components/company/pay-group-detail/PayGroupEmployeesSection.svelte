<script lang="ts">
	// PayGroupEmployeesSection - Manage employees assigned to a pay group
	import type { PayGroup } from '$lib/types/pay-group';
	import type { Employee } from '$lib/types/employee';
	import { PROVINCE_LABELS } from '$lib/types/employee';
	import {
		getEmployeesByPayGroup,
		getUnassignedEmployees,
		assignEmployeesToPayGroup,
		removeEmployeeFromPayGroup
	} from '$lib/services/employeeService';

	interface Props {
		payGroup: PayGroup;
		onEmployeeCountChange?: (count: number) => void;
	}

	let { payGroup, onEmployeeCountChange }: Props = $props();

	// State
	let employees = $state<Employee[]>([]);
	let unassignedEmployees = $state<Employee[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let showModal = $state(false);
	let selectedIds = $state<Set<string>>(new Set());
	let isAssigning = $state(false);
	let isRemoving = $state<string | null>(null);

	// Load employees when pay group changes
	$effect(() => {
		if (payGroup.id) {
			loadEmployees();
		}
	});

	async function loadEmployees() {
		isLoading = true;
		error = null;

		try {
			const result = await getEmployeesByPayGroup(payGroup.id);
			if (result.error) {
				error = result.error;
			} else {
				employees = result.data;
				onEmployeeCountChange?.(employees.length);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load employees';
		} finally {
			isLoading = false;
		}
	}

	async function loadUnassignedEmployees() {
		try {
			const result = await getUnassignedEmployees();
			if (result.error) {
				console.error('Failed to load unassigned employees:', result.error);
				unassignedEmployees = [];
			} else {
				unassignedEmployees = result.data;
			}
		} catch (err) {
			console.error('Failed to load unassigned employees:', err);
			unassignedEmployees = [];
		}
	}

	function openModal() {
		selectedIds = new Set();
		loadUnassignedEmployees();
		showModal = true;
	}

	function closeModal() {
		showModal = false;
		selectedIds = new Set();
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

	function toggleSelectAll() {
		if (selectedIds.size === unassignedEmployees.length) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(unassignedEmployees.map((e) => e.id));
		}
	}

	async function handleAssign() {
		if (selectedIds.size === 0) return;

		isAssigning = true;
		try {
			const result = await assignEmployeesToPayGroup(Array.from(selectedIds), payGroup.id);
			if (result.error) {
				error = result.error;
			} else {
				closeModal();
				await loadEmployees();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to assign employees';
		} finally {
			isAssigning = false;
		}
	}

	async function handleRemove(employeeId: string, employeeName: string) {
		if (!confirm(`Remove ${employeeName} from this pay group?`)) return;

		isRemoving = employeeId;
		try {
			const result = await removeEmployeeFromPayGroup(employeeId);
			if (result.error) {
				error = result.error;
			} else {
				await loadEmployees();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to remove employee';
		} finally {
			isRemoving = null;
		}
	}

	function formatCompensation(employee: Employee): string {
		if (employee.annualSalary) {
			return `$${employee.annualSalary.toLocaleString()}/yr`;
		}
		if (employee.hourlyRate) {
			return `$${employee.hourlyRate.toFixed(2)}/hr`;
		}
		return '—';
	}
</script>

<section class="employees-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-users"></i>
			Employees
			<span class="employee-count">({employees.length})</span>
		</h2>
		<button class="btn-add" onclick={openModal}>
			<i class="fas fa-user-plus"></i>
			Add Employees
		</button>
	</div>

	<div class="section-content">
		{#if error}
			<div class="error-message">
				<i class="fas fa-exclamation-circle"></i>
				{error}
				<button class="btn-dismiss" onclick={() => (error = null)}>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		{#if isLoading}
			<div class="loading-state">
				<i class="fas fa-spinner fa-spin"></i>
				Loading employees...
			</div>
		{:else if employees.length === 0}
			<div class="empty-state">
				<div class="empty-icon">
					<i class="fas fa-user-plus"></i>
				</div>
				<p>No employees assigned to this pay group yet.</p>
				<button class="btn-add-empty" onclick={openModal}>
					<i class="fas fa-plus"></i>
					Add Employees
				</button>
			</div>
		{:else}
			<div class="employees-table-wrapper">
				<table class="employees-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>Province</th>
							<th>Compensation</th>
							<th>Type</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						{#each employees as employee (employee.id)}
							<tr>
								<td class="name-cell">
									<span class="employee-name">{employee.firstName} {employee.lastName}</span>
									{#if employee.email}
										<span class="employee-email">{employee.email}</span>
									{/if}
								</td>
								<td>{PROVINCE_LABELS[employee.provinceOfEmployment]}</td>
								<td>{formatCompensation(employee)}</td>
								<td>
									<span class="type-badge {employee.employmentType}">
										{employee.employmentType === 'full_time' ? 'Full-time' : 'Part-time'}
									</span>
								</td>
								<td class="action-cell">
									<button
										class="btn-remove"
										onclick={() => handleRemove(employee.id, `${employee.firstName} ${employee.lastName}`)}
										disabled={isRemoving === employee.id}
									>
										{#if isRemoving === employee.id}
											<i class="fas fa-spinner fa-spin"></i>
										{:else}
											<i class="fas fa-times"></i>
										{/if}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</section>

<!-- Add Employees Modal -->
{#if showModal}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="modal-overlay" onclick={closeModal}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>Add Employees to {payGroup.name}</h3>
				<button class="btn-close" onclick={closeModal}>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<div class="modal-body">
				{#if unassignedEmployees.length === 0}
					<div class="modal-empty">
						<i class="fas fa-info-circle"></i>
						<p>No unassigned employees available.</p>
						<p class="hint">All employees are already assigned to a pay group, or you need to add employees first.</p>
						<a href="/employees" class="btn-go-employees">
							<i class="fas fa-arrow-right"></i>
							Go to Employees
						</a>
					</div>
				{:else}
					<div class="select-all-row">
						<label class="checkbox-label">
							<input
								type="checkbox"
								checked={selectedIds.size === unassignedEmployees.length}
								onchange={toggleSelectAll}
							/>
							<span>Select All ({unassignedEmployees.length})</span>
						</label>
					</div>

					<div class="employees-list">
						{#each unassignedEmployees as employee (employee.id)}
							<label class="employee-row">
								<input
									type="checkbox"
									checked={selectedIds.has(employee.id)}
									onchange={() => toggleSelect(employee.id)}
								/>
								<div class="employee-info">
									<span class="name">{employee.firstName} {employee.lastName}</span>
									<span class="details">
										{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
									</span>
								</div>
							</label>
						{/each}
					</div>
				{/if}
			</div>

			{#if unassignedEmployees.length > 0}
				<div class="modal-footer">
					<button class="btn-cancel" onclick={closeModal}>Cancel</button>
					<button
						class="btn-assign"
						onclick={handleAssign}
						disabled={selectedIds.size === 0 || isAssigning}
					>
						{#if isAssigning}
							<i class="fas fa-spinner fa-spin"></i>
							Assigning...
						{:else}
							<i class="fas fa-check"></i>
							Add {selectedIds.size} Employee{selectedIds.size !== 1 ? 's' : ''}
						{/if}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.employees-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.section-title {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.section-title i {
		color: var(--color-primary-500);
	}

	.employee-count {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-normal);
		color: var(--color-surface-500);
	}

	.btn-add {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add:hover {
		background: var(--color-primary-600);
	}

	.section-content {
		padding: var(--spacing-5);
	}

	/* Error Message */
	.error-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-error-50);
		color: var(--color-error-700);
		border-radius: var(--radius-md);
		margin-bottom: var(--spacing-4);
	}

	.error-message .btn-dismiss {
		margin-left: auto;
		background: none;
		border: none;
		color: var(--color-error-500);
		cursor: pointer;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-8);
		color: var(--color-surface-500);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--spacing-8) var(--spacing-4);
		text-align: center;
	}

	.empty-icon {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		background: var(--color-surface-100);
		color: var(--color-surface-400);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 24px;
		margin-bottom: var(--spacing-4);
	}

	.empty-state p {
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
	}

	.btn-add-empty {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-empty:hover {
		opacity: 0.9;
	}

	/* Employees Table */
	.employees-table-wrapper {
		overflow-x: auto;
	}

	.employees-table {
		width: 100%;
		border-collapse: collapse;
	}

	.employees-table th,
	.employees-table td {
		padding: var(--spacing-3) var(--spacing-4);
		text-align: left;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.employees-table th {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.employees-table tbody tr:hover {
		background: var(--color-surface-50);
	}

	.name-cell {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-email {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.type-badge.full_time {
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	.type-badge.part_time {
		background: var(--color-info-50);
		color: var(--color-info-700);
	}

	.action-cell {
		text-align: right;
		width: 40px;
	}

	.btn-remove {
		width: 28px;
		height: 28px;
		border-radius: var(--radius-md);
		background: transparent;
		border: none;
		color: var(--color-surface-400);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-remove:hover:not(:disabled) {
		background: var(--color-error-50);
		color: var(--color-error-600);
	}

	.btn-remove:disabled {
		cursor: not-allowed;
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal-content {
		background: white;
		border-radius: var(--radius-xl);
		width: 100%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		box-shadow: var(--shadow-md3-3);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-header h3 {
		margin: 0;
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.btn-close {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-md);
		background: transparent;
		border: none;
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-close:hover {
		background: var(--color-surface-100);
	}

	.modal-body {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-4) var(--spacing-5);
	}

	.modal-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: var(--spacing-6);
	}

	.modal-empty i {
		font-size: 32px;
		color: var(--color-surface-400);
		margin-bottom: var(--spacing-4);
	}

	.modal-empty p {
		color: var(--color-surface-600);
		margin: 0;
	}

	.modal-empty .hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-top: var(--spacing-2);
	}

	.btn-go-employees {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border-radius: var(--radius-md);
		text-decoration: none;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		transition: var(--transition-fast);
	}

	.btn-go-employees:hover {
		background: var(--color-primary-600);
	}

	.select-all-row {
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
		margin-bottom: var(--spacing-3);
	}

	.employees-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.employee-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.employee-row:hover {
		background: var(--color-surface-50);
	}

	.employee-row input[type='checkbox'] {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary-500);
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-info .name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-info .details {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
	}

	.checkbox-label span {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-cancel {
		padding: var(--spacing-2) var(--spacing-4);
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel:hover {
		background: var(--color-surface-100);
	}

	.btn-assign {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-assign:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-assign:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.section-header {
			flex-direction: column;
			gap: var(--spacing-3);
			align-items: flex-start;
		}

		.btn-add {
			width: 100%;
			justify-content: center;
		}

		.employees-table th:nth-child(3),
		.employees-table td:nth-child(3),
		.employees-table th:nth-child(4),
		.employees-table td:nth-child(4) {
			display: none;
		}
	}
</style>
