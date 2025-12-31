<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import type { Employee } from '$lib/types/employee';
	import type { CompensationHistory } from '$lib/types/compensation';
	import { getEmployee } from '$lib/services/employeeService';
	import {
		getCompensationHistory,
		getCurrentCompensation
	} from '$lib/services/compensationService';
	import { formatShortDate, getCurrentDate } from '$lib/utils/dateUtils';
	import CompensationAdjustModal from '$lib/components/employees/CompensationAdjustModal.svelte';

	// Get employee ID from route params
	const employeeId = $derived($page.params.id);

	// State
	let employee = $state<Employee | null>(null);
	let currentCompensation = $state<CompensationHistory | null>(null);
	let history = $state<CompensationHistory[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let showAdjustModal = $state(false);

	// Load data on mount
	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		isLoading = true;
		error = null;

		const id = employeeId;
		if (!id) {
			error = 'Employee ID is required';
			isLoading = false;
			return;
		}

		try {
			// Load employee and compensation data in parallel
			const [employeeResult, currentResult, historyResult] = await Promise.all([
				getEmployee(id),
				getCurrentCompensation(id),
				getCompensationHistory(id)
			]);

			if (employeeResult.error) {
				error = employeeResult.error;
				return;
			}

			if (!employeeResult.data) {
				error = 'Employee not found';
				return;
			}

			// Check for compensation data errors
			if (currentResult.error) {
				error = `Failed to load current compensation: ${currentResult.error.message}`;
				return;
			}

			if (historyResult.error) {
				error = `Failed to load compensation history: ${historyResult.error.message}`;
				return;
			}

			employee = employeeResult.data;
			currentCompensation = currentResult.data;
			history = historyResult.data || [];
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load data';
		} finally {
			isLoading = false;
		}
	}

	// Handle back navigation
	function handleBack() {
		goto('/employees');
	}

	// Format currency
	function formatCurrency(amount: number | null | undefined): string {
		if (amount == null) return '-';
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			maximumFractionDigits: 2
		}).format(amount);
	}

	// Format compensation display
	function formatCompensation(comp: CompensationHistory): string {
		if (comp.compensationType === 'hourly' && comp.hourlyRate != null) {
			return `${formatCurrency(comp.hourlyRate)}/hr`;
		}
		if (comp.compensationType === 'salary' && comp.annualSalary != null) {
			return `${formatCurrency(comp.annualSalary)}/yr`;
		}
		return '-';
	}

	// Get compensation type label
	function getCompensationTypeLabel(type: 'salary' | 'hourly'): string {
		return type === 'salary' ? 'Salaried' : 'Hourly';
	}

	// Get full name
	function getFullName(emp: Employee): string {
		return `${emp.firstName} ${emp.lastName}`;
	}

	// Handle successful adjustment
	async function handleAdjustSuccess() {
		showAdjustModal = false;
		await loadData();
	}
</script>

<svelte:head>
	<title>
		{employee ? `${getFullName(employee)} - Compensation` : 'Compensation History'} - BeanFlow
		Payroll
	</title>
</svelte:head>

<div class="compensation-page">
	{#if isLoading}
		<!-- Loading State -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading compensation history...</p>
		</div>
	{:else if error && !employee}
		<!-- Error State -->
		<div class="error-state">
			<i class="fas fa-exclamation-triangle"></i>
			<h2>Error</h2>
			<p>{error}</p>
			<button class="btn-primary" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				Back to Employees
			</button>
		</div>
	{:else if employee}
		<!-- Header -->
		<header class="page-header">
			<button class="back-btn" onclick={handleBack} aria-label="Back to employees">
				<i class="fas fa-arrow-left"></i>
			</button>
			<div class="header-content">
				<h1>{getFullName(employee)}</h1>
				<p class="header-subtitle">Compensation History</p>
			</div>
		</header>

		<!-- Error Banner -->
		{#if error}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button class="error-dismiss" onclick={() => (error = null)} aria-label="Dismiss error">
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Current Compensation Card -->
		<section class="current-compensation-card">
			<div class="card-header">
				<h2>Current Compensation</h2>
				<button class="btn-adjust" onclick={() => (showAdjustModal = true)}>
					<i class="fas fa-edit"></i>
					Adjust Salary
				</button>
			</div>

			{#if currentCompensation}
				<div class="compensation-details">
					<div class="detail-row">
						<span class="detail-label">Type</span>
						<span class="detail-value">
							{getCompensationTypeLabel(currentCompensation.compensationType)}
						</span>
					</div>
					<div class="detail-row highlight">
						<span class="detail-label">
							{currentCompensation.compensationType === 'hourly'
								? 'Hourly Rate'
								: 'Annual Salary'}
						</span>
						<span class="detail-value amount">
							{formatCompensation(currentCompensation)}
						</span>
					</div>
					<div class="detail-row">
						<span class="detail-label">Effective Since</span>
						<span class="detail-value">
							{formatShortDate(currentCompensation.effectiveDate)}
						</span>
					</div>
					{#if currentCompensation.changeReason}
						<div class="detail-row">
							<span class="detail-label">Reason</span>
							<span class="detail-value">{currentCompensation.changeReason}</span>
						</div>
					{/if}
				</div>
			{:else}
				<div class="no-data">
					<p>No compensation record found.</p>
					<button class="btn-primary" onclick={() => (showAdjustModal = true)}>
						<i class="fas fa-plus"></i>
						Add Compensation
					</button>
				</div>
			{/if}
		</section>

		<!-- History Section -->
		<section class="history-section">
			<h2>History</h2>

			{#if history.length > 0}
				<div class="history-table-container">
					<table class="history-table">
						<thead>
							<tr>
								<th>Effective Date</th>
								<th>Type</th>
								<th>Amount</th>
								<th>Reason</th>
								<th>End Date</th>
							</tr>
						</thead>
						<tbody>
							{#each history as record (record.id)}
								<tr class:current={!record.endDate}>
									<td>{formatShortDate(record.effectiveDate)}</td>
									<td>{getCompensationTypeLabel(record.compensationType)}</td>
									<td class="amount">{formatCompensation(record)}</td>
									<td class="reason">{record.changeReason || '-'}</td>
									<td>
										{#if record.endDate}
											{formatShortDate(record.endDate)}
										{:else}
											<span class="current-badge">Current</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="empty-history">
					<i class="fas fa-history"></i>
					<p>No compensation history available.</p>
				</div>
			{/if}
		</section>
	{/if}
</div>

<!-- Adjust Compensation Modal -->
{#if showAdjustModal && employee}
	<CompensationAdjustModal
		{employee}
		currentCompensation={currentCompensation}
		onClose={() => (showAdjustModal = false)}
		onSuccess={handleAdjustSuccess}
	/>
{/if}

<style>
	.compensation-page {
		max-width: 900px;
		margin: 0 auto;
		padding: var(--spacing-6);
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.back-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border: none;
		background: var(--color-surface-100);
		color: var(--color-surface-600);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
		flex-shrink: 0;
	}

	.back-btn:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-800);
	}

	.header-content {
		flex: 1;
	}

	.header-content h1 {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.header-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		margin: var(--spacing-1) 0 0;
	}

	/* Error Banner */
	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-error-50, #fef2f2);
		border: 1px solid var(--color-error-200, #fecaca);
		border-radius: var(--radius-lg);
		color: var(--color-error-700, #b91c1c);
		margin-bottom: var(--spacing-4);
	}

	.error-banner i:first-child {
		font-size: 1.25rem;
	}

	.error-banner span {
		flex: 1;
	}

	.error-dismiss {
		background: none;
		border: none;
		color: var(--color-error-500, #ef4444);
		cursor: pointer;
		padding: var(--spacing-1);
		opacity: 0.7;
	}

	.error-dismiss:hover {
		opacity: 1;
	}

	/* Current Compensation Card */
	.current-compensation-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-5);
		margin-bottom: var(--spacing-6);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-4);
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.card-header h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.btn-adjust {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-adjust:hover {
		opacity: 0.9;
	}

	.compensation-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2) 0;
	}

	.detail-row.highlight {
		background: var(--color-primary-50);
		padding: var(--spacing-3) var(--spacing-4);
		border-radius: var(--radius-lg);
		margin: var(--spacing-2) 0;
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

	.detail-value.amount {
		font-size: var(--font-size-title-medium);
		color: var(--color-primary-600);
		font-weight: var(--font-weight-semibold);
	}

	.no-data {
		text-align: center;
		padding: var(--spacing-6);
		color: var(--color-surface-500);
	}

	.no-data p {
		margin: 0 0 var(--spacing-4);
	}

	/* History Section */
	.history-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-5);
	}

	.history-section h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4);
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-table-container {
		overflow-x: auto;
	}

	.history-table {
		width: 100%;
		border-collapse: collapse;
	}

	.history-table th {
		text-align: left;
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.history-table td {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-table tr:last-child td {
		border-bottom: none;
	}

	.history-table tr.current {
		background: var(--color-primary-50);
	}

	.history-table td.amount {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.history-table td.reason {
		color: var(--color-surface-500);
		font-style: italic;
	}

	.current-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-success-100);
		color: var(--color-success-700);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-full);
	}

	.empty-history {
		text-align: center;
		padding: var(--spacing-8);
		color: var(--color-surface-400);
	}

	.empty-history i {
		font-size: 48px;
		margin-bottom: var(--spacing-4);
	}

	.empty-history p {
		margin: 0;
		font-size: var(--font-size-body-content);
	}

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		gap: var(--spacing-4);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-container p {
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
		gap: var(--spacing-4);
	}

	.error-state i {
		font-size: 48px;
		color: var(--color-surface-400);
	}

	.error-state h2 {
		font-size: var(--font-size-title-large);
		color: var(--color-surface-800);
		margin: 0;
	}

	.error-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.compensation-page {
			padding: var(--spacing-4);
		}

		.card-header {
			flex-direction: column;
			gap: var(--spacing-3);
			align-items: flex-start;
		}

		.btn-adjust {
			width: 100%;
			justify-content: center;
		}

		.history-table th,
		.history-table td {
			padding: var(--spacing-2) var(--spacing-3);
			font-size: var(--font-size-body-small);
		}
	}
</style>
