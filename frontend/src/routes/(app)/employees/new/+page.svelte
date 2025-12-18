<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { PayGroup } from '$lib/types/pay-group';
	import type { Employee } from '$lib/types/employee';
	import { listPayGroups } from '$lib/services/payGroupService';
	import EmployeeForm from '$lib/components/employees/EmployeeForm.svelte';

	// State
	let payGroups = $state<PayGroup[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let formRef = $state<EmployeeForm | null>(null);
	let isSaving = $state(false);

	// Load pay groups on mount
	onMount(async () => {
		await loadPayGroups();
	});

	async function loadPayGroups() {
		isLoading = true;
		error = null;

		try {
			const result = await listPayGroups();
			if (result.error) {
				error = result.error;
				return;
			}
			payGroups = result.data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load pay groups';
		} finally {
			isLoading = false;
		}
	}

	// Handle back navigation
	function handleBack() {
		goto('/employees');
	}

	// Handle cancel
	function handleCancel() {
		goto('/employees');
	}

	// Handle successful creation
	function handleSuccess(employee: Employee) {
		goto(`/employees/${employee.id}`);
	}

	// Handle save button click
	function handleSave() {
		// Trigger form submission
		const form = document.querySelector('.employee-form') as HTMLFormElement;
		if (form) {
			form.requestSubmit();
		}
	}
</script>

<svelte:head>
	<title>New Employee - BeanFlow Payroll</title>
</svelte:head>

<div class="employee-new-page">
	{#if isLoading}
		<!-- Loading State -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading...</p>
		</div>
	{:else if error && payGroups.length === 0}
		<!-- Error State -->
		<div class="error-state">
			<i class="fas fa-exclamation-triangle"></i>
			<h2>Error Loading Data</h2>
			<p>{error}</p>
			<button class="btn-primary" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				Back to Employees
			</button>
		</div>
	{:else if payGroups.length === 0}
		<!-- No Pay Groups State -->
		<div class="empty-state">
			<i class="fas fa-users-cog"></i>
			<h2>No Pay Groups Found</h2>
			<p>You need to create at least one pay group before adding employees.</p>
			<button class="btn-primary" onclick={() => goto('/company/pay-groups/new')}>
				<i class="fas fa-plus"></i>
				Create Pay Group
			</button>
		</div>
	{:else}
		<!-- Header -->
		<header class="page-header">
			<button class="back-btn" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
			</button>
			<div class="header-content">
				<h1>New Employee</h1>
				<p class="header-subtitle">Add a new employee to your payroll</p>
			</div>
		</header>

		<!-- Form -->
		<div class="form-container">
			<EmployeeForm
				bind:this={formRef}
				{payGroups}
				mode="create"
				onSuccess={handleSuccess}
				onCancel={handleCancel}
			/>
		</div>

		<!-- Bottom Action Bar -->
		<div class="action-bar">
			<div class="action-bar-content">
				<button class="btn-cancel" onclick={handleCancel} disabled={isSaving}>
					Cancel
				</button>
				<button class="btn-save" onclick={handleSave} disabled={isSaving}>
					{#if isSaving}
						<i class="fas fa-spinner fa-spin"></i>
						<span>Creating...</span>
					{:else}
						<i class="fas fa-check"></i>
						<span>Create Employee</span>
					{/if}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.employee-new-page {
		max-width: 900px;
		margin: 0 auto;
		padding: var(--spacing-6);
		padding-bottom: 100px; /* Space for action bar */
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
	}

	.back-btn:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-800);
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

	/* Form Container */
	.form-container {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	/* Action Bar */
	.action-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: white;
		border-top: 1px solid var(--color-surface-200);
		box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
		padding: var(--spacing-4) var(--spacing-6);
		z-index: 100;
	}

	.action-bar-content {
		max-width: 900px;
		margin: 0 auto;
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
	}

	.btn-cancel,
	.btn-save {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-6);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	.btn-cancel:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-save {
		background: var(--gradient-primary);
		color: white;
		border: none;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-save:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-save:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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
	.error-state,
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
		gap: var(--spacing-4);
	}

	.error-state i,
	.empty-state i {
		font-size: 48px;
		color: var(--color-surface-400);
	}

	.error-state h2,
	.empty-state h2 {
		font-size: var(--font-size-title-large);
		color: var(--color-surface-800);
		margin: 0;
	}

	.error-state p,
	.empty-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
		max-width: 400px;
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
		.employee-new-page {
			padding: var(--spacing-4);
			padding-bottom: 100px;
		}

		.action-bar-content {
			flex-direction: column;
		}

		.btn-cancel,
		.btn-save {
			width: 100%;
		}
	}
</style>
