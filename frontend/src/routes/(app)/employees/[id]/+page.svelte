<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import type { Employee } from '$lib/types/employee';
	import { getEmployee, deleteEmployee } from '$lib/services/employeeService';
	import EmployeeForm from '$lib/components/employees/EmployeeForm.svelte';

	// Get employee ID from route params
	const employeeId = $derived($page.params.id);

	// State
	let employee = $state<Employee | null>(null);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let isSaving = $state(false);
	let isDeleting = $state(false);
	let showDeleteConfirm = $state(false);

	// Load data on mount
	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		isLoading = true;
		error = null;

		try {
			// Validate employeeId
			if (!employeeId) {
				error = 'Employee ID is required';
				isLoading = false;
				return;
			}

			const employeeResult = await getEmployee(employeeId);

			if (employeeResult.error) {
				error = employeeResult.error;
				return;
			}

			if (!employeeResult.data) {
				error = 'Employee not found';
				return;
			}

			employee = employeeResult.data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load employee';
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

	// Handle successful update
	function handleSuccess(updatedEmployee: Employee) {
		employee = updatedEmployee;
		// Show success toast or notification
		goto('/employees');
	}

	// Handle save button click
	function handleSave() {
		const form = document.querySelector('.employee-form') as HTMLFormElement;
		if (form) {
			form.requestSubmit();
		}
	}

	// Handle delete
	async function handleDelete() {
		if (!employee) return;

		isDeleting = true;
		try {
			const result = await deleteEmployee(employee.id);
			if (result.error) {
				error = result.error;
				return;
			}
			goto('/employees');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete employee';
		} finally {
			isDeleting = false;
			showDeleteConfirm = false;
		}
	}

	// Get full name
	function getFullName(emp: Employee): string {
		return `${emp.firstName} ${emp.lastName}`;
	}
</script>

<svelte:head>
	<title>{employee ? getFullName(employee) : 'Employee'} - BeanFlow Payroll</title>
</svelte:head>

<div class="employee-detail-page">
	{#if isLoading}
		<!-- Loading State -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading employee...</p>
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
				<p class="header-subtitle">
					{#if employee.status === 'terminated'}
						<span class="status-badge terminated">Terminated</span>
					{:else if employee.status === 'draft'}
						<span class="status-badge draft">Draft</span>
					{:else}
						<span class="status-badge active">Active</span>
					{/if}
					Employee ID: {employee.id.slice(0, 8)}...
				</p>
			</div>
			<div class="header-actions">
				{#if employee.status === 'draft'}
					<button class="btn-delete" onclick={() => showDeleteConfirm = true} disabled={isDeleting}>
						<i class="fas fa-trash-alt"></i>
						Delete
					</button>
				{/if}
			</div>
		</header>

		<!-- Error Banner -->
		{#if error}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button class="error-dismiss" onclick={() => error = null} aria-label="Dismiss error">
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Form -->
		<div class="form-container">
			<EmployeeForm
				{employee}
				mode="edit"
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
						<span>Saving...</span>
					{:else}
						<i class="fas fa-check"></i>
						<span>Save Changes</span>
					{/if}
				</button>
			</div>
		</div>

		<!-- Delete Confirmation Modal -->
		{#if showDeleteConfirm}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<div class="modal-overlay" onclick={() => showDeleteConfirm = false} onkeydown={(e) => e.key === 'Escape' && (showDeleteConfirm = false)} role="dialog" aria-modal="true" aria-labelledby="delete-modal-title">
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div class="modal-content" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()}>
					<h3 id="delete-modal-title">Delete Employee?</h3>
					<p>Are you sure you want to delete <strong>{getFullName(employee)}</strong>? This action cannot be undone.</p>
					<div class="modal-actions">
						<button class="btn-cancel" onclick={() => showDeleteConfirm = false} disabled={isDeleting}>
							Cancel
						</button>
						<button class="btn-danger" onclick={handleDelete} disabled={isDeleting}>
							{#if isDeleting}
								<i class="fas fa-spinner fa-spin"></i>
								Deleting...
							{:else}
								Delete Employee
							{/if}
						</button>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.employee-detail-page {
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
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-badge.terminated {
		background: var(--color-surface-200);
		color: var(--color-surface-600);
	}

	.header-actions {
		display: flex;
		gap: var(--spacing-2);
	}

	.btn-delete {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: white;
		color: var(--color-error-600);
		border: 1px solid var(--color-error-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-delete:hover:not(:disabled) {
		background: var(--color-error-50);
		border-color: var(--color-error-400);
	}

	.btn-delete:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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

	/* Delete Confirmation Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-6);
		max-width: 400px;
		width: 90%;
		box-shadow: var(--shadow-lg);
	}

	.modal-content h3 {
		font-size: var(--font-size-title-medium);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	.modal-content p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-5);
	}

	.modal-actions {
		display: flex;
		gap: var(--spacing-3);
		justify-content: flex-end;
	}

	.btn-danger {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: var(--color-error-600);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-danger:hover:not(:disabled) {
		background: var(--color-error-700);
	}

	.btn-danger:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.employee-detail-page {
			padding: var(--spacing-4);
			padding-bottom: 100px;
		}

		.page-header {
			flex-wrap: wrap;
		}

		.header-actions {
			width: 100%;
			margin-top: var(--spacing-3);
		}

		.action-bar-content {
			flex-direction: column;
		}

		.btn-cancel,
		.btn-save {
			width: 100%;
		}

		.modal-actions {
			flex-direction: column-reverse;
		}

		.modal-actions button {
			width: 100%;
		}
	}
</style>
