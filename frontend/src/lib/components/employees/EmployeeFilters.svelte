<script lang="ts">
	import type {
		EmployeeFilters,
		EmployeeStatusCounts,
		Province,
		PayFrequency,
		EmploymentType,
		CompensationType,
		EmployeeStatus
	} from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		DEFAULT_EMPLOYEE_FILTERS
	} from '$lib/types/employee';
	import type { PayGroup } from '$lib/types/pay-group';

	interface Props {
		filters: EmployeeFilters;
		statusCounts: EmployeeStatusCounts;
		payGroups?: PayGroup[];  // Available pay groups for filtering
		onFiltersChange: (filters: EmployeeFilters) => void;
	}

	let { filters, statusCounts, payGroups = [], onFiltersChange }: Props = $props();

	// Province options
	const provinces: Province[] = ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'SK', 'YT'];

	// Pay frequency options
	const payFrequencies: PayFrequency[] = ['weekly', 'bi_weekly', 'semi_monthly', 'monthly'];

	// Employment type options
	const employmentTypes: EmploymentType[] = ['full_time', 'part_time'];

	// Compensation type options
	const compensationTypes: { value: CompensationType | 'all'; label: string }[] = [
		{ value: 'all', label: 'All' },
		{ value: 'salaried', label: 'Salaried' },
		{ value: 'hourly', label: 'Hourly' }
	];

	// Count active filters (excluding status and search)
	const activeFilterCount = $derived(() => {
		let count = 0;
		if (filters.province !== 'all') count++;
		if (filters.payFrequency !== 'all') count++;
		if (filters.employmentType !== 'all') count++;
		if (filters.compensationType !== 'all') count++;
		if (filters.payGroupId !== 'all') count++;
		return count;
	});

	// Update individual filter
	function updateFilter<K extends keyof EmployeeFilters>(key: K, value: EmployeeFilters[K]) {
		onFiltersChange({ ...filters, [key]: value });
	}

	// Clear all filters (except search)
	function clearFilters() {
		onFiltersChange({
			...DEFAULT_EMPLOYEE_FILTERS,
			searchQuery: filters.searchQuery
		});
	}

	// Status options for tabs
	const statusOptions: { value: EmployeeStatus | 'all'; label: string; countKey: keyof EmployeeStatusCounts }[] = [
		{ value: 'all', label: 'All', countKey: 'total' },
		{ value: 'draft', label: 'Draft', countKey: 'draft' },
		{ value: 'active', label: 'Active', countKey: 'active' },
		{ value: 'terminated', label: 'Terminated', countKey: 'terminated' }
	];
</script>

<div class="employee-filters">
	<!-- Row 1: Status Tabs + Search -->
	<div class="filter-row-1">
		<div class="status-tabs">
			{#each statusOptions as option}
				<button
					class="status-tab"
					class:active={filters.status === option.value}
					onclick={() => updateFilter('status', option.value)}
				>
					{option.label} ({statusCounts[option.countKey]})
				</button>
			{/each}
		</div>
		<div class="search-box">
			<i class="fas fa-search"></i>
			<input
				type="text"
				placeholder="Search employees..."
				value={filters.searchQuery}
				oninput={(e) => updateFilter('searchQuery', e.currentTarget.value)}
			/>
		</div>
	</div>

	<!-- Row 2: Dropdown Filters -->
	<div class="filter-row-2">
		<div class="dropdown-filters">
			<!-- Province Filter -->
			<div class="filter-dropdown">
				<label for="province-filter">Province</label>
				<select
					id="province-filter"
					value={filters.province}
					onchange={(e) => updateFilter('province', e.currentTarget.value as Province | 'all')}
				>
					<option value="all">All Provinces</option>
					{#each provinces as province}
						<option value={province}>{PROVINCE_LABELS[province]}</option>
					{/each}
				</select>
			</div>

			<!-- Pay Frequency Filter -->
			<div class="filter-dropdown">
				<label for="pay-freq-filter">Pay Frequency</label>
				<select
					id="pay-freq-filter"
					value={filters.payFrequency}
					onchange={(e) => updateFilter('payFrequency', e.currentTarget.value as PayFrequency | 'all')}
				>
					<option value="all">All Frequencies</option>
					{#each payFrequencies as freq}
						<option value={freq}>{PAY_FREQUENCY_LABELS[freq]}</option>
					{/each}
				</select>
			</div>

			<!-- Employment Type Filter -->
			<div class="filter-dropdown">
				<label for="emp-type-filter">Type</label>
				<select
					id="emp-type-filter"
					value={filters.employmentType}
					onchange={(e) => updateFilter('employmentType', e.currentTarget.value as EmploymentType | 'all')}
				>
					<option value="all">All Types</option>
					{#each employmentTypes as empType}
						<option value={empType}>{EMPLOYMENT_TYPE_LABELS[empType]}</option>
					{/each}
				</select>
			</div>

			<!-- Compensation Type Filter -->
			<div class="filter-dropdown">
				<label for="comp-type-filter">Compensation</label>
				<select
					id="comp-type-filter"
					value={filters.compensationType}
					onchange={(e) => updateFilter('compensationType', e.currentTarget.value as CompensationType | 'all')}
				>
					{#each compensationTypes as compType}
						<option value={compType.value}>{compType.label}</option>
					{/each}
				</select>
			</div>

			<!-- Pay Group Filter -->
			{#if payGroups.length > 0}
				<div class="filter-dropdown">
					<label for="pay-group-filter">Pay Group</label>
					<select
						id="pay-group-filter"
						value={filters.payGroupId}
						onchange={(e) => updateFilter('payGroupId', e.currentTarget.value)}
					>
						<option value="all">All Pay Groups</option>
						<option value="unassigned">Unassigned</option>
						{#each payGroups as pg}
							<option value={pg.id}>{pg.name}</option>
						{/each}
					</select>
				</div>
			{/if}
		</div>

		<!-- Clear Filters Button -->
		{#if activeFilterCount() > 0}
			<button class="clear-filters-btn" onclick={clearFilters}>
				<i class="fas fa-times"></i>
				Clear {activeFilterCount()} filter{activeFilterCount() > 1 ? 's' : ''}
			</button>
		{/if}
	</div>
</div>

<style>
	.employee-filters {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-4);
	}

	/* Row 1: Status Tabs + Search */
	.filter-row-1 {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-4);
		flex-wrap: wrap;
	}

	.status-tabs {
		display: flex;
		gap: var(--spacing-1);
		background: var(--color-surface-100);
		padding: var(--spacing-1);
		border-radius: var(--radius-lg);
	}

	.status-tab {
		padding: var(--spacing-2) var(--spacing-4);
		border: none;
		background: transparent;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
		white-space: nowrap;
	}

	.status-tab:hover {
		color: var(--color-surface-800);
	}

	.status-tab.active {
		background: white;
		color: var(--color-surface-800);
		box-shadow: var(--shadow-md3-1);
	}

	.search-box {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		min-width: 250px;
	}

	.search-box i {
		color: var(--color-surface-400);
	}

	.search-box input {
		flex: 1;
		border: none;
		outline: none;
		font-size: var(--font-size-body-content);
		background: transparent;
	}

	/* Row 2: Dropdown Filters */
	.filter-row-2 {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: var(--spacing-4);
		flex-wrap: wrap;
	}

	.dropdown-filters {
		display: flex;
		gap: var(--spacing-4);
		flex-wrap: wrap;
	}

	.filter-dropdown {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.filter-dropdown label {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		font-weight: var(--font-weight-medium);
	}

	.filter-dropdown select {
		padding: var(--spacing-2) var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		background: white;
		cursor: pointer;
		min-width: 140px;
		transition: var(--transition-fast);
	}

	.filter-dropdown select:hover {
		border-color: var(--color-surface-300);
	}

	.filter-dropdown select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.clear-filters-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		border: none;
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
		white-space: nowrap;
	}

	.clear-filters-btn:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-800);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.filter-row-1 {
			flex-direction: column;
			align-items: stretch;
		}

		.status-tabs {
			width: 100%;
			overflow-x: auto;
		}

		.search-box {
			min-width: 100%;
		}

		.filter-row-2 {
			flex-direction: column;
			align-items: stretch;
		}

		.dropdown-filters {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
			gap: var(--spacing-3);
		}

		.filter-dropdown select {
			min-width: 100%;
		}

		.clear-filters-btn {
			align-self: flex-start;
		}
	}
</style>
