<script lang="ts">
	import type { Employee } from '$lib/types/employee';
	import type { PayGroupSummary } from '$lib/types/payroll';
	import { PROVINCE_LABELS } from '$lib/types/employee';
	import SlideOverPanel from '$lib/components/ui/SlideOverPanel.svelte';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		payGroup: PayGroupSummary;
		unassignedEmployees: Employee[];
		isAssigning: boolean;
		isOpen: boolean;
		onClose: () => void;
		onAssign: (employeeIds: string[]) => void;
	}

	let { payGroup, unassignedEmployees, isAssigning, isOpen, onClose, onAssign }: Props = $props();

	let selectedEmployeeIds = $state<Set<string>>(new Set());

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
			selectedEmployeeIds = new Set(unassignedEmployees.map((e) => e.id));
		}
	}

	function handleAssign() {
		onAssign(Array.from(selectedEmployeeIds));
	}

	function handleClose() {
		selectedEmployeeIds = new Set();
		onClose();
	}
</script>

<SlideOverPanel {isOpen} title="Add Employees to {payGroup.name}" width="lg" onClose={handleClose}>
	{#if unassignedEmployees.length === 0}
		<div class="flex flex-col items-center text-center py-6">
			<i class="fas fa-info-circle text-headline-super-large text-surface-300 mb-4"></i>
			<p class="text-body-content text-surface-600 m-0 mb-2">No unassigned employees available.</p>
			<p class="text-body-small text-surface-500 mb-4">
				All employees are already assigned to a pay group, or you need to add employees first.
			</p>
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
			<label
				class="flex items-center gap-3 cursor-pointer text-body-content font-medium text-surface-700"
			>
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
						<span class="text-body-content font-medium text-surface-800"
							>{employee.firstName} {employee.lastName}</span
						>
						<span class="text-body-small text-surface-500">
							{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
						</span>
					</div>
				</label>
			{/each}
		</div>
	{/if}

	{#snippet footer()}
		{#if unassignedEmployees.length > 0}
			<div class="flex justify-end gap-3">
				<button
					class="py-2 px-4 bg-white text-surface-700 border border-surface-300 rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:border-surface-400 disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={handleClose}
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
	{/snippet}
</SlideOverPanel>
