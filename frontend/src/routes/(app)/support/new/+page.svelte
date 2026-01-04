<script lang="ts">
	import { goto } from '$app/navigation';
	import { companyState } from '$lib/stores/company.svelte';
	import {
		createTicket,
		uploadAttachment,
		getFileValidationError,
		formatFileSize
	} from '$lib/services/ticketService';
	import {
		TICKET_PRIORITY_INFO,
		type TicketPriority,
		type PendingAttachment
	} from '$lib/types/ticket';

	// Form state
	let title = $state('');
	let description = $state('');
	let priority = $state<TicketPriority>('normal');
	let pendingAttachments = $state<PendingAttachment[]>([]);

	// UI state
	let submitting = $state(false);
	let error = $state<string | null>(null);
	let dragOver = $state(false);

	// Priority options
	const priorityOptions: { value: TicketPriority; label: string; description: string }[] = [
		{ value: 'low', label: 'Low', description: 'Minor issue, no urgency' },
		{ value: 'normal', label: 'Normal', description: 'Standard request' },
		{ value: 'high', label: 'High', description: 'Important, needs attention soon' },
		{ value: 'urgent', label: 'Urgent', description: 'Critical issue, blocking work' }
	];

	// Form validation
	let isValid = $derived(title.trim().length > 0 && description.trim().length > 0);

	// Handle file selection
	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files) {
			addFiles(Array.from(input.files));
		}
		input.value = ''; // Reset for same file selection
	}

	// Handle drag and drop
	function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
		if (event.dataTransfer?.files) {
			addFiles(Array.from(event.dataTransfer.files));
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	// Add files to pending list
	function addFiles(files: File[]) {
		const maxAttachments = 5;
		const remaining = maxAttachments - pendingAttachments.length;

		if (remaining <= 0) {
			error = `Maximum ${maxAttachments} attachments allowed`;
			return;
		}

		const filesToAdd = files.slice(0, remaining);

		for (const file of filesToAdd) {
			const validationError = getFileValidationError(file);
			if (validationError) {
				pendingAttachments = [
					...pendingAttachments,
					{
						file,
						preview: '',
						error: validationError
					}
				];
			} else {
				// Create preview URL
				const preview = URL.createObjectURL(file);
				pendingAttachments = [
					...pendingAttachments,
					{
						file,
						preview
					}
				];
			}
		}

		if (files.length > remaining) {
			error = `Only ${remaining} more file(s) can be added`;
		}
	}

	// Remove pending attachment
	function removeAttachment(index: number) {
		const attachment = pendingAttachments[index];
		if (attachment.preview) {
			URL.revokeObjectURL(attachment.preview);
		}
		pendingAttachments = pendingAttachments.filter((_, i) => i !== index);
	}

	// Submit form
	async function handleSubmit() {
		if (!isValid || submitting) return;

		submitting = true;
		error = null;

		try {
			// Create the ticket
			const companyId = companyState.currentCompany?.id;
			const ticket = await createTicket(
				{
					title: title.trim(),
					description: description.trim(),
					priority
				},
				companyId
			);

			// Upload attachments (valid ones only)
			const validAttachments = pendingAttachments.filter((a) => !a.error);
			for (const attachment of validAttachments) {
				try {
					await uploadAttachment(ticket.id, attachment.file);
				} catch (uploadError) {
					console.error('Failed to upload attachment:', uploadError);
					// Continue with other attachments
				}
			}

			// Navigate to the new ticket
			goto(`/support/${ticket.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create ticket';
			submitting = false;
		}
	}

	// Cleanup previews on unmount
	$effect(() => {
		return () => {
			pendingAttachments.forEach((a) => {
				if (a.preview) URL.revokeObjectURL(a.preview);
			});
		};
	});
</script>

<div class="page-container">
	<!-- Header -->
	<div class="page-header">
		<a href="/support" class="back-link">
			<i class="fas fa-arrow-left"></i>
			Back to Tickets
		</a>
		<h1 class="page-title">New Support Ticket</h1>
		<p class="page-subtitle">Describe your issue and we'll help you as soon as possible</p>
	</div>

	<!-- Form -->
	<form
		class="ticket-form"
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
	>
		{#if error}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button
					type="button"
					class="close-btn"
					onclick={() => (error = null)}
					aria-label="Dismiss error"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Title -->
		<div class="form-group">
			<label for="title" class="form-label">
				Title <span class="required">*</span>
			</label>
			<input
				type="text"
				id="title"
				bind:value={title}
				class="form-input"
				placeholder="Brief summary of your issue"
				maxlength="200"
				required
			/>
			<span class="char-count">{title.length}/200</span>
		</div>

		<!-- Priority -->
		<div class="form-group">
			<span class="form-label">Priority</span>
			<div class="priority-options">
				{#each priorityOptions as option (option.value)}
					<label class="priority-option" class:selected={priority === option.value}>
						<input type="radio" name="priority" value={option.value} bind:group={priority} />
						<span class="priority-badge {TICKET_PRIORITY_INFO[option.value].colorClass}">
							<i class="fas {TICKET_PRIORITY_INFO[option.value].icon}"></i>
							{option.label}
						</span>
						<span class="priority-desc">{option.description}</span>
					</label>
				{/each}
			</div>
		</div>

		<!-- Description -->
		<div class="form-group">
			<label for="description" class="form-label">
				Description <span class="required">*</span>
			</label>
			<textarea
				id="description"
				bind:value={description}
				class="form-textarea"
				placeholder="Please provide as much detail as possible about your issue..."
				rows="6"
				maxlength="10000"
				required
			></textarea>
			<span class="char-count">{description.length}/10000</span>
		</div>

		<!-- Attachments -->
		<div class="form-group">
			<span class="form-label">
				Attachments
				<span class="optional">(optional, max 5 images)</span>
			</span>
			<div
				class="drop-zone"
				class:drag-over={dragOver}
				ondrop={handleDrop}
				ondragover={handleDragOver}
				ondragleave={handleDragLeave}
				role="button"
				tabindex="0"
			>
				<input
					type="file"
					id="file-input"
					accept="image/jpeg,image/png,image/gif,image/webp"
					multiple
					onchange={handleFileSelect}
					class="file-input"
				/>
				<label for="file-input" class="drop-zone-content">
					<i class="fas fa-cloud-upload-alt"></i>
					<span>Drop images here or click to browse</span>
					<span class="drop-zone-hint">JPEG, PNG, GIF, WebP up to 5MB each</span>
				</label>
			</div>

			{#if pendingAttachments.length > 0}
				<div class="attachments-preview">
					{#each pendingAttachments as attachment, index (index)}
						<div class="attachment-item" class:has-error={attachment.error}>
							{#if attachment.preview && !attachment.error}
								<img src={attachment.preview} alt={attachment.file.name} class="attachment-thumb" />
							{:else}
								<div class="attachment-thumb error-thumb">
									<i class="fas fa-exclamation-triangle"></i>
								</div>
							{/if}
							<div class="attachment-info">
								<span class="attachment-name">{attachment.file.name}</span>
								{#if attachment.error}
									<span class="attachment-error">{attachment.error}</span>
								{:else}
									<span class="attachment-size">{formatFileSize(attachment.file.size)}</span>
								{/if}
							</div>
							<button
								type="button"
								class="remove-btn"
								onclick={() => removeAttachment(index)}
								aria-label="Remove attachment"
							>
								<i class="fas fa-times"></i>
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Actions -->
		<div class="form-actions">
			<a href="/support" class="btn-secondary">Cancel</a>
			<button type="submit" class="btn-primary" disabled={!isValid || submitting}>
				{#if submitting}
					<i class="fas fa-spinner fa-spin"></i>
					Submitting...
				{:else}
					<i class="fas fa-paper-plane"></i>
					Submit Ticket
				{/if}
			</button>
		</div>
	</form>
</div>

<style>
	.page-container {
		max-width: 700px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		color: var(--color-surface-600);
		text-decoration: none;
		font-size: var(--font-size-body-small);
		margin-bottom: var(--spacing-3);
		transition: var(--transition-fast);
	}

	.back-link:hover {
		color: var(--color-primary-600);
	}

	.page-title {
		font-size: var(--font-size-headline-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-1) 0;
	}

	.page-subtitle {
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Form */
	.ticket-form {
		background: white;
		border-radius: var(--radius-xl);
		border: 1px solid var(--color-surface-200);
		padding: var(--spacing-6);
	}

	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-lg);
		color: var(--color-error-700);
		margin-bottom: var(--spacing-4);
	}

	.error-banner .close-btn {
		margin-left: auto;
		background: none;
		border: none;
		color: var(--color-error-500);
		cursor: pointer;
		padding: var(--spacing-1);
	}

	.form-group {
		margin-bottom: var(--spacing-5);
		position: relative;
	}

	.form-label {
		display: block;
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-2);
	}

	.required {
		color: var(--color-error-500);
	}

	.optional {
		font-weight: var(--font-weight-normal);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-small);
	}

	.form-input,
	.form-textarea {
		width: 100%;
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		transition: var(--transition-fast);
	}

	.form-input:focus,
	.form-textarea:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-textarea {
		resize: vertical;
		min-height: 120px;
	}

	.char-count {
		position: absolute;
		right: var(--spacing-2);
		bottom: calc(-1 * var(--spacing-4));
		font-size: var(--font-size-label-small);
		color: var(--color-surface-400);
	}

	/* Priority Options */
	.priority-options {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-2);
	}

	.priority-option {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		padding: var(--spacing-3);
		border: 2px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.priority-option:hover {
		border-color: var(--color-surface-300);
	}

	.priority-option.selected {
		border-color: var(--color-primary-500);
		background: var(--color-primary-50);
	}

	.priority-option input {
		display: none;
	}

	.priority-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-md);
		font-size: var(--font-size-label-small);
		font-weight: var(--font-weight-medium);
		width: fit-content;
	}

	.priority-desc {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Drop Zone */
	.drop-zone {
		position: relative;
		border: 2px dashed var(--color-surface-300);
		border-radius: var(--radius-lg);
		padding: var(--spacing-6);
		text-align: center;
		transition: var(--transition-fast);
	}

	.drop-zone.drag-over {
		border-color: var(--color-primary-500);
		background: var(--color-primary-50);
	}

	.file-input {
		position: absolute;
		inset: 0;
		opacity: 0;
		cursor: pointer;
	}

	.drop-zone-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-2);
		color: var(--color-surface-500);
		pointer-events: none;
	}

	.drop-zone-content i {
		font-size: 32px;
		color: var(--color-primary-400);
	}

	.drop-zone-hint {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-400);
	}

	/* Attachments Preview */
	.attachments-preview {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
		margin-top: var(--spacing-3);
	}

	.attachment-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
	}

	.attachment-item.has-error {
		background: var(--color-error-50);
	}

	.attachment-thumb {
		width: 48px;
		height: 48px;
		object-fit: cover;
		border-radius: var(--radius-md);
		flex-shrink: 0;
	}

	.error-thumb {
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-error-100);
		color: var(--color-error-500);
	}

	.attachment-info {
		flex: 1;
		min-width: 0;
	}

	.attachment-name {
		display: block;
		font-size: var(--font-size-body-small);
		color: var(--color-surface-800);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.attachment-size {
		font-size: var(--font-size-label-small);
		color: var(--color-surface-500);
	}

	.attachment-error {
		font-size: var(--font-size-label-small);
		color: var(--color-error-600);
	}

	.remove-btn {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: white;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-full);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
		flex-shrink: 0;
	}

	.remove-btn:hover {
		background: var(--color-error-50);
		border-color: var(--color-error-300);
		color: var(--color-error-600);
	}

	/* Actions */
	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		margin-top: var(--spacing-6);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-primary,
	.btn-secondary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border-radius: var(--radius-lg);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		text-decoration: none;
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		border: none;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: var(--shadow-md3-2);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	/* Responsive */
	@media (max-width: 640px) {
		.ticket-form {
			padding: var(--spacing-4);
		}

		.priority-options {
			grid-template-columns: 1fr;
		}

		.form-actions {
			flex-direction: column;
		}

		.btn-primary,
		.btn-secondary {
			width: 100%;
			justify-content: center;
		}
	}
</style>
