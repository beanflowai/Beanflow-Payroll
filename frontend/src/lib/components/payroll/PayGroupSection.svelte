<script lang="ts">
	import type { PayrollRunPayGroup, PayrollRecord, PayrollRunStatus } from '$lib/types/payroll';
	import { PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { PayrollRecordExpandedRow, LeaveTypeBadge } from '$lib/components/payroll';
	import { formatDateRange } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		payGroup: PayrollRunPayGroup;
		runStatus: PayrollRunStatus;
		payDate?: string;
		expandedRecordId: string | null;
		onToggleExpand: (id: string) => void;
		onPreviewPaystub?: (record: PayrollRecord) => void;
		onDownloadPaystub?: (record: PayrollRecord) => void;
		onResendPaystub?: (record: PayrollRecord) => void;
	}

	let {
		payGroup,
		runStatus,
		payDate,
		expandedRecordId,
		onToggleExpand,
		onPreviewPaystub,
		onDownloadPaystub,
		onResendPaystub
	}: Props = $props();

	let isCollapsed = $state(false);

	function toggleCollapse() {
		isCollapsed = !isCollapsed;
	}

	const isApprovedOrPaid = $derived(runStatus === 'approved' || runStatus === 'paid');
</script>

<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden mb-4">
	<!-- Section Header -->
	<button
		class="w-full flex items-center justify-between px-5 py-4 bg-surface-50 border-none cursor-pointer transition-all duration-150 text-left hover:bg-surface-100 max-md:flex-col max-md:items-start max-md:gap-3"
		onclick={toggleCollapse}
	>
		<div class="flex items-center gap-3">
			<i class="fas fa-chevron-{isCollapsed ? 'right' : 'down'} text-xs text-surface-500 w-4"></i>
			<div
				class="w-9 h-9 rounded-md bg-primary-100 text-primary-600 flex items-center justify-center text-sm"
			>
				<i class="fas fa-tag"></i>
			</div>
			<div class="flex flex-col gap-1">
				<h3 class="text-body-content font-semibold text-surface-800 m-0">
					{payGroup.payGroupName}
				</h3>
				<div class="flex items-center gap-2">
					<span class="text-auxiliary-text text-surface-600">
						{PAY_FREQUENCY_LABELS[payGroup.payFrequency] || payGroup.payFrequency}
					</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span class="text-auxiliary-text text-surface-600">
						{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType] || payGroup.employmentType}
					</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span class="text-auxiliary-text text-surface-600">
						{formatDateRange(payGroup.periodStart, payGroup.periodEnd)}
					</span>
				</div>
			</div>
		</div>
		<div class="flex items-center max-md:w-full">
			<div class="flex gap-6 max-lg:gap-4 max-md:w-full max-md:justify-between">
				<div class="flex flex-col items-end max-md:items-start">
					<span class="text-body-content font-semibold text-surface-800">
						{payGroup.totalEmployees}
					</span>
					<span class="text-auxiliary-text text-surface-500">Employees</span>
				</div>
				<div class="flex flex-col items-end max-md:items-start">
					<span class="text-body-content font-semibold text-surface-800">
						{formatCurrency(payGroup.totalGross)}
					</span>
					<span class="text-auxiliary-text text-surface-500">Gross</span>
				</div>
				<div class="flex flex-col items-end max-md:items-start">
					<span class="text-body-content font-semibold text-surface-800">
						{formatCurrency(payGroup.totalNetPay)}
					</span>
					<span class="text-auxiliary-text text-surface-500">Net Pay</span>
				</div>
			</div>
		</div>
	</button>

	<!-- Section Content -->
	{#if !isCollapsed}
		<div class="border-t border-surface-200">
			<table class="w-full border-collapse">
				<thead>
					<tr>
						<th
							class="w-[22%] text-left px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Employee
						</th>
						<th
							class="w-[8%] text-left px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Province
						</th>
						<th
							class="w-[13%] text-right px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Gross
						</th>
						<th
							class="w-[10%] text-left px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Leave
						</th>
						<th
							class="w-[10%] text-left px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Overtime
						</th>
						<th
							class="w-[13%] text-right px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Deductions
						</th>
						<th
							class="w-[13%] text-right px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Net Pay
						</th>
						<th
							class="w-[12%] text-right px-4 py-3 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide bg-surface-50 border-b border-surface-200"
						>
							Actions
						</th>
					</tr>
				</thead>
				<tbody>
					{#each payGroup.records as record, index (record.id)}
						<tr
							class="cursor-pointer transition-all duration-150 group
								{expandedRecordId === record.id ? '[&>td]:bg-primary-50' : 'hover:[&>td]:bg-surface-50'}"
							onclick={() => onToggleExpand(record.id)}
						>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								<span class="font-medium text-surface-800">{record.employeeName}</span>
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								<span
									class="inline-flex px-2 py-1 bg-surface-100 rounded-sm text-auxiliary-text font-medium text-surface-700"
								>
									{record.employeeProvince}
								</span>
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100 text-right
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								{formatCurrency(record.totalGross)}
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								{#if record.leaveEntries && record.leaveEntries.length > 0}
									<div class="flex gap-1 flex-wrap">
										{#each record.leaveEntries as entry (entry.leaveType)}
											<LeaveTypeBadge type={entry.leaveType} hours={entry.hours} compact />
										{/each}
									</div>
								{:else}
									<span class="text-surface-400">-</span>
								{/if}
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								{#if record.overtimeEntries && record.overtimeEntries.length > 0}
									{@const totalHours = record.overtimeEntries.reduce((sum, e) => sum + e.hours, 0)}
									<span
										class="inline-flex items-center gap-1 px-2 py-1 bg-success-100 text-success-700 rounded-sm text-auxiliary-text font-medium"
									>
										<i class="fas fa-clock text-[10px]"></i>
										{totalHours}h
									</span>
								{:else}
									<span class="text-surface-400">-</span>
								{/if}
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100 text-right
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								{formatCurrency(record.totalDeductions)}
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100 text-right
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								<span class="font-semibold text-surface-800">{formatCurrency(record.netPay)}</span>
							</td>
							<td
								class="px-4 py-3 text-body-content text-surface-700 border-b border-surface-100 text-right
									{index === payGroup.records.length - 1 && expandedRecordId !== record.id ? 'border-b-0' : ''}"
							>
								<div class="flex gap-2 justify-end">
									<!-- Preview button - always visible -->
									<button
										class="p-2 bg-transparent border-none rounded-md text-surface-500 cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:text-primary-600"
										title="Preview Paystub"
										onclick={(e) => {
											e.stopPropagation();
											onPreviewPaystub?.(record);
										}}
									>
										<i class="fas fa-eye"></i>
									</button>
									{#if isApprovedOrPaid}
										<button
											class="p-2 bg-transparent border-none rounded-md text-surface-500 cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:text-primary-600"
											title="Download Paystub"
											onclick={(e) => {
												e.stopPropagation();
												onDownloadPaystub?.(record);
											}}
										>
											<i class="fas fa-download"></i>
										</button>
										<button
											class="p-2 bg-transparent border-none rounded-md text-surface-500 cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:text-primary-600"
											title="Resend Paystub"
											onclick={(e) => {
												e.stopPropagation();
												onResendPaystub?.(record);
											}}
										>
											<i class="fas fa-paper-plane"></i>
										</button>
									{/if}
									<button
										class="p-2 bg-transparent border-none rounded-md text-surface-500 cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:text-primary-600"
										title={expandedRecordId === record.id ? 'Collapse' : 'Expand'}
									>
										<i class="fas fa-chevron-{expandedRecordId === record.id ? 'up' : 'down'}"></i>
									</button>
								</div>
							</td>
						</tr>
						{#if expandedRecordId === record.id}
							<PayrollRecordExpandedRow {record} groupBenefits={payGroup.groupBenefits} />
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
