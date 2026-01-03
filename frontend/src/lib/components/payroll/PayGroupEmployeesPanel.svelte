<script lang="ts">
	import type { PayGroupSummary } from '$lib/types/payroll';
	import type { Employee } from '$lib/types/employee';
	import { PROVINCE_LABELS } from '$lib/types/employee';
	import SlideOverPanel from '$lib/components/ui/SlideOverPanel.svelte';
	import {
		getEmployeesByPayGroup,
		getUnassignedEmployees,
		assignEmployeesToPayGroup,
		removeEmployeeFromPayGroup
	} from '$lib/services/employeeService';

	interface Props {
		payGroup: PayGroupSummary;
		isOpen: boolean;
		onClose: () => void;
		onEmployeesChanged?: () => void;
	}

	let { payGroup, isOpen, onClose, onEmployeesChanged }: Props = $props();

	// State
	let assignedEmployees = $state<Employee[]>([]);
	let unassignedEmployees = $state<Employee[]>([]);
	let selectedIds = $state<Set<string>>(new Set());
	let isLoading = $state(true);
	let isAssigning = $state(false);
	let isRemoving = $state<string | null>(null);
	let error = $state<string | null>(null);
	let showAddSection = $state(false);

	// Load data when panel opens or pay group changes
	$effect(() => {
		if (isOpen && payGroup.id) {
			loadData();
		}
	});

	async function loadData() {
		isLoading = true;
		error = null;
		selectedIds = new Set();

		try {
			const [assignedResult, unassignedResult] = await Promise.all([
				getEmployeesByPayGroup(payGroup.id),
				getUnassignedEmployees()
			]);

			if (assignedResult.error) {
				error = assignedResult.error;
				return;
			}
			if (unassignedResult.error) {
				error = unassignedResult.error;
				return;
			}

			assignedEmployees = assignedResult.data;
			unassignedEmployees = unassignedResult.data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load employees';
		} finally {
			isLoading = false;
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
		error = null;

		try {
			const result = await assignEmployeesToPayGroup(Array.from(selectedIds), payGroup.id);
			if (result.error) {
				error = result.error;
				return;
			}

			await loadData();
			showAddSection = false;
			onEmployeesChanged?.();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to assign employees';
		} finally {
			isAssigning = false;
		}
	}

	async function handleRemove(employeeId: string, employeeName: string) {
		if (!confirm(`Remove ${employeeName} from this pay group?`)) return;

		isRemoving = employeeId;
		error = null;

		try {
			const result = await removeEmployeeFromPayGroup(employeeId);
			if (result.error) {
				error = result.error;
				return;
			}

			await loadData();
			onEmployeesChanged?.();
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
		return '-';
	}

	function handleClose() {
		showAddSection = false;
		selectedIds = new Set();
		onClose();
	}
</script>

<SlideOverPanel isOpen={isOpen} title="{payGroup.name} Employees" width="md" onClose={handleClose}>
	{#snippet children()}
		{#if error}
			<div class="flex items-center gap-2 p-3 bg-error-50 text-error-700 rounded-lg mb-4">
				<i class="fas fa-exclamation-circle"></i>
				<span class="flex-1">{error}</span>
				<button
					type="button"
					class="text-error-500 hover:text-error-700 cursor-pointer bg-transparent border-none"
					onclick={() => (error = null)}
					aria-label="Dismiss error"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		{#if isLoading}
			<div class="flex flex-col items-center justify-center py-12">
				<div class="w-10 h-10 border-4 border-surface-200 border-t-primary-500 rounded-full animate-spin mb-4"></div>
				<p class="text-surface-600">Loading employees...</p>
			</div>
		{:else}
			<!-- Assigned Employees Section -->
			<div class="mb-6">
				<div class="flex items-center justify-between mb-3">
					<h3 class="text-body-content font-semibold text-surface-800 m-0 flex items-center gap-2">
						<i class="fas fa-users text-primary-500"></i>
						Assigned ({assignedEmployees.length})
					</h3>
				</div>

				{#if assignedEmployees.length === 0}
					<div class="flex flex-col items-center py-8 px-4 bg-surface-50 rounded-lg text-center">
						<div class="w-14 h-14 rounded-full bg-surface-200 text-surface-400 flex items-center justify-center text-xl mb-3">
							<i class="fas fa-user-slash"></i>
						</div>
						<p class="text-surface-600 m-0">No employees assigned yet.</p>
					</div>
				{:else}
					<div class="flex flex-col gap-2">
						{#each assignedEmployees as employee (employee.id)}
							<div class="flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors">
								<div class="flex flex-col gap-0.5 min-w-0 flex-1">
									<span class="font-medium text-surface-800 truncate">
										{employee.firstName} {employee.lastName}
									</span>
									<span class="text-auxiliary-text text-surface-500 truncate">
										{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
									</span>
								</div>
								<button
									type="button"
									class="w-8 h-8 flex items-center justify-center rounded-md text-surface-400 hover:bg-error-50 hover:text-error-600 transition-colors cursor-pointer border-none bg-transparent shrink-0 ml-2 disabled:opacity-50 disabled:cursor-not-allowed"
									onclick={() => handleRemove(employee.id, `${employee.firstName} ${employee.lastName}`)}
									disabled={isRemoving === employee.id}
									title="Remove from pay group"
								>
									{#if isRemoving === employee.id}
										<i class="fas fa-spinner fa-spin"></i>
									{:else}
										<i class="fas fa-times"></i>
									{/if}
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Add Employees Section -->
			<div>
				<button
					type="button"
					class="flex items-center justify-between w-full p-3 bg-surface-50 rounded-lg cursor-pointer border-none text-left hover:bg-surface-100 transition-colors"
					onclick={() => (showAddSection = !showAddSection)}
				>
					<span class="flex items-center gap-2 font-medium text-surface-700">
						<i class="fas fa-user-plus text-primary-500"></i>
						Add Employees
						{#if unassignedEmployees.length > 0}
							<span class="text-auxiliary-text font-normal text-surface-500">({unassignedEmployees.length} available)</span>
						{/if}
					</span>
					<i class="fas fa-chevron-{showAddSection ? 'up' : 'down'} text-surface-400"></i>
				</button>

				{#if showAddSection}
					<div class="mt-3 border border-surface-200 rounded-lg overflow-hidden">
						{#if unassignedEmployees.length === 0}
							<div class="flex flex-col items-center py-8 px-4 text-center">
								<i class="fas fa-info-circle text-2xl text-surface-400 mb-3"></i>
								<p class="text-surface-600 m-0 mb-1">No unassigned employees available.</p>
								<p class="text-auxiliary-text text-surface-500 m-0">All employees are already assigned to a pay group.</p>
								<a
									href="/employees"
									class="inline-flex items-center gap-2 mt-4 py-2 px-4 bg-primary-500 text-white rounded-md no-underline text-body-content font-medium transition-colors hover:bg-primary-600"
								>
									<i class="fas fa-arrow-right"></i>
									Go to Employees
								</a>
							</div>
						{:else}
							<!-- Select All -->
							<div class="p-3 border-b border-surface-100 bg-surface-50">
								<label class="flex items-center gap-2 cursor-pointer">
									<input
										type="checkbox"
										class="w-4 h-4 accent-primary-500"
										checked={selectedIds.size === unassignedEmployees.length}
										onchange={toggleSelectAll}
									/>
									<span class="text-body-content text-surface-700">Select All</span>
								</label>
							</div>

							<!-- Employee List -->
							<div class="max-h-[250px] overflow-y-auto">
								{#each unassignedEmployees as employee (employee.id)}
									<label class="flex items-center gap-3 p-3 cursor-pointer hover:bg-surface-50 transition-colors border-b border-surface-100 last:border-b-0">
										<input
											type="checkbox"
											class="w-4 h-4 accent-primary-500"
											checked={selectedIds.has(employee.id)}
											onchange={() => toggleSelect(employee.id)}
										/>
										<div class="flex flex-col gap-0.5 min-w-0 flex-1">
											<span class="font-medium text-surface-800 truncate">
												{employee.firstName} {employee.lastName}
											</span>
											<span class="text-auxiliary-text text-surface-500 truncate">
												{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
											</span>
										</div>
									</label>
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if !isLoading && showAddSection && unassignedEmployees.length > 0}
			<div class="flex justify-end gap-3">
				<button
					type="button"
					class="py-2 px-4 bg-transparent text-surface-600 border border-surface-200 rounded-md text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-100"
					onclick={() => {
						showAddSection = false;
						selectedIds = new Set();
					}}
				>
					Cancel
				</button>
				<button
					type="button"
					class="inline-flex items-center gap-2 py-2 px-4 bg-primary-500 text-white border-none rounded-md text-body-content font-medium cursor-pointer transition-colors hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={handleAssign}
					disabled={selectedIds.size === 0 || isAssigning}
				>
					{#if isAssigning}
						<i class="fas fa-spinner fa-spin"></i>
						Adding...
					{:else}
						<i class="fas fa-plus"></i>
						Add Selected ({selectedIds.size})
					{/if}
				</button>
			</div>
		{/if}
	{/snippet}
</SlideOverPanel>
