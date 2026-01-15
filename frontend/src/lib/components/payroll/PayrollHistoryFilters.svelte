<script lang="ts">
	import type { PayGroup } from '$lib/types/pay-group';
	import type { Employee } from '$lib/types/employee';
	import type { DateRange, DateRangePeriod } from '$lib/utils/dateUtils';
	import { getDateRange, formatDateRange } from '$lib/utils/dateUtils';
	import type { PayrollHistoryFilters } from '$lib/types/payroll-filters';

	interface Props {
		filters: PayrollHistoryFilters;
		payGroups: PayGroup[];
		employees: Employee[];
		onFiltersChange: (filters: PayrollHistoryFilters) => void;
	}

	let { filters, payGroups = [], employees = [], onFiltersChange }: Props = $props();

	// Date range period options
	const dateRangeOptions: { key: DateRangePeriod | 'all' | 'custom'; label: string }[] = [
		{ key: 'all', label: 'All Time' },
		{ key: 'thisMonth', label: 'This Month' },
		{ key: 'lastMonth', label: 'Last Month' },
		{ key: 'last30Days', label: 'Last 30 Days' },
		{ key: 'last90Days', label: 'Last 90 Days' },
		{ key: 'thisYear', label: 'This Year' },
		{ key: 'custom', label: 'Custom Range...' }
	];

	// Local state for custom date range UI
	let isCustomDate = $state(false);
	let customFrom = $state(filters.dateRange?.from || '');
	let customTo = $state(filters.dateRange?.to || '');

	// Sync isCustomDate with incoming filters
	$effect(() => {
		if (filters.dateRange) {
			const isPredefined = dateRangeOptions.some(
				(opt) =>
					opt.key !== 'all' &&
					opt.key !== 'custom' &&
					JSON.stringify(getDateRange(opt.key as DateRangePeriod)) ===
						JSON.stringify(filters.dateRange)
			);
			if (!isPredefined && filters.dateRange.from && filters.dateRange.to) {
				isCustomDate = true;
				customFrom = filters.dateRange.from;
				customTo = filters.dateRange.to;
			}
		} else {
			isCustomDate = false;
		}
	});

	// 过滤后的员工列表（根据选中的 Pay Group）- 两级联选核心
	const filteredEmployees = $derived(
		filters.payGroupId === 'all'
			? employees
			: employees.filter((e) => e.payGroupId === filters.payGroupId)
	);

	// Employee 下拉框显示标签
	const employeeFilterLabel = $derived(
		filters.employeeId === 'all'
			? filters.payGroupId === 'all'
				? 'All Employees'
				: `All in ${payGroups.find((pg) => pg.id === filters.payGroupId)?.name || 'Group'}`
			: (() => {
					const employee = filteredEmployees.find((e) => e.id === filters.employeeId);
					return employee
						? `${employee.firstName} ${employee.lastName}`.trim() || 'Select Employee'
						: 'Select Employee';
				})()
	);

	// Active filter count
	const activeFilterCount = $derived(
		(filters.payGroupId !== 'all' ? 1 : 0) +
			(filters.employeeId !== 'all' ? 1 : 0) +
			(filters.dateRange ? 1 : 0)
	);

	function updateFilter<K extends keyof PayrollHistoryFilters>(
		key: K,
		value: PayrollHistoryFilters[K]
	) {
		onFiltersChange({ ...filters, [key]: value });
	}

	function handlePayGroupChange(groupId: string) {
		// 切换 Pay Group 时重置 Employee - 两级联选关键逻辑
		onFiltersChange({
			...filters,
			payGroupId: groupId,
			employeeId: 'all'
		});
	}

	function handleEmployeeChange(employeeId: string) {
		// 如果选了具体员工，自动设置其所属的 Pay Group（智能联动）
		if (employeeId !== 'all') {
			const employee = employees.find((e) => e.id === employeeId);
			if (employee && employee.payGroupId && employee.payGroupId !== filters.payGroupId) {
				// 员工不在当前选中的 group，自动切换过去
				onFiltersChange({
					...filters,
					payGroupId: employee.payGroupId,
					employeeId
				});
				return;
			}
		}
		onFiltersChange({ ...filters, employeeId: employeeId });
	}

	function clearFilters() {
		isCustomDate = false;
		customFrom = '';
		customTo = '';
		onFiltersChange({
			status: filters.status, // Keep status, it's managed by tabs
			payGroupId: 'all',
			employeeId: 'all',
			dateRange: undefined
		});
	}

	function handleDateRangeChange(period: DateRangePeriod | 'all' | 'custom') {
		if (period === 'all') {
			isCustomDate = false;
			updateFilter('dateRange', undefined);
		} else if (period === 'custom') {
			isCustomDate = true;
			// Don't update filter yet, wait for dates to be picked
		} else {
			isCustomDate = false;
			updateFilter('dateRange', getDateRange(period));
		}
	}

	function applyCustomDate() {
		if (customFrom && customTo) {
			updateFilter('dateRange', { from: customFrom, to: customTo });
		}
	}
</script>

<div class="bg-white p-4 rounded-xl border border-surface-200 shadow-sm mb-6">
	<div class="flex items-end gap-4 flex-wrap">
		<!-- Pay Group Filter -->
		{#if payGroups.length > 0}
			<div class="flex-1 min-w-[200px]">
				<label for="pay-group-filter" class="flex items-center gap-2 text-sm font-medium text-surface-700 mb-1.5">
					<i class="fas fa-users text-surface-400"></i>
					Pay Group
				</label>
				<div class="relative">
					<select
						id="pay-group-filter"
						class="w-full h-10 pl-3 pr-10 border border-surface-200 rounded-lg text-body-content bg-white appearance-none cursor-pointer hover:border-primary-400 transition-colors focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
						value={filters.payGroupId}
						onchange={(e) => handlePayGroupChange(e.currentTarget.value)}
					>
						<option value="all">All Pay Groups</option>
						{#each payGroups as pg (pg.id)}
							<option value={pg.id}>{pg.name}</option>
						{/each}
					</select>
					<div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-surface-400">
						<i class="fas fa-chevron-down text-xs"></i>
					</div>
				</div>
			</div>
		{/if}

		<!-- Employee Filter -->
		{#if employees.length > 0}
			<div class="flex-1 min-w-[220px]">
				<label for="employee-filter" class="flex items-center gap-2 text-sm font-medium text-surface-700 mb-1.5">
					<i class="fas fa-user text-surface-400"></i>
					Employee
				</label>
				<div class="relative">
					<select
						id="employee-filter"
						class="w-full h-10 pl-3 pr-10 border border-surface-200 rounded-lg text-body-content bg-white appearance-none cursor-pointer hover:border-primary-400 transition-colors focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
						value={filters.employeeId}
						onchange={(e) => handleEmployeeChange(e.currentTarget.value)}
					>
						<option value="all">{employeeFilterLabel}</option>
						{#each filteredEmployees as employee (employee.id)}
							<option value={employee.id}>{employee.firstName} {employee.lastName}</option>
						{/each}
					</select>
					<div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-surface-400">
						<i class="fas fa-chevron-down text-xs"></i>
					</div>
				</div>
			</div>
		{/if}

		<!-- Date Range Selector -->
		<div class="flex-1 min-w-[200px]">
			<label for="date-range-filter" class="flex items-center gap-2 text-sm font-medium text-surface-700 mb-1.5">
				<i class="fas fa-calendar-alt text-surface-400"></i>
				Date Range
			</label>
			<div class="relative">
				<select
					id="date-range-filter"
					class="w-full h-10 pl-3 pr-10 border border-surface-200 rounded-lg text-body-content bg-white appearance-none cursor-pointer hover:border-primary-400 transition-colors focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
					value={isCustomDate ? 'custom' : (filters.dateRange ? dateRangeOptions.find(opt => opt.key !== 'all' && opt.key !== 'custom' && JSON.stringify(getDateRange(opt.key as DateRangePeriod)) === JSON.stringify(filters.dateRange))?.key || 'all' : 'all')}
					onchange={(e) => {
						const selectedKey = e.currentTarget.value as DateRangePeriod | 'all' | 'custom';
						handleDateRangeChange(selectedKey);
					}}
				>
					{#each dateRangeOptions as option}
						<option value={option.key}>{option.label}</option>
					{/each}
				</select>
				<div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-surface-400">
					<i class="fas fa-chevron-down text-xs"></i>
				</div>
			</div>
		</div>

		<!-- Custom Date Inputs -->
		{#if isCustomDate}
			<div class="flex items-end gap-2 animate-in fade-in slide-in-from-left-2 duration-200">
				<div class="flex flex-col">
					<label for="custom-from" class="text-[11px] font-semibold text-surface-500 uppercase tracking-wider mb-1 px-1">From</label>
					<input
						id="custom-from"
						type="date"
						bind:value={customFrom}
						onchange={applyCustomDate}
						class="h-10 px-3 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
					/>
				</div>
				<div class="flex flex-col">
					<label for="custom-to" class="text-[11px] font-semibold text-surface-500 uppercase tracking-wider mb-1 px-1">To</label>
					<input
						id="custom-to"
						type="date"
						bind:value={customTo}
						onchange={applyCustomDate}
						class="h-10 px-3 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
					/>
				</div>
			</div>
		{/if}

		<!-- Actions -->
		<div class="flex items-center gap-2 ml-auto">
			{#if activeFilterCount > 0}
				<button
					class="h-10 px-3.5 text-sm font-medium text-surface-600 bg-white border border-surface-200 rounded-lg cursor-pointer hover:border-surface-300 hover:bg-surface-50 transition-colors duration-200 flex items-center gap-2 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
					onclick={clearFilters}
				>
					<i class="fas fa-times text-surface-400"></i>
					Clear Filters
				</button>
			{/if}
		</div>
	</div>
</div>

<style>
	input[type="date"]::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0.6;
		transition: opacity 0.2s;
	}
	input[type="date"]::-webkit-calendar-picker-indicator:hover {
		opacity: 1;
	}
</style>
