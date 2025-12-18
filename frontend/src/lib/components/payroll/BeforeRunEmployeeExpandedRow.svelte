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

<div class="expanded-content">
	<!-- Three Column Layout -->
	<div class="expanded-columns">
		<!-- Earnings Column -->
		<div class="expanded-col earnings-col">
			<h4 class="col-title">Earnings <span class="edit-hint">(double-click to edit)</span></h4>
			<div class="earnings-list">
				{#each earningsBreakdown as item (item.key)}
					<div class="earnings-item" class:editable-row={item.editable}>
						<span class="item-label">{item.label}</span>
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
							<div class="hours-edit-wrapper">
								<InlineEditField
									value={item.editValue ?? 0}
									formatValue={(h) => `${h}h`}
									onSave={(newValue) => onEarningsEdit(item.key, newValue)}
									step={0.5}
									suffix="h"
								/>
								{#if item.amount > 0}
									<span class="hours-result">= {formatCurrency(item.amount)}</span>
								{/if}
							</div>
						{:else}
							<!-- Non-editable display -->
							<span class="item-amount" class:negative={item.amount < 0}>
								{item.amount !== 0 ? formatCurrency(Math.abs(item.amount)) : '--'}
							</span>
						{/if}
					</div>
					{#if item.detail && !item.editable}
						<div class="item-detail">{item.detail}</div>
					{/if}
				{/each}
				{#if earningsBreakdown.length === 0}
					<div class="empty-section">No earnings data</div>
				{/if}
			</div>
			<div class="col-total">
				<span>Est. Gross</span>
				<span class="total-amount">
					{estimatedGross !== null ? formatCurrency(estimatedGross) : '--'}
				</span>
			</div>
		</div>

		<!-- Deductions Column (Placeholder) -->
		<div class="expanded-col deductions-col">
			<h4 class="col-title">Deductions</h4>
			<div class="deductions-list placeholder-section">
				<div class="deduction-item">
					<span class="item-label">CPP</span>
					<span class="item-amount placeholder">--</span>
				</div>
				<div class="deduction-item">
					<span class="item-label">EI</span>
					<span class="item-amount placeholder">--</span>
				</div>
				<div class="deduction-item">
					<span class="item-label">Federal Tax</span>
					<span class="item-amount placeholder">--</span>
				</div>
				<div class="deduction-item">
					<span class="item-label">Provincial Tax</span>
					<span class="item-amount placeholder">--</span>
				</div>
			</div>
			<div class="col-total">
				<span>Total Deductions</span>
				<span class="total-amount placeholder">--</span>
			</div>
		</div>

		<!-- Leave Column -->
		<div class="expanded-col leave-col">
			<h4 class="col-title">Leave</h4>
			<div class="leave-inputs">
				<!-- Vacation Block -->
				<div class="leave-type-block">
					<div class="leave-type-header">
						<span class="leave-icon">🏖️</span>
						<span class="leave-type-name">Vacation</span>
					</div>
					<div class="leave-field">
						<span class="field-label">Hours:</span>
						<input
							type="number"
							class="leave-hours-input"
							min="0"
							max="200"
							step="0.5"
							value={getLeaveHours('vacation')}
							onchange={(e) => handleLeaveInputChange('vacation', (e.target as HTMLInputElement).value)}
							placeholder="0"
						/>
					</div>
					<div class="leave-field balance">
						<span class="field-label">Balance:</span>
						<span class="balance-value">-- h</span>
					</div>
				</div>
				<!-- Sick Block -->
				<div class="leave-type-block">
					<div class="leave-type-header">
						<span class="leave-icon">🏥</span>
						<span class="leave-type-name">Sick</span>
					</div>
					<div class="leave-field">
						<span class="field-label">Hours:</span>
						<input
							type="number"
							class="leave-hours-input"
							min="0"
							max="200"
							step="0.5"
							value={getLeaveHours('sick')}
							onchange={(e) => handleLeaveInputChange('sick', (e.target as HTMLInputElement).value)}
							placeholder="0"
						/>
					</div>
					<div class="leave-field balance">
						<span class="field-label">Balance:</span>
						<span class="balance-value">-- h</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- One-time Adjustments Section -->
	<div class="adjustments-section">
		<div class="adjustments-header">
			<h4 class="section-title">One-time Adjustments</h4>
			<button class="btn-add-adjustment" onclick={onAddAdjustment}>
				<i class="fas fa-plus"></i>
				Add
			</button>
		</div>
		{#if input.adjustments.length === 0}
			<div class="no-adjustments">
				<span>No adjustments added</span>
			</div>
		{:else}
			<div class="adjustments-list">
				{#each input.adjustments as adj, idx (adj.id)}
					<div class="adjustment-row">
						<select
							class="adj-type-select"
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
							class="adj-desc-input"
							placeholder="Description"
							value={adj.description}
							onchange={(e) => {
								onUpdateAdjustment(idx, { description: (e.target as HTMLInputElement).value });
							}}
						/>
						<div class="adj-amount-wrapper">
							<span class="currency-prefix">$</span>
							<input
								type="number"
								class="adj-amount-input"
								min="0"
								step="0.01"
								value={adj.amount}
								onchange={(e) => {
									onUpdateAdjustment(idx, { amount: parseFloat((e.target as HTMLInputElement).value) || 0 });
								}}
							/>
						</div>
						<button
							class="btn-remove-adj"
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
	<div class="net-pay-preview">
		<span class="net-label">Est. Net Pay</span>
		<span class="net-value placeholder">--</span>
		<span class="net-hint">(Start Payroll Run to calculate CPP/EI/Tax)</span>
	</div>
</div>

<style>
	.expanded-content {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-top: 1px solid var(--color-surface-200);
	}

	.expanded-columns {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: var(--spacing-6);
		margin-bottom: var(--spacing-4);
	}

	.expanded-col {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-sm);
	}

	.col-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3);
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.edit-hint {
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-normal);
		color: var(--color-surface-400);
	}

	/* Earnings */
	.earnings-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.earnings-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2) 0;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.earnings-item:last-child {
		border-bottom: none;
	}

	.earnings-item.editable-row {
		background: var(--color-primary-50);
		margin: 0 calc(-1 * var(--spacing-2));
		padding: var(--spacing-2);
		border-radius: var(--radius-md);
		border-bottom: none;
	}

	.item-label {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
	}

	.item-amount {
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.item-amount.negative {
		color: var(--color-error-600);
	}

	.item-amount.placeholder {
		color: var(--color-surface-400);
	}

	.item-detail {
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
		padding-left: var(--spacing-2);
		margin-top: -4px;
		margin-bottom: var(--spacing-1);
	}

	.hours-edit-wrapper {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.hours-result {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	.col-total {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: var(--spacing-3);
		padding-top: var(--spacing-3);
		border-top: 2px solid var(--color-surface-200);
		font-weight: var(--font-weight-semibold);
	}

	.total-amount {
		font-size: var(--font-size-body-content);
		color: var(--color-primary-600);
	}

	.total-amount.placeholder {
		color: var(--color-surface-400);
	}

	.empty-section {
		text-align: center;
		padding: var(--spacing-4);
		color: var(--color-surface-400);
		font-size: var(--font-size-body-small);
	}

	/* Deductions */
	.deductions-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.deduction-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2) 0;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.deduction-item:last-child {
		border-bottom: none;
	}

	.placeholder-section .item-amount {
		color: var(--color-surface-400);
	}

	/* Leave */
	.leave-inputs {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.leave-type-block {
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-3);
	}

	.leave-type-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-2);
	}

	.leave-icon {
		font-size: 16px;
	}

	.leave-type-name {
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.leave-field {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-1);
	}

	.leave-field.balance {
		margin-bottom: 0;
	}

	.field-label {
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
		min-width: 50px;
	}

	.leave-hours-input {
		width: 70px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
		text-align: center;
	}

	.leave-hours-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.balance-value {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Adjustments */
	.adjustments-section {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-sm);
		margin-bottom: var(--spacing-4);
	}

	.adjustments-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-3);
	}

	.section-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0;
	}

	.btn-add-adjustment {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-primary-50);
		color: var(--color-primary-600);
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-adjustment:hover {
		background: var(--color-primary-100);
	}

	.no-adjustments {
		text-align: center;
		padding: var(--spacing-3);
		color: var(--color-surface-400);
		font-size: var(--font-size-body-small);
	}

	.adjustments-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.adjustment-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
	}

	.adj-type-select {
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
		background: white;
		min-width: 130px;
	}

	.adj-desc-input {
		flex: 1;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
	}

	.adj-amount-wrapper {
		display: flex;
		align-items: center;
		background: white;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.currency-prefix {
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-small);
	}

	.adj-amount-input {
		width: 80px;
		padding: var(--spacing-1) var(--spacing-2);
		border: none;
		font-size: var(--font-size-body-small);
		text-align: right;
	}

	.adj-amount-input:focus {
		outline: none;
	}

	.btn-remove-adj {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		background: none;
		border: none;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.btn-remove-adj:hover {
		background: var(--color-error-100);
		color: var(--color-error-600);
	}

	/* Net Pay Preview */
	.net-pay-preview {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
	}

	.net-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
	}

	.net-value {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-bold);
		color: var(--color-success-600);
	}

	.net-value.placeholder {
		color: var(--color-surface-400);
	}

	.net-hint {
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
		margin-left: auto;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.expanded-columns {
			grid-template-columns: 1fr 1fr;
		}

		.leave-col {
			grid-column: span 2;
		}
	}

	@media (max-width: 768px) {
		.expanded-columns {
			grid-template-columns: 1fr;
		}

		.leave-col {
			grid-column: span 1;
		}

		.adjustment-row {
			flex-wrap: wrap;
		}

		.adj-desc-input {
			min-width: 100%;
			order: 3;
		}
	}
</style>
