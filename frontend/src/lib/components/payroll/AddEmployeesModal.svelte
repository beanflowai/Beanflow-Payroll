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
<div
	class="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000] p-4"
	onclick={handleOverlayClick}
>
	<div
		class="bg-white rounded-xl shadow-xl w-full max-w-[500px] max-h-[80vh] flex flex-col overflow-hidden"
		onclick={(e) => e.stopPropagation()}
	>
		<div class="flex justify-between items-center py-4 px-5 border-b border-surface-200">
			<h3 class="text-title-small font-semibold text-surface-800 m-0">Add Employees to {payGroup.name}</h3>
			<button
				class="flex items-center justify-center w-8 h-8 bg-transparent border-none text-surface-500 cursor-pointer rounded-md transition-all duration-150 hover:bg-surface-100 hover:text-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
				onclick={onClose}
				disabled={isAssigning}
			>
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="flex-1 overflow-y-auto py-4 px-5">
			{#if unassignedEmployees.length === 0}
				<div class="flex flex-col items-center text-center py-6">
					<i class="fas fa-info-circle text-[48px] text-surface-300 mb-4"></i>
					<p class="text-body-content text-surface-600 m-0 mb-2">No unassigned employees available.</p>
					<p class="text-body-small text-surface-500 mb-4">All employees are already assigned to a pay group, or you need to add employees first.</p>
					<a
						href="/employees"
						class="flex items-center gap-2 py-2 px-4 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-small font-medium no-underline cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
					>
						<i class="fas fa-arrow-right"></i>
						Go to Employees
					</a>
				</div>
			{:else}
				<div class="p-3 bg-surface-50 rounded-lg mb-3">
					<label class="flex items-center gap-3 cursor-pointer text-body-content font-medium text-surface-700">
						<input
							type="checkbox"
							class="w-[18px] h-[18px] cursor-pointer"
							checked={selectedEmployeeIds.size === unassignedEmployees.length}
							onchange={toggleSelectAllEmployees}
							disabled={isAssigning}
						/>
						<span>Select All ({unassignedEmployees.length})</span>
					</label>
				</div>

				<div class="flex flex-col gap-2">
					{#each unassignedEmployees as employee (employee.id)}
						<label
							class="flex items-center gap-3 p-3 border border-surface-200 rounded-lg cursor-pointer transition-all duration-150 hover:bg-surface-50 hover:border-surface-300"
							class:bg-primary-50={selectedEmployeeIds.has(employee.id)}
							class:border-primary-300={selectedEmployeeIds.has(employee.id)}
						>
							<input
								type="checkbox"
								class="w-[18px] h-[18px] cursor-pointer"
								checked={selectedEmployeeIds.has(employee.id)}
								onchange={() => toggleEmployeeSelect(employee.id)}
								disabled={isAssigning}
							/>
							<div class="flex flex-col gap-0.5">
								<span class="text-body-content font-medium text-surface-800">{employee.firstName} {employee.lastName}</span>
								<span class="text-body-small text-surface-500">
									{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
								</span>
							</div>
						</label>
					{/each}
				</div>
			{/if}
		</div>

		{#if unassignedEmployees.length > 0}
			<div class="flex justify-end gap-3 py-4 px-5 border-t border-surface-200 bg-surface-50">
				<button
					class="py-2 px-4 bg-white text-surface-700 border border-surface-300 rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:border-surface-400 disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={onClose}
					disabled={isAssigning}
				>
					Cancel
				</button>
				<button
					class="flex items-center gap-2 py-2 px-4 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
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
