<script lang="ts">
	// PayGroupEmployeesSection - Manage employees assigned to a pay group
	import type { PayGroup } from '$lib/types/pay-group';
	import type { Employee } from '$lib/types/employee';
	import { PROVINCE_LABELS, PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS } from '$lib/types/employee';
	import SlideOverPanel from '$lib/components/ui/SlideOverPanel.svelte';
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
			// Filter by matching employment type and pay frequency
			const result = await getUnassignedEmployees({
				employmentType: payGroup.employmentType,
				payFrequency: payGroup.payFrequency
			});
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

<section class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
	<div class="flex justify-between items-center p-4 px-5 bg-surface-50 border-b border-surface-100 max-sm:flex-col max-sm:gap-3 max-sm:items-start">
		<h2 class="flex items-center gap-2 text-title-medium font-semibold text-surface-800 m-0">
			<i class="fas fa-users text-primary-500"></i>
			Employees
			<span class="text-body-content font-normal text-surface-500">({employees.length})</span>
		</h2>
		<button
			class="inline-flex items-center gap-2 py-2 px-4 bg-primary-500 text-white border-none rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] hover:bg-primary-600 max-sm:w-full max-sm:justify-center"
			onclick={openModal}
		>
			<i class="fas fa-user-plus"></i>
			Add Employees
		</button>
	</div>

	<div class="p-5">
		{#if error}
			<div class="flex items-center gap-2 py-3 px-4 bg-error-50 text-error-700 rounded-md mb-4">
				<i class="fas fa-exclamation-circle"></i>
				{error}
				<button
					class="ml-auto bg-transparent border-none text-error-500 cursor-pointer"
					onclick={() => (error = null)}
					aria-label="Dismiss error"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		{#if isLoading}
			<div class="flex items-center justify-center gap-2 py-8 text-surface-500">
				<i class="fas fa-spinner fa-spin"></i>
				Loading employees...
			</div>
		{:else if employees.length === 0}
			<div class="flex flex-col items-center py-8 px-4 text-center">
				<div class="w-16 h-16 rounded-full bg-surface-100 text-surface-400 flex items-center justify-center text-2xl mb-4">
					<i class="fas fa-user-plus"></i>
				</div>
				<p class="text-surface-600 m-0 mb-4">No employees assigned to this pay group yet.</p>
				<button
					class="inline-flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] hover:opacity-90"
					onclick={openModal}
				>
					<i class="fas fa-plus"></i>
					Add Employees
				</button>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full border-collapse">
					<thead>
						<tr>
							<th class="py-3 px-4 text-left border-b border-surface-100 text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider">Name</th>
							<th class="py-3 px-4 text-left border-b border-surface-100 text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider">Province</th>
							<th class="py-3 px-4 text-left border-b border-surface-100 text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider max-sm:hidden">Compensation</th>
							<th class="py-3 px-4 text-left border-b border-surface-100 text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider max-sm:hidden">Type</th>
							<th class="py-3 px-4 text-left border-b border-surface-100 text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider w-10"></th>
						</tr>
					</thead>
					<tbody>
						{#each employees as employee (employee.id)}
							<tr class="hover:bg-surface-50">
								<td class="py-3 px-4 text-left border-b border-surface-100 flex flex-col gap-0.5">
									<span class="font-medium text-surface-800">{employee.firstName} {employee.lastName}</span>
									{#if employee.email}
										<span class="text-auxiliary-text text-surface-500">{employee.email}</span>
									{/if}
								</td>
								<td class="py-3 px-4 text-left border-b border-surface-100">{PROVINCE_LABELS[employee.provinceOfEmployment]}</td>
								<td class="py-3 px-4 text-left border-b border-surface-100 max-sm:hidden">{formatCompensation(employee)}</td>
								<td class="py-3 px-4 text-left border-b border-surface-100 max-sm:hidden">
									<span class="inline-block py-1 px-2 rounded-full text-auxiliary-text font-medium {employee.employmentType === 'full_time' ? 'bg-success-50 text-success-700' : 'bg-info-50 text-info-700'}">
										{employee.employmentType === 'full_time' ? 'Full-time' : 'Part-time'}
									</span>
								</td>
								<td class="py-3 px-4 text-right border-b border-surface-100 w-10">
									<button
										class="w-7 h-7 rounded-md bg-transparent border-none text-surface-400 cursor-pointer transition-[150ms] hover:bg-error-50 hover:text-error-600 disabled:cursor-not-allowed"
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

<!-- Add Employees Slide-over Panel -->
<SlideOverPanel isOpen={showModal} title="Add Employees to {payGroup.name}" width="md" onClose={closeModal}>
	{#snippet children()}
		<!-- Filter info banner -->
		<div class="mb-4 p-3 bg-surface-50 rounded-md text-auxiliary-text text-surface-600">
			<i class="fas fa-filter mr-2"></i>
			Showing employees with <strong>{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType]}</strong> / <strong>{PAY_FREQUENCY_LABELS[payGroup.payFrequency]}</strong>
		</div>

		{#if unassignedEmployees.length === 0}
			<div class="flex flex-col items-center text-center py-8 px-4">
				<i class="fas fa-info-circle text-[32px] text-surface-400 mb-4"></i>
				<p class="text-surface-600 m-0">No matching unassigned employees.</p>
				<p class="text-auxiliary-text text-surface-500 mt-2">No employees match this pay group's employment type and pay frequency, or all matching employees are already assigned.</p>
				<a
					href="/employees"
					class="inline-flex items-center gap-2 mt-4 py-3 px-4 bg-primary-500 text-white rounded-md no-underline text-body-content font-medium transition-[150ms] hover:bg-primary-600"
				>
					<i class="fas fa-arrow-right"></i>
					Go to Employees
				</a>
			</div>
		{:else}
			<div class="pb-3 border-b border-surface-100 mb-3">
				<label class="flex items-center gap-2 cursor-pointer">
					<input
						type="checkbox"
						class="w-[18px] h-[18px] accent-primary-500"
						checked={selectedIds.size === unassignedEmployees.length}
						onchange={toggleSelectAll}
					/>
					<span class="text-body-content text-surface-700">Select All ({unassignedEmployees.length})</span>
				</label>
			</div>

			<div class="flex flex-col gap-2">
				{#each unassignedEmployees as employee (employee.id)}
					<label class="flex items-center gap-3 p-3 rounded-md cursor-pointer transition-[150ms] hover:bg-surface-50">
						<input
							type="checkbox"
							class="w-[18px] h-[18px] accent-primary-500"
							checked={selectedIds.has(employee.id)}
							onchange={() => toggleSelect(employee.id)}
						/>
						<div class="flex flex-col gap-0.5">
							<span class="font-medium text-surface-800">{employee.firstName} {employee.lastName}</span>
							<span class="text-auxiliary-text text-surface-500">
								{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
							</span>
						</div>
					</label>
				{/each}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if unassignedEmployees.length > 0}
			<div class="flex justify-end gap-3">
				<button
					type="button"
					class="py-2 px-4 bg-transparent text-surface-600 border border-surface-200 rounded-md text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-surface-100"
					onclick={closeModal}
				>
					Cancel
				</button>
				<button
					type="button"
					class="inline-flex items-center gap-2 py-2 px-4 bg-primary-500 text-white border-none rounded-md text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
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
	{/snippet}
</SlideOverPanel>
