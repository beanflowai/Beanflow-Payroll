<script lang="ts">
	import type { PayrollRun } from '$lib/types/payroll';
	import { SummaryCard } from '$lib/components/shared';

	interface Props {
		payrollRun: PayrollRun;
	}

	let { payrollRun }: Props = $props();

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}
</script>

<!-- Summary Cards - Row 1 -->
<div class="summary-grid">
	<SummaryCard label="Total Gross" value={formatCurrency(payrollRun.totalGross)} />
	<SummaryCard label="Total Deductions" value={`-${formatCurrency(payrollRun.totalDeductions)}`} valueClass="deductions" />
	<SummaryCard label="Net Pay" value={formatCurrency(payrollRun.totalNetPay)} variant="highlight" />
	<SummaryCard label="Employees" value={payrollRun.totalEmployees} />
</div>

<!-- Summary Cards - Row 2: Employer Costs -->
<div class="summary-grid employer-costs">
	<SummaryCard label="Employer CPP" value={formatCurrency(payrollRun.totalCppEmployer)} variant="small" />
	<SummaryCard label="Employer EI" value={formatCurrency(payrollRun.totalEiEmployer)} variant="small" />
	<SummaryCard label="Total Employer Cost" value={formatCurrency(payrollRun.totalEmployerCost)} variant="accent" />
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
