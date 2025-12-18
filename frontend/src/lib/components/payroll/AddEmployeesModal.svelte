<script lang="ts">
	import type { Employee } from '$lib/types/employee';
	import type { PayGroupSummary } from '$lib/types/payroll';
	import { PROVINCE_LABELS } from '$lib/types/employee';

	interface Props {
		payGroup: PayGroupSummary;
		unassignedEmployees: Employee[];
		isAssigning: boolean;
		onClose: () => void;
		onAssign: (employeeIds: string[]) => void;
	}

	let {
		payGroup,
		unassignedEmployees,
		isAssigning,
		onClose,
		onAssign
	}: Props = $props();

	let selectedEmployeeIds = $state<Set<string>>(new Set());

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function formatCompensation(employee: Employee): string {
		if (employee.annualSalary) {
			return formatCurrency(employee.annualSalary) + '/yr';
		} else if (employee.hourlyRate) {
			return formatCurrency(employee.hourlyRate) + '/hr';
		}
		return '--';
	}

	function toggleEmployeeSelect(id: string) {
		const newSet = new Set(selectedEmployeeIds);
		if (newSet.has(id)) {
			newSet.delete(id);
		} else {
			newSet.add(id);
		}
		selectedEmployeeIds = newSet;
	}

	function toggleSelectAllEmployees() {
		if (selectedEmployeeIds.size === unassignedEmployees.length) {
			selectedEmployeeIds = new Set();
		} else {
			selectedEmployeeIds = new Set(unassignedEmployees.map(e => e.id));
		}
	}

	function handleAssign() {
		onAssign(Array.from(selectedEmployeeIds));
	}

	function handleOverlayClick() {
		if (!isAssigning) {
			onClose();
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="modal-overlay" onclick={handleOverlayClick}>
	<div class="modal-content" onclick={(e) => e.stopPropagation()}>
		<div class="modal-header">
			<h3>Add Employees to {payGroup.name}</h3>
			<button class="btn-close" onclick={onClose} disabled={isAssigning}>
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
							checked={selectedEmployeeIds.size === unassignedEmployees.length}
							onchange={toggleSelectAllEmployees}
							disabled={isAssigning}
						/>
						<span>Select All ({unassignedEmployees.length})</span>
					</label>
				</div>

				<div class="employees-list">
					{#each unassignedEmployees as employee (employee.id)}
						<label class="employee-row">
							<input
								type="checkbox"
								checked={selectedEmployeeIds.has(employee.id)}
								onchange={() => toggleEmployeeSelect(employee.id)}
								disabled={isAssigning}
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
				<button class="btn-cancel" onclick={onClose} disabled={isAssigning}>Cancel</button>
				<button
					class="btn-assign"
					onclick={handleAssign}
					disabled={selectedEmployeeIds.size === 0 || isAssigning}
				>
					{#if isAssigning}
						<i class="fas fa-spinner fa-spin"></i>
						Assigning...
					{:else}
						<i class="fas fa-check"></i>
						Add {selectedEmployeeIds.size} Employee{selectedEmployeeIds.size !== 1 ? 's' : ''}
					{/if}
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
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
		box-shadow: var(--shadow-xl);
		width: 100%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.modal-header h3 {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.btn-close {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		background: none;
		border: none;
		color: var(--color-surface-500);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.btn-close:hover:not(:disabled) {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.btn-close:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.modal-body {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-4) var(--spacing-5);
	}

	/* Empty State */
	.modal-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: var(--spacing-6) 0;
	}

	.modal-empty i {
		font-size: 48px;
		color: var(--color-surface-300);
		margin-bottom: var(--spacing-4);
	}

	.modal-empty p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-2);
	}

	.modal-empty .hint {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		margin-bottom: var(--spacing-4);
	}

	.btn-go-employees {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		text-decoration: none;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-go-employees:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	/* Select All */
	.select-all-row {
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-3);
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		cursor: pointer;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.checkbox-label input[type="checkbox"] {
		width: 18px;
		height: 18px;
		cursor: pointer;
	}

	/* Employees List */
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
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.employee-row:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.employee-row:has(input:checked) {
		background: var(--color-primary-50);
		border-color: var(--color-primary-300);
	}

	.employee-row input[type="checkbox"] {
		width: 18px;
		height: 18px;
		cursor: pointer;
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-info .name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-info .details {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Modal Footer */
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-200);
		background: var(--color-surface-50);
	}

	.btn-cancel {
		padding: var(--spacing-2) var(--spacing-4);
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-100);
		border-color: var(--color-surface-400);
	}

	.btn-cancel:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-assign {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-assign:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-assign:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}
</style>
