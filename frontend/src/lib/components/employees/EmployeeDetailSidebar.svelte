<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Employee } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		EMPLOYEE_STATUS_LABELS,
		formatVacationRate
	} from '$lib/types/employee';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		employee: Employee;
		showSIN: boolean;
		onToggleSIN: () => void;
		onClose: () => void;
	}

	let { employee, showSIN, onToggleSIN, onClose }: Props = $props();

	function handleEdit() {
		goto(`/employees/${employee.id}`);
	}

	// Pay periods per year based on frequency
	const PAY_PERIODS_MAP: Record<string, number> = {
		weekly: 52,
		bi_weekly: 26,
		semi_monthly: 24,
		monthly: 12
	};

	// Helpers
	function maskSIN(sin: string): string {
		const digits = sin.replace(/\D/g, '');
		return `***-***-${digits.slice(6)}`;
	}

	function formatCurrency(amount: number | null | undefined): string {
		if (amount == null) return '-';
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			maximumFractionDigits: 0
		}).format(amount);
	}

	function formatCompensation(emp: Employee): string {
		if (emp.hourlyRate) return `$${emp.hourlyRate.toFixed(2)}/hr`;
		if (emp.annualSalary) return `${formatCurrency(emp.annualSalary)}/yr`;
		return '-';
	}

	function formatDate(dateStr: string | null | undefined): string {
		if (!dateStr) return '-';
		return formatShortDate(dateStr);
	}

	function getPerPeriodAmount(emp: Employee): string {
		if (!emp.annualSalary) return '-';
		const periods = PAY_PERIODS_MAP[emp.payFrequency] || 26;
		return formatCurrency(emp.annualSalary / periods);
	}

</script>

<aside class="detail-sidebar">
	<div class="sidebar-header">
		<h2>Employee Details</h2>
		<button class="close-btn" onclick={onClose} aria-label="Close sidebar">
			<i class="fas fa-times"></i>
		</button>
	</div>

	<div class="sidebar-content">
		<!-- Basic Info -->
		<section class="detail-section">
			<h3 class="section-title">Basic Information</h3>
			<div class="detail-row">
				<span class="detail-label">Name</span>
				<span class="detail-value">{employee.firstName} {employee.lastName}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">SIN</span>
				<span class="detail-value">
					<button class="sin-toggle" onclick={onToggleSIN}>
						{showSIN ? employee.sin : maskSIN(employee.sin)}
						<i class="fas" class:fa-eye={!showSIN} class:fa-eye-slash={showSIN}></i>
					</button>
				</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Email</span>
				<span class="detail-value">{employee.email || '-'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Status</span>
				<span class="detail-value">
					<span class="status-badge" class:active={employee.status === 'active'} class:draft={employee.status === 'draft'}>
						{EMPLOYEE_STATUS_LABELS[employee.status]}
					</span>
				</span>
			</div>
		</section>

		<!-- Employment -->
		<section class="detail-section">
			<h3 class="section-title">Employment</h3>
			<div class="detail-row">
				<span class="detail-label">Province</span>
				<span class="detail-value">{PROVINCE_LABELS[employee.provinceOfEmployment]}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Employment Type</span>
				<span class="detail-value">{EMPLOYMENT_TYPE_LABELS[employee.employmentType]}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Pay Frequency</span>
				<span class="detail-value">{PAY_FREQUENCY_LABELS[employee.payFrequency]}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Hire Date</span>
				<span class="detail-value">{formatDate(employee.hireDate)}</span>
			</div>
			{#if employee.terminationDate}
				<div class="detail-row">
					<span class="detail-label">Termination Date</span>
					<span class="detail-value">{formatDate(employee.terminationDate)}</span>
				</div>
			{/if}
		</section>

		<!-- Compensation -->
		<section class="detail-section">
			<h3 class="section-title">Compensation</h3>
			<div class="detail-row">
				<span class="detail-label">Type</span>
				<span class="detail-value">{employee.hourlyRate ? 'Hourly' : 'Salaried'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">{employee.hourlyRate ? 'Hourly Rate' : 'Annual Salary'}</span>
				<span class="detail-value highlight">{formatCompensation(employee)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Per-Period Gross</span>
				<span class="detail-value">{getPerPeriodAmount(employee)}</span>
			</div>
		</section>

		<!-- Tax Information -->
		<section class="detail-section">
			<h3 class="section-title">Tax Information (TD1)</h3>
			<div class="detail-row">
				<span class="detail-label">Federal Additional Claims</span>
				<span class="detail-value">{formatCurrency(employee.federalAdditionalClaims)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Provincial Additional Claims</span>
				<span class="detail-value">{formatCurrency(employee.provincialAdditionalClaims)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">CPP Exempt</span>
				<span class="detail-value">{employee.isCppExempt ? 'Yes' : 'No'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">EI Exempt</span>
				<span class="detail-value">{employee.isEiExempt ? 'Yes' : 'No'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">CPP2 Exempt</span>
				<span class="detail-value tooltip-container">
					{employee.cpp2Exempt ? 'Yes' : 'No'}
					{#if employee.cpp2Exempt}
						<span class="info-tooltip" title="CPT30 form on file - exempt from additional CPP contributions for multi-job employees">
							<i class="fas fa-info-circle"></i>
						</span>
					{/if}
				</span>
			</div>
		</section>

		<!-- Deductions -->
		<section class="detail-section">
			<h3 class="section-title">Optional Deductions</h3>
			<div class="detail-row">
				<span class="detail-label">RRSP Per Period</span>
				<span class="detail-value">{formatCurrency(employee.rrspPerPeriod)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Union Dues Per Period</span>
				<span class="detail-value">{formatCurrency(employee.unionDuesPerPeriod)}</span>
			</div>
		</section>

		<!-- Vacation -->
		<section class="detail-section">
			<h3 class="section-title">Vacation</h3>
			<div class="detail-row">
				<span class="detail-label">Payout Method</span>
				<span class="detail-value" style="text-transform: capitalize;">
					{employee.vacationConfig.payoutMethod.replace('_', ' ')}
				</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Vacation Rate</span>
				<span class="detail-value">
					{formatVacationRate(employee.vacationConfig.vacationRate)}
				</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Current Balance</span>
				<span class="detail-value highlight">{formatCurrency(employee.vacationBalance)}</span>
			</div>
		</section>

		<!-- Actions -->
		<div class="sidebar-actions">
			<button class="btn-primary full-width" onclick={handleEdit}>
				<i class="fas fa-edit"></i>
				Edit Employee
			</button>
			<button class="btn-secondary full-width">
				<i class="fas fa-history"></i>
				View Pay History
			</button>
		</div>
	</div>
</aside>

<style>
	/* Detail Sidebar */
	.detail-sidebar {
		width: 360px;
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-2);
		overflow: hidden;
		position: sticky;
		top: var(--spacing-4);
		max-height: calc(100vh - var(--spacing-8));
		display: flex;
		flex-direction: column;
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.sidebar-header h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.close-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.close-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.sidebar-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-4) var(--spacing-5);
	}

	.detail-section {
		margin-bottom: var(--spacing-5);
	}

	.section-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 var(--spacing-3);
		padding-bottom: var(--spacing-2);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2) 0;
	}

	.detail-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.detail-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		font-weight: var(--font-weight-medium);
	}

	.detail-value.highlight {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-semibold);
	}

	/* Status Badge */
	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	/* Tooltip */
	.tooltip-container {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.info-tooltip {
		color: var(--color-surface-400);
		font-size: 0.75rem;
		cursor: help;
		transition: var(--transition-fast);
	}

	.info-tooltip:hover {
		color: var(--color-primary-500);
	}

	/* SIN Toggle */
	.sin-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-1) var(--spacing-2);
		border: none;
		background: transparent;
		font-family: monospace;
		font-size: inherit;
		color: var(--color-surface-700);
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: var(--transition-fast);
	}

	.sin-toggle:hover {
		background: var(--color-surface-100);
	}

	.sin-toggle i {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-400);
	}

	.sidebar-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-100);
		margin-top: var(--spacing-4);
	}

	.btn-primary,
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.btn-primary.full-width,
	.btn-secondary.full-width {
		width: 100%;
		justify-content: center;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.detail-sidebar {
			width: 100%;
			position: fixed;
			right: 0;
			top: 0;
			height: 100vh;
			max-height: 100vh;
			border-radius: 0;
			z-index: 100;
		}
	}
</style>
