<script lang="ts">
	import { REMITTER_TYPE_INFO } from '$lib/types/company';
	import type { RemitterType } from '$lib/types/company';
	import {
		REMITTANCE_STATUS_INFO,
		PAYMENT_METHOD_INFO
	} from '$lib/types/remittance';
	import type { RemittancePeriod, RemittanceSummary, PaymentMethod } from '$lib/types/remittance';
	import MarkAsPaidModal from '$lib/components/remittance/MarkAsPaidModal.svelte';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { companyState } from '$lib/stores/company.svelte';
	import {
		listRemittancePeriods,
		getRemittanceSummary,
		recordPayment,
		downloadPD7A
	} from '$lib/services/remittanceService';

	// State
	let selectedYear = $state(new Date().getFullYear());
	let remittances = $state<RemittancePeriod[]>([]);
	let summary = $state<RemittanceSummary | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Get upcoming remittance (first pending)
	let upcomingRemittance = $derived(
		remittances.find((r) => r.status === 'pending' || r.status === 'due_soon' || r.status === 'overdue') || null
	);

	// Current company derived from store
	const currentCompany = $derived(companyState.currentCompany);
	const remitterType = $derived<RemitterType>(currentCompany?.remitterType ?? 'regular');

	// Load data
	async function loadData(companyId: string, year: number) {
		loading = true;
		error = null;

		try {
			// Load remittance periods
			const periodsResult = await listRemittancePeriods(companyId, { year });
			if (periodsResult.error) {
				error = periodsResult.error;
				return;
			}
			remittances = periodsResult.data;

			// Load summary
			const summaryResult = await getRemittanceSummary(companyId, year);
			if (summaryResult.error) {
				error = summaryResult.error;
				return;
			}
			summary = summaryResult.data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	// Load data when company or year changes
	$effect(() => {
		const company = companyState.currentCompany;
		if (company) {
			loadData(company.id, selectedYear);
		} else if (!companyState.isLoading) {
			// No company selected and not loading - stop spinner
			loading = false;
		}
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
		return formatShortDate(dateStr);
	}

	// Modal state
	let showMarkAsPaidModal = $state(false);
	let selectedRemittance = $state<RemittancePeriod | null>(null);
	let submitting = $state(false);

	function openMarkAsPaidModal(remittance: RemittancePeriod) {
		selectedRemittance = remittance;
		showMarkAsPaidModal = true;
	}

	function closeModal() {
		showMarkAsPaidModal = false;
		selectedRemittance = null;
	}

	async function handleMarkAsPaid(data: {
		paymentDate: string;
		paymentMethod: PaymentMethod;
		confirmationNumber: string;
	}) {
		if (!selectedRemittance || !currentCompany) return;

		submitting = true;
		try {
			const result = await recordPayment(selectedRemittance.id, {
				paid_date: data.paymentDate,
				payment_method: data.paymentMethod,
				confirmation_number: data.confirmationNumber || undefined
			});

			if (result.error) {
				alert('Failed to record payment: ' + result.error);
				return;
			}

			// Reload data
			await loadData(currentCompany.id, selectedYear);
			closeModal();
		} catch (err) {
			alert('Failed to record payment: ' + (err instanceof Error ? err.message : 'Unknown error'));
		} finally {
			submitting = false;
		}
	}

	// PDF download
	let downloadingPdfId = $state<string | null>(null);

	async function handleDownloadPD7A(remittance: RemittancePeriod) {
		if (!currentCompany) return;

		downloadingPdfId = remittance.id;
		try {
			const result = await downloadPD7A(currentCompany.id, remittance.id);
			if (result.error) {
				error = result.error;
			}
		} finally {
			downloadingPdfId = null;
		}
	}

	// Expanded row state
	let expandedRowId = $state<string | null>(null);

	function toggleRowExpansion(id: string) {
		expandedRowId = expandedRowId === id ? null : id;
	}

	// Get due date description based on remitter type
	function getDueDateDescription(type: RemitterType): string {
		switch (type) {
			case 'quarterly':
				return 'Due 15th of month after quarter end';
			case 'regular':
				return 'Due 15th of following month';
			case 'threshold_1':
				return 'Due 25th (1st-15th) or 10th (16th-end)';
			case 'threshold_2':
				return 'Due within 3 days of withholding';
			default:
				return 'Due 15th of following month';
		}
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
		<span class="text-secondary-600">{getDueDateDescription(remitterType)}</span>
	</div>

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<i class="fas fa-spinner fa-spin text-2xl text-surface-400"></i>
		</div>
	{:else if error}
		<div class="bg-error-50 text-error-700 p-4 rounded-lg mb-6">
			<i class="fas fa-exclamation-circle mr-2"></i>
			{error}
		</div>
	{:else}
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
						<button
							class="inline-flex items-center justify-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-surface-300 disabled:opacity-50 disabled:cursor-not-allowed"
							onclick={() => handleDownloadPD7A(upcomingRemittance)}
							disabled={downloadingPdfId === upcomingRemittance.id}
						>
							{#if downloadingPdfId === upcomingRemittance.id}
								<i class="fas fa-spinner fa-spin"></i>
								<span>Downloading...</span>
							{:else}
								<i class="fas fa-file-pdf"></i>
								<span>Generate PD7A</span>
							{/if}
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
		{:else}
			<div class="bg-success-50 text-success-700 p-6 rounded-lg mb-6 text-center">
				<i class="fas fa-check-circle text-2xl mb-2"></i>
				<p class="m-0">All remittances for {selectedYear} are paid!</p>
			</div>
		{/if}

		<!-- Summary Cards -->
		{#if summary}
			<div class="grid grid-cols-4 gap-4 mb-6 max-md:grid-cols-2 max-sm:grid-cols-1">
				<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
					<span class="text-auxiliary-text text-surface-500">YTD Remitted</span>
					<span class="text-title-large font-semibold text-surface-800">{formatCurrency(summary.ytdRemitted)}</span>
					<span class="text-auxiliary-text text-surface-500">Total paid this year</span>
				</div>
				<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
					<span class="text-auxiliary-text text-surface-500">Remittances</span>
					<span class="text-title-large font-semibold text-surface-800">{summary.completedRemittances} of {summary.totalRemittances}</span>
					<span class="text-auxiliary-text text-surface-500">Completed this year</span>
				</div>
				<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
					<span class="text-auxiliary-text text-surface-500">On-Time Rate</span>
					<span class="text-title-large font-semibold text-success-600">{(summary.onTimeRate * 100).toFixed(0)}%</span>
					<span class="text-auxiliary-text text-surface-500">{summary.onTimeRate === 1 ? 'No late payments' : 'Some late payments'}</span>
				</div>
				<div class="bg-white rounded-lg shadow-md3-1 p-4 flex flex-col gap-1">
					<span class="text-auxiliary-text text-surface-500">Pending</span>
					<span class="text-title-large font-semibold text-surface-800">{formatCurrency(summary.pendingAmount)}</span>
					<span class="text-auxiliary-text text-surface-500">{summary.pendingCount} pending remittance(s)</span>
				</div>
			</div>
		{/if}

		<!-- Remittance History Table -->
		<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
			<div class="flex justify-between items-center px-6 py-4 border-b border-surface-100">
				<h2 class="text-title-medium font-semibold text-surface-800 m-0">Remittance History</h2>
				<button class="inline-flex items-center gap-2 px-3 py-2 bg-transparent border-none text-primary-600 text-body-content font-medium cursor-pointer rounded-md transition-[150ms] hover:bg-primary-50">
					<i class="fas fa-download"></i>
					<span>Export</span>
				</button>
			</div>

			{#if remittances.length === 0}
				<div class="p-8 text-center text-surface-500">
					<i class="fas fa-inbox text-4xl mb-4"></i>
					<p class="m-0">No remittance periods for {selectedYear}</p>
				</div>
			{:else}
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
							{#each remittances as remittance (remittance.id)}
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
										<div class="flex items-center justify-center gap-1">
											<button
												class="w-8 h-8 border-none bg-transparent text-surface-500 cursor-pointer rounded-md transition-[150ms] hover:bg-surface-100 hover:text-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
												title="Download PD7A"
												onclick={(e) => { e.stopPropagation(); handleDownloadPD7A(remittance); }}
												disabled={downloadingPdfId === remittance.id}
											>
												{#if downloadingPdfId === remittance.id}
													<i class="fas fa-spinner fa-spin"></i>
												{:else}
													<i class="fas fa-file-pdf"></i>
												{/if}
											</button>
											{#if remittance.status !== 'paid' && remittance.status !== 'paid_late'}
												<button
													class="w-8 h-8 border-none bg-transparent text-success-500 cursor-pointer rounded-md transition-[150ms] hover:bg-success-50 hover:text-success-700"
													title="Mark as Paid"
													onclick={(e) => { e.stopPropagation(); openMarkAsPaidModal(remittance); }}
												>
													<i class="fas fa-check"></i>
												</button>
											{/if}
										</div>
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
			{/if}
		</div>
	{/if}
</div>

<!-- Mark as Paid Modal -->
{#if showMarkAsPaidModal && selectedRemittance}
	<MarkAsPaidModal
		remittance={selectedRemittance}
		onClose={closeModal}
		onSubmit={handleMarkAsPaid}
	/>
{/if}
