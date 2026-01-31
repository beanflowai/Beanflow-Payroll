<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Employee } from '$lib/types/employee';
	import EmployeeForm from '$lib/components/employees/EmployeeForm.svelte';
	import { markStepComplete } from '$lib/stores/onboarding.svelte';

	// State
	let formRef = $state<EmployeeForm | null>(null);
	let isSaving = $state(false);

	// Sync isSaving with form's isSubmitting state
	let formIsSubmitting = $state(false);
	$effect(() => {
		isSaving = formIsSubmitting;
	});

	// Handle back navigation
	function handleBack() {
		goto('/employees');
	}

	// Handle cancel
	function handleCancel() {
		goto('/employees');
	}

	// Handle successful creation
	async function handleSuccess(employee: Employee, action: 'save' | 'saveAndNew' = 'save') {
		// Mark onboarding steps as complete
		await markStepComplete('employees');
		if (employee.payGroupId) {
			await markStepComplete('employee_assignment');
		}
		if (action === 'saveAndNew') {
			// Stay on new employee page for adding more employees
			// Trigger a page reload to reset the form
			location.reload();
		} else {
			// Go to employee list
			goto('/employees');
		}
	}

	// Handle save button click
	function handleSave() {
		// Set action to 'save' and trigger form submission
		const form = document.querySelector('.employee-form') as HTMLFormElement;
		if (form) {
			(form as any)._submitAction = 'save';
			form.requestSubmit();
		}
	}

	// Handle save & new button click
	function handleSaveAndNew() {
		// Set action to 'saveAndNew' and trigger form submission
		const form = document.querySelector('.employee-form') as HTMLFormElement;
		if (form) {
			(form as any)._submitAction = 'saveAndNew';
			form.requestSubmit();
		}
	}
</script>

<svelte:head>
	<title>New Employee - BeanFlow Payroll</title>
</svelte:head>

<div class="employee-new-page">
	<!-- Header -->
	<header class="page-header">
		<button class="back-btn" onclick={handleBack} aria-label="Back to employees">
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
			mode="create"
			bind:isSubmitting={formIsSubmitting}
			onSuccess={handleSuccess}
			onCancel={handleCancel}
		/>
	</div>

	<!-- Bottom Action Bar -->
	<div class="action-bar">
		<div class="action-bar-content">
			<button class="btn-cancel" onclick={handleCancel} disabled={isSaving}> Cancel </button>
			<button class="btn-save-and-new" onclick={handleSaveAndNew} disabled={isSaving}>
				{#if isSaving}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Creating...</span>
				{:else}
					<i class="fas fa-plus"></i>
					<span>Save & New</span>
				{/if}
			</button>
			<button class="btn-save" onclick={handleSave} disabled={isSaving}>
				{#if isSaving}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Creating...</span>
				{:else}
					<i class="fas fa-check"></i>
					<span>Save</span>
				{/if}
			</button>
		</div>
	</div>
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
	.btn-save,
	.btn-save-and-new {
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

	.btn-save-and-new {
		background: white;
		color: var(--color-primary-600);
		border: 1px solid var(--color-primary-300);
	}

	.btn-save-and-new:hover:not(:disabled) {
		background: var(--color-primary-50);
		border-color: var(--color-primary-400);
	}

	.btn-save-and-new:disabled {
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
		.btn-save,
		.btn-save-and-new {
			width: 100%;
		}
	}
</style>
