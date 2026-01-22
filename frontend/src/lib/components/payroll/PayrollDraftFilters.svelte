<script lang="ts">
	import type { PayrollDraftFilters } from '$lib/types/payroll';
	import { DEFAULT_PAYROLL_DRAFT_FILTERS } from '$lib/types/payroll';

	interface Props {
		filters: PayrollDraftFilters;
		payGroups: Array<{ payGroupId: string; payGroupName: string }>;
		stats: { total: number; filtered: number };
		onFiltersChange: (filters: PayrollDraftFilters) => void;
	}

	let { filters, payGroups, stats, onFiltersChange }: Props = $props();

	function updateFilter<K extends keyof PayrollDraftFilters>(
		key: K,
		value: PayrollDraftFilters[K]
	) {
		onFiltersChange({ ...filters, [key]: value });
	}

	function clearFilters() {
		// Use the centralized default values to ensure consistency
		onFiltersChange({ ...DEFAULT_PAYROLL_DRAFT_FILTERS });
	}

	// Derived: check if any filters are active
	const hasActiveFilters = $derived(
		filters.searchQuery !== '' ||
			filters.payGroupId !== 'all' ||
			filters.showNoHoursEntered ||
			filters.showZeroEarnings ||
			filters.showNeedsHolidayPay
	);
</script>

<div class="payroll-draft-filters">
	<!-- Row 1: Search + Pay Group Dropdown -->
	<div class="filter-row-primary">
		<div class="search-box">
			<i class="fas fa-search search-icon"></i>
			<input
				type="text"
				class="search-input"
				placeholder="Search employees..."
				value={filters.searchQuery}
				oninput={(e) => updateFilter('searchQuery', e.currentTarget.value)}
			/>
		</div>

		<select
			class="filter-select"
			value={filters.payGroupId}
			onchange={(e) => updateFilter('payGroupId', e.currentTarget.value)}
		>
			<option value="all">All Pay Groups</option>
			{#each payGroups as pg}
				<option value={pg.payGroupId}>{pg.payGroupName}</option>
			{/each}
		</select>
	</div>

	<!-- Row 2: Quick Filters + Stats + Clear -->
	<div class="filter-row-secondary">
		<div class="quick-filters">
			<label class="checkbox-filter">
				<input
					type="checkbox"
					class="checkbox-input"
					checked={filters.showNoHoursEntered}
					onchange={(e) => updateFilter('showNoHoursEntered', e.currentTarget.checked)}
				/>
				<span class="checkbox-label">No Hours Entered</span>
			</label>

			<label class="checkbox-filter">
				<input
					type="checkbox"
					class="checkbox-input"
					checked={filters.showZeroEarnings}
					onchange={(e) => updateFilter('showZeroEarnings', e.currentTarget.checked)}
				/>
				<span class="checkbox-label">Zero Earnings</span>
			</label>

			<label class="checkbox-filter">
				<input
					type="checkbox"
					class="checkbox-input"
					checked={filters.showNeedsHolidayPay}
					onchange={(e) => updateFilter('showNeedsHolidayPay', e.currentTarget.checked)}
				/>
				<span class="checkbox-label">Needs Holiday Pay</span>
			</label>
		</div>

		<div class="filter-stats">
			<span class="stats-text">
				Showing <strong class="stats-highlight">{stats.filtered}</strong> of
				<strong class="stats-highlight">{stats.total}</strong> employees
			</span>
			{#if hasActiveFilters}
				<button class="clear-btn" onclick={clearFilters}>
					<i class="fas fa-times"></i>
					Clear Filters
				</button>
			{/if}
		</div>
	</div>
</div>

<style>
	.payroll-draft-filters {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		margin-bottom: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
		border: 1px solid var(--color-surface-200);
	}

	/* Primary row: Search + Dropdowns */
	.filter-row-primary {
		display: flex;
		gap: var(--spacing-3);
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: var(--spacing-3);
	}

	/* Search box */
	.search-box {
		position: relative;
		flex: 1;
		min-width: 200px;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		top: 50%;
		transform: translateY(-50%);
		color: var(--color-surface-500);
		font-size: 14px;
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		padding: 10px 12px 10px 36px;
		font-size: var(--font-size-body-content);
		line-height: var(--line-height-body-content);
		color: var(--color-surface-800);
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
		font-family: var(--font-family-primary);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-50);
	}

	.search-input::placeholder {
		color: var(--color-surface-500);
	}

	/* Filter dropdowns */
	.filter-select {
		padding: 10px 32px 10px 12px;
		font-size: var(--font-size-body-content);
		line-height: var(--line-height-body-content);
		color: var(--color-surface-800);
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
		font-family: var(--font-family-primary);
		cursor: pointer;
		min-width: 180px;
		appearance: none;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236d6d6e' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 10px center;
	}

	.filter-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-50);
	}

	/* Secondary row: Quick filters + stats */
	.filter-row-secondary {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--spacing-4);
		flex-wrap: wrap;
	}

	/* Quick filter checkboxes */
	.quick-filters {
		display: flex;
		gap: var(--spacing-4);
		flex-wrap: wrap;
	}

	.checkbox-filter {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
		user-select: none;
	}

	.checkbox-input {
		width: 16px;
		height: 16px;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		cursor: pointer;
		accent-color: var(--color-primary-500);
	}

	.checkbox-label {
		font-size: var(--font-size-body-content);
		line-height: var(--line-height-body-content);
		color: var(--color-surface-700);
		user-select: none;
	}

	.checkbox-filter:hover .checkbox-label {
		color: var(--color-surface-800);
	}

	/* Filter stats */
	.filter-stats {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.stats-text {
		font-size: var(--font-size-body-content);
		line-height: var(--line-height-body-content);
		color: var(--color-surface-600);
	}

	.stats-highlight {
		color: var(--color-surface-800);
		font-weight: var(--font-weight-semibold);
	}

	/* Clear button */
	.clear-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: 6px 12px;
		font-size: var(--font-size-body-content);
		line-height: var(--line-height-body-content);
		color: var(--color-primary-600);
		background: var(--color-primary-50);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-md);
		cursor: pointer;
		font-family: var(--font-family-primary);
		font-weight: var(--font-weight-medium);
		transition: var(--transition-fast);
	}

	.clear-btn:hover {
		background: var(--color-primary-100);
		border-color: var(--color-primary-300);
		color: var(--color-primary-700);
	}

	.clear-btn i {
		font-size: 12px;
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.filter-row-primary {
			flex-direction: column;
			align-items: stretch;
		}

		.search-box {
			min-width: unset;
		}

		.filter-select {
			min-width: unset;
		}

		.filter-row-secondary {
			flex-direction: column;
			align-items: stretch;
			gap: var(--spacing-3);
		}

		.quick-filters {
			flex-direction: column;
			gap: var(--spacing-2);
		}

		.filter-stats {
			justify-content: space-between;
		}
	}
</style>
