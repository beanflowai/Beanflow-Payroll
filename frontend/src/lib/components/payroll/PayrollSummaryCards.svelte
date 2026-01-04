<script lang="ts">
	import type { PayrollRunWithGroups } from '$lib/types/payroll';
	import { SummaryCard } from '$lib/components/shared';
	import Tooltip from '$lib/components/shared/Tooltip.svelte';
	import { formatCurrency } from '$lib/utils';

	interface Props {
		payrollRun: PayrollRunWithGroups;
	}

	let { payrollRun }: Props = $props();

	// Tooltip content
	const tooltips = $derived({
		totalDeductions:
			'Amount withheld from employee pay: CPP, EI, income taxes, and other deductions',
		totalEmployerCost: `Employer CPP: ${formatCurrency(payrollRun.totalCppEmployer)} + Employer EI: ${formatCurrency(payrollRun.totalEiEmployer)}`,
		totalPayrollCost: 'Total Gross + Total Employer Cost',
		totalRemittance: 'Amount to remit to CRA: Employee & Employer CPP/EI + Income Taxes'
	});
</script>

<!-- Summary Cards - Row 1: Employee Perspective -->
<div class="summary-grid">
	<SummaryCard label="Total Gross" value={formatCurrency(payrollRun.totalGross)} />
	<Tooltip content={tooltips.totalDeductions}>
		<SummaryCard
			label="Total Deductions"
			value={`-${formatCurrency(payrollRun.totalDeductions)}`}
			valueClass="deductions"
		/>
	</Tooltip>
	<SummaryCard label="Net Pay" value={formatCurrency(payrollRun.totalNetPay)} variant="highlight" />
	<SummaryCard label="Employees" value={payrollRun.totalEmployees} />
</div>

<!-- Summary Cards - Row 2: Employer Perspective -->
<div class="summary-grid employer-costs">
	<Tooltip content={tooltips.totalEmployerCost}>
		<SummaryCard
			label="Total Employer Cost"
			value={formatCurrency(payrollRun.totalEmployerCost)}
			variant="small"
		/>
	</Tooltip>
	<Tooltip content={tooltips.totalPayrollCost}>
		<SummaryCard
			label="Total Payroll Cost"
			value={formatCurrency(payrollRun.totalPayrollCost)}
			variant="highlight"
		/>
	</Tooltip>
	<Tooltip content={tooltips.totalRemittance}>
		<SummaryCard
			label="Total Remittance"
			value={formatCurrency(payrollRun.totalRemittance)}
			variant="small"
		/>
	</Tooltip>
</div>

<style>
	/* Summary Grid */
	.summary-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-4);
	}

	.summary-grid.employer-costs {
		grid-template-columns: repeat(3, 1fr);
		margin-bottom: var(--spacing-8);
	}

	@media (max-width: 768px) {
		.summary-grid.employer-costs {
			grid-template-columns: 1fr;
		}
	}
</style>
