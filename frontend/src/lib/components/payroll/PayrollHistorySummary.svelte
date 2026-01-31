<script lang="ts">
	import { formatCurrency } from '$lib/utils/formatUtils';
	import type { PayrollRunWithGroups } from '$lib/types/payroll';
	import type { PayrollRecordWithPeriod } from '$lib/services/payroll';

	interface Props {
		count: number;
		isEmployeeView: boolean;
		records: (PayrollRunWithGroups | PayrollRecordWithPeriod)[];
	}

	let { count, isEmployeeView, records }: Props = $props();

	// Type guards
	function isPayrollRuns(
		recs: (PayrollRunWithGroups | PayrollRecordWithPeriod)[]
	): recs is PayrollRunWithGroups[] {
		return !isEmployeeView;
	}

	function isPayrollRecords(
		recs: (PayrollRunWithGroups | PayrollRecordWithPeriod)[]
	): recs is PayrollRecordWithPeriod[] {
		return isEmployeeView;
	}

	const stats = $derived.by(() => {
		if (isEmployeeView && isPayrollRecords(records)) {
			// Employee View Aggregation
			return {
				grossPay: records.reduce((sum, r) => sum + r.totalGross, 0),
				employeeCpp: records.reduce((sum, r) => sum + r.cppEmployee + r.cppAdditional, 0),
				employeeEi: records.reduce((sum, r) => sum + r.eiEmployee, 0),
				employeeTax: records.reduce((sum, r) => sum + r.federalTax + r.provincialTax, 0),
				netPay: records.reduce((sum, r) => sum + r.netPay, 0),
				employerCpp: records.reduce((sum, r) => sum + r.cppEmployer, 0),
				employerEi: records.reduce((sum, r) => sum + r.eiEmployer, 0),
				totalRemittance: records.reduce(
					(sum, r) =>
						sum +
						r.cppEmployee +
						r.cppAdditional +
						r.cppEmployer +
						r.eiEmployee +
						r.eiEmployer +
						r.federalTax +
						r.provincialTax,
					0
				)
			};
		} else if (!isEmployeeView && isPayrollRuns(records)) {
			// Summary View Aggregation
			return {
				grossPay: records.reduce((sum, r) => sum + r.totalGross, 0),
				employeeCpp: records.reduce((sum, r) => sum + r.totalCppEmployee, 0),
				employeeEi: records.reduce((sum, r) => sum + r.totalEiEmployee, 0),
				employeeTax: records.reduce(
					(sum, r) => sum + r.totalFederalTax + r.totalProvincialTax,
					0
				),
				netPay: records.reduce((sum, r) => sum + r.totalNetPay, 0),
				employerCpp: records.reduce((sum, r) => sum + r.totalCppEmployer, 0),
				employerEi: records.reduce((sum, r) => sum + r.totalEiEmployer, 0),
				totalRemittance: records.reduce((sum, r) => sum + r.totalRemittance, 0)
			};
		}
		return {
			grossPay: 0,
			employeeCpp: 0,
			employeeEi: 0,
			employeeTax: 0,
			netPay: 0,
			employerCpp: 0,
			employerEi: 0,
			totalRemittance: 0
		};
	});
</script>

<div class="grid grid-cols-4 gap-4 mb-6 max-xl:grid-cols-2 max-sm:grid-cols-1">
	<!-- 1. Summary Card -->
	<div
		class="flex flex-col gap-4 p-4 bg-primary-50 rounded-xl shadow-md3-1 border border-primary-100"
	>
		<div
			class="flex items-center gap-2 text-primary-700 font-bold border-b border-primary-200 pb-2"
		>
			<i class="fas fa-chart-simple"></i>
			<span class="text-xs uppercase tracking-wider">SUMMARY</span>
		</div>

		<div>
			<div class="flex flex-col mb-3">
				<span class="text-2xl font-bold text-surface-900">{count}</span>
				<span class="text-xs text-surface-600 font-medium">
					{isEmployeeView ? 'Pay Periods' : 'Payroll Runs'}
				</span>
			</div>

			<div class="flex flex-col">
				<span class="text-xs text-surface-600 font-medium uppercase tracking-wide">Gross Pay</span>
				<span class="text-lg font-bold text-surface-800 font-mono">
					{formatCurrency(stats.grossPay)}
				</span>
			</div>
		</div>
	</div>

	<!-- 2. Employee Deductions Card -->
	<div
		class="flex flex-col gap-3 p-4 bg-surface-50 rounded-xl shadow-md3-1 border border-surface-200"
	>
		<div
			class="flex items-center gap-2 text-surface-700 font-bold border-b border-surface-200 pb-2"
		>
			<i class="fas fa-user text-surface-500"></i>
			<span class="text-xs uppercase tracking-wider">EMPLOYEE DEDUCTIONS</span>
		</div>

		<div class="space-y-1">
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">CPP</span>
				<span class="font-mono font-medium text-surface-800"
					>{formatCurrency(stats.employeeCpp)}</span
				>
			</div>
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">EI</span>
				<span class="font-mono font-medium text-surface-800"
					>{formatCurrency(stats.employeeEi)}</span
				>
			</div>
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">Tax</span>
				<span class="font-mono font-medium text-surface-800"
					>{formatCurrency(stats.employeeTax)}</span
				>
			</div>
		</div>

		<div class="border-t border-surface-200 pt-2 mt-auto">
			<div class="flex justify-between items-end">
				<span class="text-xs font-bold text-surface-600 uppercase">Net Pay</span>
				<span class="text-lg font-bold text-surface-900 font-mono"
					>{formatCurrency(stats.netPay)}</span
				>
			</div>
		</div>
	</div>

	<!-- 3. Employer Contributions Card -->
	<div
		class="flex flex-col gap-3 p-4 bg-tertiary-50 rounded-xl shadow-md3-1 border border-tertiary-100"
	>
		<div
			class="flex items-center gap-2 text-tertiary-700 font-bold border-b border-tertiary-200 pb-2"
		>
			<i class="fas fa-building text-tertiary-600"></i>
			<span class="text-xs uppercase tracking-wider">EMPLOYER CONTRIBUTIONS</span>
		</div>

		<div class="space-y-1">
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">CPP</span>
				<span class="font-mono font-medium text-surface-800"
					>{formatCurrency(stats.employerCpp)}</span
				>
			</div>
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">EI</span>
				<span class="font-mono font-medium text-surface-800"
					>{formatCurrency(stats.employerEi)}</span
				>
			</div>
		</div>

		<div class="border-t border-tertiary-200 pt-2 mt-auto">
			<div class="flex justify-between items-end">
				<span class="text-xs font-bold text-tertiary-700 uppercase">Total Cost</span>
				<span class="text-lg font-bold text-tertiary-900 font-mono">
					{formatCurrency(stats.employerCpp + stats.employerEi)}
				</span>
			</div>
		</div>
	</div>

	<!-- 4. Remittance Card -->
	<div
		class="flex flex-col gap-3 p-4 bg-warning-50 rounded-xl shadow-md3-1 border border-warning-100"
	>
		<div
			class="flex items-center gap-2 text-warning-800 font-bold border-b border-warning-200 pb-2"
		>
			<i class="fas fa-paper-plane text-warning-600"></i>
			<span class="text-xs uppercase tracking-wider">REMITTANCE</span>
		</div>

		<div class="space-y-1">
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">Total CPP</span>
				<span class="font-mono font-medium text-surface-800">
					{formatCurrency(stats.employeeCpp + stats.employerCpp)}
				</span>
			</div>
			<div class="flex justify-between text-sm">
				<span class="text-surface-600">Total EI</span>
				<span class="font-mono font-medium text-surface-800">
					{formatCurrency(stats.employeeEi + stats.employerEi)}
				</span>
			</div>
		</div>

		<div class="border-t border-warning-200 pt-2 mt-auto">
			<div class="flex justify-between items-end">
				<span class="text-xs font-bold text-warning-800 uppercase">Total Remit</span>
				<span class="text-lg font-bold text-warning-900 font-mono">
					{formatCurrency(stats.totalRemittance)}
				</span>
			</div>
		</div>
	</div>
</div>
