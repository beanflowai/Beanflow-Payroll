<script lang="ts">
	import type { EmployeePayrollInput, EarningsBreakdown, Adjustment } from '$lib/types/payroll';
	import { ADJUSTMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { InlineEditField } from '$lib/components/shared';

	interface Props {
		input: EmployeePayrollInput;
		earningsBreakdown: EarningsBreakdown[];
		estimatedGross: number | null;
		onEarningsEdit: (key: string, value: number) => void;
		onLeaveChange: (type: 'vacation' | 'sick', hours: number) => void;
		onAddAdjustment: () => void;
		onUpdateAdjustment: (idx: number, updates: Partial<Adjustment>) => void;
		onRemoveAdjustment: (idx: number) => void;
	}

	let {
		input,
		earningsBreakdown,
		estimatedGross,
		onEarningsEdit,
		onLeaveChange,
		onAddAdjustment,
		onUpdateAdjustment,
		onRemoveAdjustment
	}: Props = $props();

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function getLeaveHours(type: 'vacation' | 'sick'): number {
		return input.leaveEntries.find(l => l.type === type)?.hours ?? 0;
	}

	function handleLeaveInputChange(type: 'vacation' | 'sick', value: string) {
		const hours = parseFloat(value) || 0;
		onLeaveChange(type, hours);
	}
</script>

<div class="p-4 bg-surface-50 border-t border-surface-200">
	<!-- Three Column Layout -->
	<div class="grid grid-cols-3 gap-6 mb-4 max-lg:grid-cols-2 max-md:grid-cols-1">
		<!-- Earnings Column -->
		<div class="bg-white rounded-lg p-4 shadow-sm">
			<h4 class="text-body-content font-semibold text-surface-700 mb-3 flex items-center gap-2">
				Earnings <span class="text-caption font-normal text-surface-400">(double-click to edit)</span>
			</h4>
			<div class="flex flex-col gap-2">
				{#each earningsBreakdown as item (item.key)}
					<div class="flex justify-between items-center py-2 border-b border-surface-100 last:border-b-0" class:editable-row={item.editable}>
						<span class="text-body-small text-surface-600">{item.label}</span>
						{#if item.editable && item.editType === 'amount'}
							<!-- Editable amount (Regular Pay for salaried) -->
							<InlineEditField
								value={item.editValue ?? item.amount}
								formatValue={formatCurrency}
								onSave={(newValue) => onEarningsEdit(item.key, newValue)}
								step={0.01}
							/>
						{:else if item.editable && item.editType === 'hours'}
							<!-- Editable hours (Overtime) -->
							<div class="flex items-center gap-2">
								<InlineEditField
									value={item.editValue ?? 0}
									formatValue={(h) => `${h}h`}
									onSave={(newValue) => onEarningsEdit(item.key, newValue)}
									step={0.5}
									suffix="h"
								/>
								{#if item.amount > 0}
									<span class="text-body-small text-surface-500">= {formatCurrency(item.amount)}</span>
								{/if}
							</div>
						{:else}
							<!-- Non-editable display -->
							<span class="text-body-small font-medium" class:text-error-600={item.amount < 0} class:text-surface-800={item.amount >= 0} class:text-surface-400={item.amount === 0}>
								{item.amount !== 0 ? formatCurrency(Math.abs(item.amount)) : '--'}
							</span>
						{/if}
					</div>
					{#if item.detail && !item.editable}
						<div class="text-caption text-surface-500 pl-2 -mt-1 mb-1">{item.detail}</div>
					{/if}
				{/each}
				{#if earningsBreakdown.length === 0}
					<div class="text-center py-4 text-surface-400 text-body-small">No earnings data</div>
				{/if}
			</div>
			<div class="flex justify-between items-center mt-3 pt-3 border-t-2 border-surface-200 font-semibold">
				<span>Est. Gross</span>
				<span class="text-body-content" class:text-primary-600={estimatedGross !== null} class:text-surface-400={estimatedGross === null}>
					{estimatedGross !== null ? formatCurrency(estimatedGross) : '--'}
				</span>
			</div>
		</div>

		<!-- Deductions Column (Placeholder) -->
		<div class="bg-white rounded-lg p-4 shadow-sm">
			<h4 class="text-body-content font-semibold text-surface-700 mb-3">Deductions</h4>
			<div class="flex flex-col gap-2 opacity-60">
				<div class="flex justify-between items-center py-2 border-b border-surface-100">
					<span class="text-body-small text-surface-600">CPP</span>
					<span class="text-body-small font-medium text-surface-400">--</span>
				</div>
				<div class="flex justify-between items-center py-2 border-b border-surface-100">
					<span class="text-body-small text-surface-600">EI</span>
					<span class="text-body-small font-medium text-surface-400">--</span>
				</div>
				<div class="flex justify-between items-center py-2 border-b border-surface-100">
					<span class="text-body-small text-surface-600">Federal Tax</span>
					<span class="text-body-small font-medium text-surface-400">--</span>
				</div>
				<div class="flex justify-between items-center py-2 border-b border-surface-100 last:border-b-0">
					<span class="text-body-small text-surface-600">Provincial Tax</span>
					<span class="text-body-small font-medium text-surface-400">--</span>
				</div>
			</div>
			<div class="flex justify-between items-center mt-3 pt-3 border-t-2 border-surface-200 font-semibold">
				<span>Total Deductions</span>
				<span class="text-body-content text-surface-400">--</span>
			</div>
		</div>

		<!-- Leave Column -->
		<div class="bg-white rounded-lg p-4 shadow-sm max-lg:col-span-2 max-md:col-span-1">
			<h4 class="text-body-content font-semibold text-surface-700 mb-3">Leave</h4>
			<div class="flex flex-col gap-4">
				<!-- Vacation Block -->
				<div class="bg-surface-50 rounded-md p-3">
					<div class="flex items-center gap-2 mb-2">
						<span class="text-base">🏖️</span>
						<span class="text-body-small font-medium text-surface-700">Vacation</span>
					</div>
					<div class="flex items-center gap-2 mb-1">
						<span class="text-caption text-surface-500 min-w-[50px]">Hours:</span>
						<input
							type="number"
							class="w-[70px] py-1 px-2 border border-surface-300 rounded-md text-body-small text-center focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
							min="0"
							max="200"
							step="0.5"
							value={getLeaveHours('vacation')}
							onchange={(e) => handleLeaveInputChange('vacation', (e.target as HTMLInputElement).value)}
							placeholder="0"
						/>
					</div>
					<div class="flex items-center gap-2">
						<span class="text-caption text-surface-500 min-w-[50px]">Balance:</span>
						<span class="text-body-small text-surface-500">-- h</span>
					</div>
				</div>
				<!-- Sick Block -->
				<div class="bg-surface-50 rounded-md p-3">
					<div class="flex items-center gap-2 mb-2">
						<span class="text-base">🏥</span>
						<span class="text-body-small font-medium text-surface-700">Sick</span>
					</div>
					<div class="flex items-center gap-2 mb-1">
						<span class="text-caption text-surface-500 min-w-[50px]">Hours:</span>
						<input
							type="number"
							class="w-[70px] py-1 px-2 border border-surface-300 rounded-md text-body-small text-center focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
							min="0"
							max="200"
							step="0.5"
							value={getLeaveHours('sick')}
							onchange={(e) => handleLeaveInputChange('sick', (e.target as HTMLInputElement).value)}
							placeholder="0"
						/>
					</div>
					<div class="flex items-center gap-2">
						<span class="text-caption text-surface-500 min-w-[50px]">Balance:</span>
						<span class="text-body-small text-surface-500">-- h</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- One-time Adjustments Section -->
	<div class="bg-white rounded-lg p-4 shadow-sm mb-4">
		<div class="flex justify-between items-center mb-3">
			<h4 class="text-body-content font-semibold text-surface-700">One-time Adjustments</h4>
			<button
				class="flex items-center gap-1 py-1 px-2 bg-primary-50 text-primary-600 border-none rounded-md text-caption font-medium cursor-pointer transition-all duration-150 hover:bg-primary-100"
				onclick={onAddAdjustment}
			>
				<i class="fas fa-plus text-[10px]"></i>
				Add
			</button>
		</div>
		{#if input.adjustments.length === 0}
			<div class="text-center py-3 text-surface-400 text-body-small">
				<span>No adjustments added</span>
			</div>
		{:else}
			<div class="flex flex-col gap-2">
				{#each input.adjustments as adj, idx (adj.id)}
					<div class="flex items-center gap-2 p-2 bg-surface-50 rounded-md max-md:flex-wrap">
						<select
							class="py-1 px-2 border border-surface-300 rounded-md text-body-small bg-white min-w-[130px] max-md:min-w-full"
							value={adj.type}
							onchange={(e) => {
								const newType = (e.target as HTMLSelectElement).value as typeof adj.type;
								const newTaxable = ADJUSTMENT_TYPE_LABELS[newType].taxable;
								onUpdateAdjustment(idx, { type: newType, taxable: newTaxable });
							}}
						>
							<option value="bonus">Bonus</option>
							<option value="retroactive_pay">Retroactive Pay</option>
							<option value="taxable_benefit">Taxable Benefit</option>
							<option value="reimbursement">Reimbursement</option>
							<option value="deduction">Deduction</option>
						</select>
						<input
							type="text"
							class="flex-1 py-1 px-2 border border-surface-300 rounded-md text-body-small max-md:min-w-full max-md:order-3"
							placeholder="Description"
							value={adj.description}
							onchange={(e) => {
								onUpdateAdjustment(idx, { description: (e.target as HTMLInputElement).value });
							}}
						/>
						<div class="flex items-center bg-white border border-surface-300 rounded-md overflow-hidden">
							<span class="py-1 px-2 bg-surface-100 text-surface-500 text-body-small">$</span>
							<input
								type="number"
								class="w-[80px] py-1 px-2 border-none text-body-small text-right focus:outline-none"
								min="0"
								step="0.01"
								value={adj.amount}
								onchange={(e) => {
									onUpdateAdjustment(idx, { amount: parseFloat((e.target as HTMLInputElement).value) || 0 });
								}}
							/>
						</div>
						<button
							class="flex items-center justify-center w-7 h-7 bg-transparent border-none text-surface-400 cursor-pointer rounded-md transition-all duration-150 hover:bg-error-100 hover:text-error-600"
							onclick={() => onRemoveAdjustment(idx)}
							aria-label="Remove adjustment"
						>
							<i class="fas fa-times"></i>
						</button>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Net Pay Preview -->
	<div class="flex items-center gap-3 p-3 bg-surface-100 rounded-lg">
		<span class="text-body-content font-semibold text-surface-700">Est. Net Pay</span>
		<span class="text-title-small font-bold text-surface-400">--</span>
		<span class="text-caption text-surface-500 ml-auto">(Start Payroll Run to calculate CPP/EI/Tax)</span>
	</div>
</div>

<style>
	/* Only keep styles that can't be easily expressed in Tailwind */
	.editable-row {
		background: var(--color-primary-50);
		margin: 0 calc(-1 * var(--spacing-2));
		padding: var(--spacing-2);
		border-radius: var(--radius-md);
		border-bottom: none;
	}
</style>
