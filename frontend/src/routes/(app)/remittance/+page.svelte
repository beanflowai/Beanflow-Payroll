<script lang="ts">
	// Remittance page - Phase 0 static UI prototype
	import { REMITTER_TYPE_INFO } from '$lib/types/company';
	import type { RemitterType } from '$lib/types/company';
	import {
		REMITTANCE_STATUS_INFO,
		PAYMENT_METHOD_INFO,
		determineRemittanceStatus,
		formatPeriodLabel,
		calculatePenaltyRate,
		calculatePenaltyAmount
	} from '$lib/types/remittance';
	import type { RemittancePeriod, RemittanceStatus, PaymentMethod } from '$lib/types/remittance';
	import MarkAsPaidModal from '$lib/components/remittance/MarkAsPaidModal.svelte';

	// Mock data
	let selectedYear = $state(2025);
	let remitterType: RemitterType = 'regular';

	// Mock remittance data
	const mockRemittances: RemittancePeriod[] = [
		{
			id: '1',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-12-01',
			periodEnd: '2025-12-31',
			periodLabel: 'December 2025',
			dueDate: '2026-01-15',
			cppEmployee: 1500,
			cppEmployer: 1500,
			eiEmployee: 400,
			eiEmployer: 560,
			federalTax: 3000,
			provincialTax: 1200,
			totalAmount: 8160,
			status: 'pending',
			paidDate: null,
			paymentMethod: null,
			confirmationNumber: null,
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_1', 'run_2'],
			createdAt: '2025-12-01T00:00:00Z',
			updatedAt: '2025-12-01T00:00:00Z'
		},
		{
			id: '2',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-11-01',
			periodEnd: '2025-11-30',
			periodLabel: 'November 2025',
			dueDate: '2025-12-15',
			cppEmployee: 1450,
			cppEmployer: 1450,
			eiEmployee: 390,
			eiEmployer: 546,
			federalTax: 2900,
			provincialTax: 1154,
			totalAmount: 7890,
			status: 'paid',
			paidDate: '2025-12-14',
			paymentMethod: 'my_payment',
			confirmationNumber: 'PAY-2025-12-001234',
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_3', 'run_4'],
			createdAt: '2025-11-01T00:00:00Z',
			updatedAt: '2025-12-14T00:00:00Z'
		},
		{
			id: '3',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-10-01',
			periodEnd: '2025-10-31',
			periodLabel: 'October 2025',
			dueDate: '2025-11-15',
			cppEmployee: 1400,
			cppEmployer: 1400,
			eiEmployee: 380,
			eiEmployer: 532,
			federalTax: 2800,
			provincialTax: 1138,
			totalAmount: 7650,
			status: 'paid',
			paidDate: '2025-11-12',
			paymentMethod: 'online_banking',
			confirmationNumber: null,
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_5', 'run_6'],
			createdAt: '2025-10-01T00:00:00Z',
			updatedAt: '2025-11-12T00:00:00Z'
		},
		{
			id: '4',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-09-01',
			periodEnd: '2025-09-30',
			periodLabel: 'September 2025',
			dueDate: '2025-10-15',
			cppEmployee: 1350,
			cppEmployer: 1350,
			eiEmployee: 370,
			eiEmployer: 518,
			federalTax: 2700,
			provincialTax: 1112,
			totalAmount: 7400,
			status: 'paid',
			paidDate: '2025-10-14',
			paymentMethod: 'my_payment',
			confirmationNumber: 'PAY-2025-10-000987',
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_7', 'run_8'],
			createdAt: '2025-09-01T00:00:00Z',
			updatedAt: '2025-10-14T00:00:00Z'
		}
	];

	// Get upcoming remittance (first pending)
	let upcomingRemittance = $derived(mockRemittances.find((r) => r.status === 'pending') || null);

	// Calculate summary stats
	let summary = $derived(() => {
		const paidRemittances = mockRemittances.filter((r) => r.status === 'paid' || r.status === 'paid_late');
		const pendingRemittances = mockRemittances.filter((r) => r.status === 'pending' || r.status === 'due_soon' || r.status === 'overdue');

		return {
			ytdRemitted: paidRemittances.reduce((sum, r) => sum + r.totalAmount, 0),
			completedCount: paidRemittances.length,
			totalCount: 12, // For regular monthly
			onTimeRate: 1.0, // 100% on time
			pendingAmount: pendingRemittances.reduce((sum, r) => sum + r.totalAmount, 0),
			pendingCount: pendingRemittances.length
		};
	});

	// Days until due date
	function getDaysUntilDue(dueDate: string): number {
		const due = new Date(dueDate);
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		due.setHours(0, 0, 0, 0);
		return Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
	}

	// Format currency
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	// Format date
	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Modal state
	let showMarkAsPaidModal = $state(false);
	let selectedRemittance = $state<RemittancePeriod | null>(null);

	function openMarkAsPaidModal(remittance: RemittancePeriod) {
		selectedRemittance = remittance;
		showMarkAsPaidModal = true;
	}

	function closeModal() {
		showMarkAsPaidModal = false;
		selectedRemittance = null;
	}

	function handleMarkAsPaid(data: {
		paymentDate: string;
		paymentMethod: PaymentMethod;
		confirmationNumber: string;
	}) {
		// TODO: API call to mark as paid
		console.log('Mark as paid:', selectedRemittance?.id, data);
		closeModal();
	}

	// Expanded row state
	let expandedRowId = $state<string | null>(null);

	function toggleRowExpansion(id: string) {
		expandedRowId = expandedRowId === id ? null : id;
	}
</script>

<svelte:head>
	<title>Remittance - BeanFlow Payroll</title>
</svelte:head>

<div class="max-w-[1000px]">
	<header class="flex justify-between items-start mb-6 max-md:flex-col max-md:gap-4">
		<div>
			<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">CRA Remittance</h1>
			<p class="text-body-content text-surface-600 m-0">Track and manage your payroll deduction remittances</p>
		</div>
		<div class="flex items-center gap-2 bg-white rounded-lg p-2 shadow-md3-1">
			<button
				class="w-8 h-8 border-none bg-transparent text-surface-600 cursor-pointer rounded-md transition-[150ms] hover:bg-surface-100 hover:text-surface-800"
				onclick={() => (selectedYear = selectedYear - 1)}
			>
				<i class="fas fa-chevron-left"></i>
			</button>
			<span class="text-title-medium font-semibold text-surface-800 min-w-[60px] text-center">{selectedYear}</span>
			<button
				class="w-8 h-8 border-none bg-transparent text-surface-600 cursor-pointer rounded-md transition-[150ms] hover:bg-surface-100 hover:text-surface-800"
				onclick={() => (selectedYear = selectedYear + 1)}
			>
				<i class="fas fa-chevron-right"></i>
			</button>
		</div>
	</header>

	<!-- Remitter Type Badge -->
	<div class="inline-flex items-center gap-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-full text-auxiliary-text font-medium mb-6">
		<i class="fas fa-landmark"></i>
		<span>{REMITTER_TYPE_INFO[remitterType].label}</span>
		<span class="text-secondary-300">|</span>
		<span class="text-secondary-600">Due 15th of following month</span>
	</div>

	<!-- Upcoming Remittance Card -->
	{#if upcomingRemittance}
		{@const daysUntil = getDaysUntilDue(upcomingRemittance.dueDate)}
		{@const isOverdue = daysUntil < 0}
		{@const isDueSoon = daysUntil >= 0 && daysUntil <= 7}

		<div
			class="bg-white rounded-xl shadow-md3-2 p-6 mb-6 border-l-4 {isOverdue
				? 'border-l-error-500 bg-error-50'
				: isDueSoon
					? 'border-l-warning-500'
					: 'border-l-primary-500'}"
		>
			<div class="flex items-center gap-2 text-auxiliary-text font-semibold uppercase tracking-wider mb-4 {isOverdue ? 'text-error-600' : isDueSoon ? 'text-warning-600' : 'text-primary-600'}">
				{#if isOverdue}
					<i class="fas fa-exclamation-circle"></i>
					<span>REMITTANCE OVERDUE</span>
				{:else if isDueSoon}
					<i class="fas fa-exclamation-triangle"></i>
					<span>REMITTANCE DUE SOON</span>
				{:else}
					<i class="fas fa-clock"></i>
					<span>NEXT REMITTANCE DUE</span>
				{/if}
			</div>

			<div class="flex flex-col gap-4">
				<div class="flex gap-2 text-body-content">
					<span class="text-surface-500">Period:</span>
					<span class="text-surface-800 font-medium">{upcomingRemittance.periodLabel}</span>
				</div>
				<div class="flex gap-2 text-body-content">
					<span class="text-surface-500">Due Date:</span>
					<span class="text-surface-800 font-medium">{formatDate(upcomingRemittance.dueDate)}</span>
				</div>

				<div class="text-center py-6 rounded-lg {isOverdue ? 'bg-error-100' : 'bg-surface-50'}">
					<span class="block text-headline-minimum font-bold text-surface-900">{formatCurrency(upcomingRemittance.totalAmount)}</span>
					<span class="text-auxiliary-text text-surface-600">Total Amount Due</span>
				</div>

				<div class="grid grid-cols-3 gap-4 max-md:grid-cols-1">
					<div class="text-center p-3 bg-surface-50 rounded-md">
						<span class="block text-auxiliary-text text-surface-500 mb-1">CPP</span>
						<span class="block text-title-medium font-semibold text-surface-800">{formatCurrency(upcomingRemittance.cppEmployee + upcomingRemittance.cppEmployer)}</span>
						<span class="text-auxiliary-text text-surface-500">Emp + Empr</span>
					</div>
					<div class="text-center p-3 bg-surface-50 rounded-md">
						<span class="block text-auxiliary-text text-surface-500 mb-1">EI</span>
						<span class="block text-title-medium font-semibold text-surface-800">{formatCurrency(upcomingRemittance.eiEmployee + upcomingRemittance.eiEmployer)}</span>
						<span class="text-auxiliary-text text-surface-500">Emp + Empr</span>
					</div>
					<div class="text-center p-3 bg-surface-50 rounded-md">
						<span class="block text-auxiliary-text text-surface-500 mb-1">Income Tax</span>
						<span class="block text-title-medium font-semibold text-surface-800">{formatCurrency(upcomingRemittance.federalTax + upcomingRemittance.provincialTax)}</span>
						<span class="text-auxiliary-text text-surface-500">Fed + Prov</span>
					</div>
				</div>

				<div class="flex items-center justify-center gap-2 text-body-content {isOverdue ? 'text-error-600' : isDueSoon ? 'text-warning-600' : 'text-surface-600'}">
					{#if isOverdue}
						<i class="fas fa-exclamation-circle"></i>
						<span>{Math.abs(daysUntil)} days overdue - Pay immediately to avoid additional penalties</span>
					{:else}
						<i class="fas fa-clock"></i>
						<span>{daysUntil} days until due</span>
					{/if}
				</div>

				<div class="flex justify-center gap-3 pt-4 border-t border-surface-100 max-md:flex-col">
					<button class="inline-flex items-center justify-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-surface-300">
						<i class="fas fa-file-pdf"></i>
						<span>Generate PD7A</span>
					</button>
					<button
						class="inline-flex items-center justify-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-[150ms] hover:opacity-90 hover:-translate-y-px"
						onclick={() => openMarkAsPaidModal(upcomingRemittance)}
					>
						<i class="fas fa-check"></i>
						<span>Mark as Paid</span>
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Summary Cards -->
	<div class="grid grid-cols-4 gap-4 mb-6 max-md:grid-cols-2 max-sm:grid-cols-1">
		<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
			<span class="text-auxiliary-text text-surface-500">YTD Remitted</span>
			<span class="text-title-large font-semibold text-surface-800">{formatCurrency(summary().ytdRemitted)}</span>
			<span class="text-auxiliary-text text-surface-500">Total paid this year</span>
		</div>
		<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
			<span class="text-auxiliary-text text-surface-500">Remittances</span>
			<span class="text-title-large font-semibold text-surface-800">{summary().completedCount} of {summary().totalCount}</span>
			<span class="text-auxiliary-text text-surface-500">Completed this year</span>
		</div>
		<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
			<span class="text-auxiliary-text text-surface-500">On-Time Rate</span>
			<span class="text-title-large font-semibold text-success-600">{(summary().onTimeRate * 100).toFixed(0)}%</span>
			<span class="text-auxiliary-text text-surface-500">No late payments</span>
		</div>
		<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
			<span class="text-auxiliary-text text-surface-500">Pending</span>
			<span class="text-title-large font-semibold text-surface-800">{formatCurrency(summary().pendingAmount)}</span>
			<span class="text-auxiliary-text text-surface-500">{summary().pendingCount} pending remittance(s)</span>
		</div>
	</div>

	<!-- Remittance History Table -->
	<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
		<div class="flex justify-between items-center px-6 py-4 border-b border-surface-100">
			<h2 class="text-title-medium font-semibold text-surface-800 m-0">Remittance History</h2>
			<button class="inline-flex items-center gap-2 px-3 py-2 bg-transparent border-none text-primary-600 text-body-content font-medium cursor-pointer rounded-md transition-[150ms] hover:bg-primary-50">
				<i class="fas fa-download"></i>
				<span>Export</span>
			</button>
		</div>

		<div class="overflow-x-auto">
			<table class="w-full border-collapse">
				<thead>
					<tr>
						<th class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Period</th>
						<th class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Due Date</th>
						<th class="px-4 py-3 text-right text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Amount</th>
						<th class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Paid</th>
						<th class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Status</th>
						<th class="px-4 py-3 text-center text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each mockRemittances as remittance (remittance.id)}
						{@const statusInfo = REMITTANCE_STATUS_INFO[remittance.status]}
						<tr
							class="cursor-pointer transition-[150ms] hover:bg-surface-50 {expandedRowId === remittance.id ? 'bg-primary-50' : ''}"
							onclick={() => toggleRowExpansion(remittance.id)}
						>
							<td class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-800">
								<div class="flex items-center gap-2">
									<i class="fas fa-chevron-right text-xs text-surface-400 transition-[150ms] {expandedRowId === remittance.id ? 'rotate-90' : ''}"></i>
									{remittance.periodLabel}
								</div>
							</td>
							<td class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-800">{formatDate(remittance.dueDate)}</td>
							<td class="px-4 py-3 text-right text-body-content border-b border-surface-100 text-surface-800 font-medium">{formatCurrency(remittance.totalAmount)}</td>
							<td class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-800">{remittance.paidDate ? formatDate(remittance.paidDate) : '-'}</td>
							<td class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-800">
								<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-auxiliary-text font-medium {statusInfo.colorClass}">
									<i class="fas fa-{statusInfo.icon}"></i>
									{statusInfo.label}
								</span>
							</td>
							<td class="px-4 py-3 text-center text-body-content border-b border-surface-100 text-surface-800">
								<button
									class="w-8 h-8 border-none bg-transparent text-surface-500 cursor-pointer rounded-md transition-[150ms] hover:bg-surface-100 hover:text-surface-700"
									onclick={(e) => { e.stopPropagation(); }}
								>
									<i class="fas fa-ellipsis-v"></i>
								</button>
							</td>
						</tr>

						{#if expandedRowId === remittance.id}
							<tr>
								<td colspan="6" class="p-0 bg-surface-50">
									<div class="p-6 flex flex-col gap-6">
										<div class="bg-white rounded-lg p-4">
											<h4 class="text-body-content font-semibold text-surface-800 m-0 mb-3">Period Details</h4>
											<div class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-4">
												<div class="flex flex-col gap-1">
													<span class="text-auxiliary-text text-surface-500">Period</span>
													<span class="text-body-content text-surface-800">{formatDate(remittance.periodStart)} - {formatDate(remittance.periodEnd)}</span>
												</div>
												<div class="flex flex-col gap-1">
													<span class="text-auxiliary-text text-surface-500">Due Date</span>
													<span class="text-body-content text-surface-800">{formatDate(remittance.dueDate)}</span>
												</div>
												<div class="flex flex-col gap-1">
													<span class="text-auxiliary-text text-surface-500">Payroll Runs</span>
													<span class="text-body-content text-surface-800">{remittance.payrollRunIds.length} runs included</span>
												</div>
											</div>
										</div>

										<div class="bg-white rounded-lg p-4">
											<h4 class="text-body-content font-semibold text-surface-800 m-0 mb-3">Deduction Breakdown</h4>
											<table class="w-full border-collapse">
												<thead>
													<tr>
														<th class="px-3 py-2 text-left text-body-content bg-surface-50 text-surface-600 font-medium">Category</th>
														<th class="px-3 py-2 text-right text-body-content bg-surface-50 text-surface-600 font-medium">Employee</th>
														<th class="px-3 py-2 text-right text-body-content bg-surface-50 text-surface-600 font-medium">Employer</th>
													</tr>
												</thead>
												<tbody>
													<tr>
														<td class="px-3 py-2 text-body-content border-b border-surface-100">CPP Contributions</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.cppEmployee)}</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.cppEmployer)}</td>
													</tr>
													<tr>
														<td class="px-3 py-2 text-body-content border-b border-surface-100">EI Premiums</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.eiEmployee)}</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.eiEmployer)}</td>
													</tr>
													<tr>
														<td class="px-3 py-2 text-body-content border-b border-surface-100">Federal Income Tax</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.federalTax)}</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">-</td>
													</tr>
													<tr>
														<td class="px-3 py-2 text-body-content border-b border-surface-100">Provincial Income Tax</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">{formatCurrency(remittance.provincialTax)}</td>
														<td class="px-3 py-2 text-right text-body-content border-b border-surface-100">-</td>
													</tr>
													<tr class="font-semibold bg-surface-50">
														<td class="px-3 py-2 text-body-content">TOTAL</td>
														<td class="px-3 py-2 text-right text-body-content">{formatCurrency(remittance.cppEmployee + remittance.eiEmployee + remittance.federalTax + remittance.provincialTax)}</td>
														<td class="px-3 py-2 text-right text-body-content">{formatCurrency(remittance.cppEmployer + remittance.eiEmployer)}</td>
													</tr>
												</tbody>
											</table>
										</div>

										{#if remittance.paidDate}
											<div class="bg-white rounded-lg p-4">
												<h4 class="text-body-content font-semibold text-surface-800 m-0 mb-3">Payment Information</h4>
												<div class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-4">
													<div class="flex flex-col gap-1">
														<span class="text-auxiliary-text text-surface-500">Status</span>
														<span class="text-body-content text-success-600">
															<i class="fas fa-check-circle"></i> Paid
														</span>
													</div>
													<div class="flex flex-col gap-1">
														<span class="text-auxiliary-text text-surface-500">Payment Date</span>
														<span class="text-body-content text-surface-800">{formatDate(remittance.paidDate)}</span>
													</div>
													<div class="flex flex-col gap-1">
														<span class="text-auxiliary-text text-surface-500">Payment Method</span>
														<span class="text-body-content text-surface-800">{remittance.paymentMethod ? PAYMENT_METHOD_INFO[remittance.paymentMethod].label : '-'}</span>
													</div>
													{#if remittance.confirmationNumber}
														<div class="flex flex-col gap-1">
															<span class="text-auxiliary-text text-surface-500">Confirmation #</span>
															<span class="text-body-content text-surface-800">{remittance.confirmationNumber}</span>
														</div>
													{/if}
												</div>
											</div>
										{/if}
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>

<!-- Mark as Paid Modal -->
{#if showMarkAsPaidModal && selectedRemittance}
	<MarkAsPaidModal
		remittance={selectedRemittance}
		onClose={closeModal}
		onSubmit={handleMarkAsPaid}
	/>
{/if}
