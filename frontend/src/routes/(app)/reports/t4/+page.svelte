<script lang="ts">
	import { T4_STATUS_INFO, getAvailableTaxYears } from '$lib/types/t4';
	import type { T4SlipSummary, T4SummaryData } from '$lib/types/t4';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';
	import { companyState } from '$lib/stores/company.svelte';
	import {
		listT4Slips,
		generateT4Slips,
		downloadT4Slip,
		getT4Summary,
		generateT4Summary,
		downloadT4SummaryPdf,
		downloadT4Xml
	} from '$lib/services/t4Service';
	import T4SubmissionModal from '$lib/components/t4/T4SubmissionModal.svelte';
	import { TableSkeleton, AlertBanner } from '$lib/components/shared';

	// State
	let selectedYear = $state(new Date().getFullYear() - 1); // Default to previous year for T4
	let slips = $state<T4SlipSummary[]>([]);
	let summary = $state<T4SummaryData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Current company derived from store
	const currentCompany = $derived(companyState.currentCompany);

	// Operation states
	let generating = $state(false);
	let generatingSummary = $state(false);
	let downloadingSlipId = $state<string | null>(null);
	let downloadingSummaryPdf = $state(false);
	let downloadingXml = $state(false);

	// Submission modal state
	let showSubmissionModal = $state(false);

	// Available tax years
	const taxYears = getAvailableTaxYears();

	// Computed: check if we have generated slips
	let hasSlips = $derived(slips.length > 0);
	let generatedCount = $derived(slips.filter((s) => s.status !== 'draft').length);

	// Load data
	async function loadData(companyId: string, year: number) {
		loading = true;
		error = null;

		try {
			// Load T4 slips
			const slipsResult = await listT4Slips(companyId, year);
			if (slipsResult.error) {
				error = slipsResult.error;
				return;
			}
			slips = slipsResult.data?.slips ?? [];

			// Load T4 Summary
			const summaryResult = await getT4Summary(companyId, year);
			if (summaryResult.error) {
				error = summaryResult.error;
				return;
			}
			summary = summaryResult.data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load T4 data';
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

	// Generate T4 slips
	async function handleGenerateSlips(regenerate: boolean = false) {
		if (!currentCompany) return;

		generating = true;
		try {
			const result = await generateT4Slips(currentCompany.id, selectedYear, { regenerate });
			if (result.error) {
				error = result.error;
				return;
			}

			// Reload data first
			await loadData(currentCompany.id, selectedYear);

			// Then set any error/warning messages (after loadData clears error)
			if (result.data) {
				if (result.data.slipsGenerated === 0 && result.data.errors.length === 0) {
					// Show message when no payroll data found
					error = result.data.message || `No payroll data found for ${selectedYear}`;
				} else if (result.data.errors.length > 0) {
					error = `Generated ${result.data.slipsGenerated} slips with ${result.data.errors.length} errors`;
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate T4 slips';
		} finally {
			generating = false;
		}
	}

	// Generate T4 Summary
	async function handleGenerateSummary() {
		if (!currentCompany) return;

		generatingSummary = true;
		try {
			const result = await generateT4Summary(currentCompany.id, selectedYear);
			if (result.error) {
				error = result.error;
				return;
			}

			// Reload data
			await loadData(currentCompany.id, selectedYear);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate T4 Summary';
		} finally {
			generatingSummary = false;
		}
	}

	// Download individual T4 slip
	async function handleDownloadSlip(slip: T4SlipSummary) {
		if (!currentCompany) return;

		downloadingSlipId = slip.id;
		try {
			const result = await downloadT4Slip(currentCompany.id, selectedYear, slip.employeeId);
			if (result.error) {
				error = result.error;
			}
		} finally {
			downloadingSlipId = null;
		}
	}

	// Download T4 Summary PDF
	async function handleDownloadSummaryPdf() {
		if (!currentCompany) return;

		downloadingSummaryPdf = true;
		try {
			const result = await downloadT4SummaryPdf(currentCompany.id, selectedYear);
			if (result.error) {
				error = result.error;
			}
		} finally {
			downloadingSummaryPdf = false;
		}
	}

	// Download T4 XML
	async function handleDownloadXml() {
		if (!currentCompany) return;

		downloadingXml = true;
		try {
			const result = await downloadT4Xml(currentCompany.id, selectedYear);
			if (result.error) {
				error = result.error;
			}
		} finally {
			downloadingXml = false;
		}
	}

	// Open submission modal
	function handleOpenSubmissionModal() {
		showSubmissionModal = true;
	}

	// Handle submission complete
	function handleSubmissionComplete(updatedSummary: T4SummaryData) {
		summary = updatedSummary;
	}
</script>

<svelte:head>
	<title>T4 Management - BeanFlow Payroll</title>
</svelte:head>

<div class="max-w-[1000px] mx-auto">
	<header class="flex justify-between items-start mb-6 max-md:flex-col max-md:gap-4">
		<div>
			<div class="flex items-center gap-3 mb-1">
				<a
					href="/reports"
					class="text-surface-500 hover:text-surface-700 transition-colors"
					aria-label="Back to reports"
				>
					<i class="fas fa-arrow-left"></i>
				</a>
				<h1 class="text-headline-minimum font-semibold text-surface-800 m-0">
					T4 Year-End Processing
				</h1>
			</div>
			<p class="text-body-content text-surface-600 m-0 ml-8">
				Generate T4 slips and summary for CRA year-end reporting
			</p>
		</div>

		<!-- Year Selector -->
		<div class="flex items-center gap-3">
			<label for="tax-year" class="text-body-content text-surface-600">Tax Year:</label>
			<select
				id="tax-year"
				bind:value={selectedYear}
				class="px-4 py-2 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
			>
				{#each taxYears as year (year)}
					<option value={year}>{year}</option>
				{/each}
			</select>
		</div>
	</header>

	{#if loading}
		<TableSkeleton rows={5} columns={4} />
	{:else if error}
		<AlertBanner
			type="error"
			title="Error"
			message={error}
			dismissible
			onDismiss={() => (error = null)}
		/>
	{/if}

	{#if !loading}
		<!-- T4 Generation Section -->
		<div class="bg-white rounded-xl shadow-md3-2 p-6 mb-6">
			<div class="flex justify-between items-start mb-4 max-md:flex-col max-md:gap-4">
				<div>
					<h2 class="text-title-medium font-semibold text-surface-800 m-0 mb-1">T4 Slips</h2>
					<p class="text-body-content text-surface-500 m-0">
						{#if hasSlips}
							{slips.length} employee(s) • {generatedCount} generated
						{:else}
							No T4 slips generated for {selectedYear}
						{/if}
					</p>
				</div>
				<div class="flex gap-2">
					{#if hasSlips}
						<button
							class="inline-flex items-center gap-2 px-4 py-2 bg-surface-100 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-200 disabled:opacity-50 disabled:cursor-not-allowed"
							onclick={() => handleGenerateSlips(true)}
							disabled={generating}
						>
							{#if generating}
								<i class="fas fa-spinner fa-spin"></i>
								<span>Regenerating...</span>
							{:else}
								<i class="fas fa-sync-alt"></i>
								<span>Regenerate All</span>
							{/if}
						</button>
					{/if}
					<button
						class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all hover:opacity-90 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed"
						onclick={() => handleGenerateSlips(false)}
						disabled={generating}
					>
						{#if generating}
							<i class="fas fa-spinner fa-spin"></i>
							<span>Generating...</span>
						{:else}
							<i class="fas fa-file-alt"></i>
							<span>Generate T4 Slips</span>
						{/if}
					</button>
				</div>
			</div>

			<!-- T4 Slips Table -->
			{#if hasSlips}
				<div class="overflow-x-auto -mx-6 px-6">
					<table class="w-full border-collapse">
						<thead>
							<tr>
								<th
									class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									Employee
								</th>
								<th
									class="px-4 py-3 text-left text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									SIN
								</th>
								<th
									class="px-4 py-3 text-right text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									Employment Income
								</th>
								<th
									class="px-4 py-3 text-right text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									Tax Deducted
								</th>
								<th
									class="px-4 py-3 text-center text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									Status
								</th>
								<th
									class="px-4 py-3 text-center text-body-content bg-surface-50 text-surface-600 font-medium border-b border-surface-100"
								>
									Actions
								</th>
							</tr>
						</thead>
						<tbody>
							{#each slips as slip (slip.id)}
								{@const statusInfo = T4_STATUS_INFO[slip.status]}
								<tr class="hover:bg-surface-50 transition-colors">
									<td
										class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-800 font-medium"
									>
										{slip.employeeName}
									</td>
									<td
										class="px-4 py-3 text-left text-body-content border-b border-surface-100 text-surface-600 font-mono"
									>
										{slip.sinMasked}
									</td>
									<td
										class="px-4 py-3 text-right text-body-content border-b border-surface-100 text-surface-800"
									>
										{formatCurrency(slip.box14EmploymentIncome)}
									</td>
									<td
										class="px-4 py-3 text-right text-body-content border-b border-surface-100 text-surface-800"
									>
										{formatCurrency(slip.box22IncomeTaxDeducted)}
									</td>
									<td class="px-4 py-3 text-center text-body-content border-b border-surface-100">
										<span
											class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-auxiliary-text font-medium {statusInfo.colorClass}"
										>
											<i class="fas fa-{statusInfo.icon}"></i>
											{statusInfo.label}
										</span>
									</td>
									<td class="px-4 py-3 text-center text-body-content border-b border-surface-100">
										<button
											class="w-8 h-8 border-none bg-transparent text-surface-500 cursor-pointer rounded-md transition-colors hover:bg-surface-100 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
											title="Download T4 PDF"
											onclick={() => handleDownloadSlip(slip)}
											disabled={downloadingSlipId === slip.id || !slip.pdfAvailable}
										>
											{#if downloadingSlipId === slip.id}
												<i class="fas fa-spinner fa-spin"></i>
											{:else}
												<i class="fas fa-file-pdf"></i>
											{/if}
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="py-8 text-center">
					<i class="fas fa-file-alt text-4xl text-surface-300 mb-4"></i>
					<p class="text-body-content text-surface-500 m-0">
						Click "Generate T4 Slips" to create T4s for all employees with earnings in {selectedYear}
					</p>
				</div>
			{/if}
		</div>

		<!-- T4 Summary Section -->
		<div class="bg-white rounded-xl shadow-md3-2 p-6">
			<div class="flex justify-between items-start mb-4 max-md:flex-col max-md:gap-4">
				<div>
					<h2 class="text-title-medium font-semibold text-surface-800 m-0 mb-1">T4 Summary</h2>
					<p class="text-body-content text-surface-500 m-0">
						{#if summary}
							Generated {summary.generatedAt ? formatShortDate(summary.generatedAt) : 'N/A'}
						{:else}
							Generate after all T4 slips are ready
						{/if}
					</p>
				</div>
				<div class="flex gap-2 flex-wrap">
					{#if summary}
						<button
							class="inline-flex items-center gap-2 px-4 py-2 bg-surface-100 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-200 disabled:opacity-50 disabled:cursor-not-allowed"
							onclick={handleDownloadSummaryPdf}
							disabled={downloadingSummaryPdf}
						>
							{#if downloadingSummaryPdf}
								<i class="fas fa-spinner fa-spin"></i>
							{:else}
								<i class="fas fa-file-pdf"></i>
							{/if}
							<span>Download PDF</span>
						</button>
						<button
							class="inline-flex items-center gap-2 px-4 py-2 bg-surface-100 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-200 disabled:opacity-50 disabled:cursor-not-allowed"
							onclick={handleDownloadXml}
							disabled={downloadingXml}
						>
							{#if downloadingXml}
								<i class="fas fa-spinner fa-spin"></i>
							{:else}
								<i class="fas fa-file-code"></i>
							{/if}
							<span>Download XML</span>
						</button>
						{#if summary.status === 'generated'}
							<button
								class="inline-flex items-center gap-2 px-4 py-2 bg-success-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-success-700"
								onclick={handleOpenSubmissionModal}
							>
								<i class="fas fa-paper-plane"></i>
								<span>Submit to CRA</span>
							</button>
						{/if}
					{/if}
					{#if !summary || summary.status !== 'filed'}
						<button
							class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all hover:opacity-90 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed"
							onclick={handleGenerateSummary}
							disabled={generatingSummary || !hasSlips}
						>
							{#if generatingSummary}
								<i class="fas fa-spinner fa-spin"></i>
								<span>Generating...</span>
							{:else}
								<i class="fas fa-calculator"></i>
								<span>{summary ? 'Regenerate Summary' : 'Generate Summary'}</span>
							{/if}
						</button>
					{/if}
				</div>
			</div>

			{#if summary}
				<!-- Summary Totals -->
				<div class="grid grid-cols-4 gap-4 mb-6 max-md:grid-cols-2 max-sm:grid-cols-1">
					<div class="bg-surface-50 rounded-lg p-4">
						<span class="block text-auxiliary-text text-surface-500 mb-1">Total T4 Slips</span>
						<span class="block text-title-large font-semibold text-surface-800">
							{summary.totalNumberOfT4Slips}
						</span>
					</div>
					<div class="bg-surface-50 rounded-lg p-4">
						<span class="block text-auxiliary-text text-surface-500 mb-1">
							Total Employment Income
						</span>
						<span class="block text-title-large font-semibold text-surface-800">
							{formatCurrency(summary.totalEmploymentIncome)}
						</span>
					</div>
					<div class="bg-surface-50 rounded-lg p-4">
						<span class="block text-auxiliary-text text-surface-500 mb-1">Total Tax Deducted</span>
						<span class="block text-title-large font-semibold text-surface-800">
							{formatCurrency(summary.totalIncomeTaxDeducted)}
						</span>
					</div>
					<div class="bg-surface-50 rounded-lg p-4">
						<span class="block text-auxiliary-text text-surface-500 mb-1">Status</span>
						<span
							class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-auxiliary-text font-medium {T4_STATUS_INFO[
								summary.status
							].colorClass}"
						>
							<i class="fas fa-{T4_STATUS_INFO[summary.status].icon}"></i>
							{T4_STATUS_INFO[summary.status].label}
						</span>
						{#if summary.status === 'filed' && summary.craConfirmationNumber}
							<div class="mt-2">
								<span class="text-auxiliary-text text-surface-500">Confirmation: </span>
								<span class="text-auxiliary-text font-mono text-surface-800"
									>{summary.craConfirmationNumber}</span
								>
							</div>
						{/if}
					</div>
				</div>

				<!-- Detailed Breakdown -->
				<div class="bg-surface-50 rounded-lg p-4">
					<h3 class="text-body-content font-semibold text-surface-800 m-0 mb-4">
						Deduction Breakdown
					</h3>
					<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
						<div class="space-y-2">
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">CPP Contributions (Employee)</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalCppContributions)}
								</span>
							</div>
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">CPP2 Contributions</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalCpp2Contributions)}
								</span>
							</div>
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">CPP (Employer)</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalCppEmployer)}
								</span>
							</div>
						</div>
						<div class="space-y-2">
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">EI Premiums (Employee)</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalEiPremiums)}
								</span>
							</div>
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">EI (Employer)</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalEiEmployer)}
								</span>
							</div>
							<div class="flex justify-between text-body-content">
								<span class="text-surface-600">Union Dues</span>
								<span class="text-surface-800 font-medium">
									{formatCurrency(summary.totalUnionDues)}
								</span>
							</div>
						</div>
					</div>

					{#if summary.remittanceDifference !== 0}
						<div
							class="mt-4 pt-4 border-t border-surface-200 flex justify-between text-body-content"
						>
							<span class="text-surface-600">Remittance Difference</span>
							<span
								class="font-semibold {summary.remittanceDifference > 0
									? 'text-error-600'
									: 'text-success-600'}"
							>
								{formatCurrency(summary.remittanceDifference)}
							</span>
						</div>
					{/if}
				</div>
			{:else}
				<div class="py-8 text-center">
					<i class="fas fa-calculator text-4xl text-surface-300 mb-4"></i>
					<p class="text-body-content text-surface-500 m-0">
						{#if hasSlips}
							Click "Generate Summary" to create the T4 Summary for CRA submission
						{:else}
							Generate T4 slips first, then create the summary
						{/if}
					</p>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Submission Modal -->
{#if currentCompany}
	<T4SubmissionModal
		companyId={currentCompany.id}
		taxYear={selectedYear}
		isOpen={showSubmissionModal}
		onClose={() => (showSubmissionModal = false)}
		onSubmissionComplete={handleSubmissionComplete}
	/>
{/if}
