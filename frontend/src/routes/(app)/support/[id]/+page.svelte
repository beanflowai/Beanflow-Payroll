<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		getTicket,
		addReply,
		addStaffReply,
		checkIsAdmin,
		updateTicketStatus,
		formatFileSize
	} from '$lib/services/ticketService';
	import {
		TICKET_STATUS_INFO,
		TICKET_PRIORITY_INFO,
		type Ticket,
		type TicketReply,
		type TicketStatus
	} from '$lib/types/ticket';

	// Get ticket ID from URL
	const ticketId = $derived($page.params.id);

	// State
	let ticket = $state<Ticket | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Admin state
	let isAdmin = $state(false);

	// Reply state
	let replyContent = $state('');
	let submittingReply = $state(false);
	let replyError = $state<string | null>(null);

	// Status update state
	let updatingStatus = $state(false);

	// Image modal state
	let selectedImage = $state<string | null>(null);

	// Status options for admin
	const statusOptions: { value: TicketStatus; label: string }[] = [
		{ value: 'open', label: 'Open' },
		{ value: 'in_progress', label: 'In Progress' },
		{ value: 'resolved', label: 'Resolved' },
		{ value: 'closed', label: 'Closed' }
	];

	// Check admin status
	async function checkAdminStatus() {
		try {
			isAdmin = await checkIsAdmin();
		} catch (err) {
			console.error('Error checking admin status:', err);
		}
	}

	// Load ticket data
	async function loadTicket() {
		if (!ticketId) {
			error = 'Invalid ticket ID';
			loading = false;
			return;
		}

		loading = true;
		error = null;

		try {
			ticket = await getTicket(ticketId);
			if (!ticket) {
				error = 'Ticket not found';
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load ticket';
		} finally {
			loading = false;
		}
	}

	// Initial load
	$effect(() => {
		checkAdminStatus();
		if (ticketId) {
			loadTicket();
		}
	});

	// Submit reply
	async function handleSubmitReply() {
		if (!replyContent.trim() || submittingReply || !ticket) return;

		submittingReply = true;
		replyError = null;

		try {
			// Use staff reply if admin
			const newReply = isAdmin
				? await addStaffReply(ticket.id, replyContent.trim())
				: await addReply(ticket.id, replyContent.trim());

			// Add to local state
			if (ticket.replies) {
				ticket.replies = [...ticket.replies, newReply];
			} else {
				ticket.replies = [newReply];
			}
			replyContent = '';
		} catch (err) {
			replyError = err instanceof Error ? err.message : 'Failed to add reply';
		} finally {
			submittingReply = false;
		}
	}

	// Update ticket status (admin only)
	async function handleStatusChange(newStatus: TicketStatus) {
		if (!ticket || updatingStatus || newStatus === ticket.status) return;

		updatingStatus = true;

		try {
			await updateTicketStatus(ticket.id, newStatus);
			ticket.status = newStatus;
		} catch (err) {
			console.error('Error updating status:', err);
			// Optionally show error to user
		} finally {
			updatingStatus = false;
		}
	}

	// Format date
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	// Format short date for replies
	function formatShortDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const isToday = date.toDateString() === now.toDateString();

		if (isToday) {
			return date.toLocaleTimeString('en-CA', {
				hour: '2-digit',
				minute: '2-digit'
			});
		}

		return date.toLocaleDateString('en-CA', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	// Open image modal
	function openImage(url: string) {
		selectedImage = url;
	}

	// Close image modal
	function closeImage() {
		selectedImage = null;
	}
</script>

<svelte:window
	onkeydown={(e) => {
		if (e.key === 'Escape' && selectedImage) closeImage();
	}}
/>

<div class="page-container">
	{#if loading}
		<div class="loading-state">
			<i class="fas fa-spinner fa-spin"></i>
			<span>Loading ticket...</span>
		</div>
	{:else if error}
		<div class="error-state">
			<i class="fas fa-exclamation-circle"></i>
			<p>{error}</p>
			<a href="/support" class="btn-secondary">
				<i class="fas fa-arrow-left"></i>
				Back to Tickets
			</a>
		</div>
	{:else if ticket}
		<!-- Header -->
		<div class="page-header">
			<a href="/support" class="back-link">
				<i class="fas fa-arrow-left"></i>
				Back to Tickets
			</a>
			<div class="header-row">
				<h1 class="page-title">{ticket.title}</h1>
				<div class="header-badges">
					{#if isAdmin}
						<!-- Admin can change status -->
						<div class="status-dropdown">
							<select
								class="status-select {TICKET_STATUS_INFO[ticket.status].colorClass}"
								value={ticket.status}
								onchange={(e) => handleStatusChange(e.currentTarget.value as TicketStatus)}
								disabled={updatingStatus}
							>
								{#each statusOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
							{#if updatingStatus}
								<i class="fas fa-spinner fa-spin status-spinner"></i>
							{/if}
						</div>
					{:else}
						<span class="status-badge {TICKET_STATUS_INFO[ticket.status].colorClass}">
							<i class="fas {TICKET_STATUS_INFO[ticket.status].icon}"></i>
							{TICKET_STATUS_INFO[ticket.status].label}
						</span>
					{/if}
					<span class="priority-badge {TICKET_PRIORITY_INFO[ticket.priority].colorClass}">
						<i class="fas {TICKET_PRIORITY_INFO[ticket.priority].icon}"></i>
						{TICKET_PRIORITY_INFO[ticket.priority].label}
					</span>
				</div>
			</div>
			<div class="page-meta-row">
				<p class="page-meta">
					Created {formatDate(ticket.createdAt)}
					{#if ticket.updatedAt !== ticket.createdAt}
						&middot; Updated {formatDate(ticket.updatedAt)}
					{/if}
				</p>
				{#if isAdmin}
					<span class="admin-badge">
						<i class="fas fa-shield-alt"></i>
						Admin View
					</span>
				{/if}
			</div>
		</div>

		<!-- Ticket Content -->
		<div class="ticket-content">
			<div class="section">
				<h2 class="section-title">Description</h2>
				<div class="description-text">
					{ticket.description}
				</div>
			</div>

			<!-- Attachments -->
			{#if ticket.attachments && ticket.attachments.length > 0}
				<div class="section">
					<h2 class="section-title">
						<i class="fas fa-paperclip"></i>
						Attachments ({ticket.attachments.length})
					</h2>
					<div class="attachments-grid">
						{#each ticket.attachments as attachment}
							{#if attachment.url}
								<button
									class="attachment-card"
									onclick={() => openImage(attachment.url!)}
									type="button"
								>
									<img src={attachment.url} alt={attachment.fileName} class="attachment-image" />
									<div class="attachment-overlay">
										<i class="fas fa-search-plus"></i>
									</div>
								</button>
							{:else}
								<div class="attachment-card no-preview">
									<i class="fas fa-image"></i>
									<span>{attachment.fileName}</span>
								</div>
							{/if}
						{/each}
					</div>
				</div>
			{/if}

			<!-- Replies -->
			<div class="section">
				<h2 class="section-title">
					<i class="fas fa-comments"></i>
					Conversation ({ticket.replies?.length || 0})
				</h2>

				{#if ticket.replies && ticket.replies.length > 0}
					<div class="replies-timeline">
						{#each ticket.replies as reply}
							<div class="reply-item" class:staff-reply={reply.isStaff}>
								<div class="reply-avatar">
									{#if reply.isStaff}
										<i class="fas fa-headset"></i>
									{:else}
										<i class="fas fa-user"></i>
									{/if}
								</div>
								<div class="reply-content">
									<div class="reply-header">
										<span class="reply-author">
											{reply.isStaff ? 'Support Team' : 'Customer'}
										</span>
										{#if reply.isStaff}
											<span class="staff-tag">Staff</span>
										{/if}
										<span class="reply-time">{formatShortDate(reply.createdAt)}</span>
									</div>
									<div class="reply-text">{reply.content}</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-replies">No replies yet.</p>
				{/if}

				<!-- Add Reply Form -->
				{#if ticket.status !== 'closed'}
					<form class="reply-form" onsubmit={(e) => { e.preventDefault(); handleSubmitReply(); }}>
						{#if replyError}
							<div class="reply-error">
								<i class="fas fa-exclamation-circle"></i>
								{replyError}
							</div>
						{/if}
						<div class="reply-input-wrapper">
							{#if isAdmin}
								<div class="staff-indicator">
									<i class="fas fa-headset"></i>
									Replying as Support Team
								</div>
							{/if}
							<textarea
								bind:value={replyContent}
								placeholder={isAdmin ? 'Write a staff reply...' : 'Add a reply...'}
								rows="3"
								class="reply-textarea"
								disabled={submittingReply}
							></textarea>
						</div>
						<div class="reply-actions">
							<button
								type="submit"
								class="btn-primary"
								disabled={!replyContent.trim() || submittingReply}
							>
								{#if submittingReply}
									<i class="fas fa-spinner fa-spin"></i>
									Sending...
								{:else}
									<i class="fas fa-paper-plane"></i>
									{isAdmin ? 'Send Staff Reply' : 'Send Reply'}
								{/if}
							</button>
						</div>
					</form>
				{:else}
					<div class="ticket-closed-notice">
						<i class="fas fa-lock"></i>
						This ticket is closed.
						{#if isAdmin}
							<button
								class="reopen-btn"
								onclick={() => handleStatusChange('open')}
								disabled={updatingStatus}
							>
								Reopen Ticket
							</button>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<!-- Image Modal -->
{#if selectedImage}
	<div class="image-modal" onclick={closeImage} role="dialog" aria-modal="true">
		<button class="modal-close" onclick={closeImage} aria-label="Close">
			<i class="fas fa-times"></i>
		</button>
		<img src={selectedImage} alt="Attachment" class="modal-image" onclick={(e) => e.stopPropagation()} />
	</div>
{/if}

<style>
	.page-container {
		max-width: 800px;
		margin: 0 auto;
	}

	/* Loading & Error States */
	.loading-state,
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12);
		text-align: center;
		background: white;
		border-radius: var(--radius-xl);
		border: 1px solid var(--color-surface-200);
	}

	.loading-state {
		gap: var(--spacing-3);
		color: var(--color-surface-500);
	}

	.loading-state i {
		font-size: 24px;
		color: var(--color-primary-500);
	}

	.error-state {
		gap: var(--spacing-4);
	}

	.error-state i {
		font-size: 32px;
		color: var(--color-error-500);
	}

	.error-state p {
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Header */
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

	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.page-title {
		font-size: var(--font-size-headline-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
		flex: 1;
	}

	.header-badges {
		display: flex;
		gap: var(--spacing-2);
		flex-shrink: 0;
		align-items: center;
	}

	.status-badge,
	.priority-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-md);
		font-size: var(--font-size-label-small);
		font-weight: var(--font-weight-medium);
	}

	.status-dropdown {
		position: relative;
		display: flex;
		align-items: center;
	}

	.status-select {
		padding: var(--spacing-1) var(--spacing-3) var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-md);
		font-size: var(--font-size-label-small);
		font-weight: var(--font-weight-medium);
		border: 1px solid transparent;
		cursor: pointer;
		appearance: none;
		padding-right: var(--spacing-6);
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 4px center;
		background-size: 16px;
	}

	.status-spinner {
		position: absolute;
		right: var(--spacing-2);
		font-size: 12px;
	}

	.page-meta-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: var(--spacing-2);
	}

	.page-meta {
		color: var(--color-surface-500);
		font-size: var(--font-size-body-small);
		margin: 0;
	}

	.admin-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		border-radius: var(--radius-md);
		font-size: var(--font-size-label-small);
		font-weight: var(--font-weight-medium);
	}

	/* Content */
	.ticket-content {
		background: white;
		border-radius: var(--radius-xl);
		border: 1px solid var(--color-surface-200);
		overflow: hidden;
	}

	.section {
		padding: var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.section:last-child {
		border-bottom: none;
	}

	.section-title {
		font-size: var(--font-size-body-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3) 0;
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.section-title i {
		color: var(--color-surface-400);
	}

	.description-text {
		color: var(--color-surface-700);
		line-height: 1.6;
		white-space: pre-wrap;
	}

	/* Attachments */
	.attachments-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: var(--spacing-3);
	}

	.attachment-card {
		position: relative;
		aspect-ratio: 1;
		border-radius: var(--radius-lg);
		overflow: hidden;
		cursor: pointer;
		border: 1px solid var(--color-surface-200);
		background: var(--color-surface-100);
		transition: var(--transition-fast);
	}

	.attachment-card:hover {
		border-color: var(--color-primary-300);
		transform: scale(1.02);
	}

	.attachment-image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.attachment-overlay {
		position: absolute;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0;
		transition: var(--transition-fast);
		color: white;
		font-size: 24px;
	}

	.attachment-card:hover .attachment-overlay {
		opacity: 1;
	}

	.attachment-card.no-preview {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-small);
	}

	.attachment-card.no-preview i {
		font-size: 24px;
	}

	/* Replies */
	.replies-timeline {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.reply-item {
		display: flex;
		gap: var(--spacing-3);
	}

	.reply-avatar {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-full);
		background: var(--color-surface-100);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-surface-500);
		flex-shrink: 0;
	}

	.staff-reply .reply-avatar {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.reply-content {
		flex: 1;
		min-width: 0;
	}

	.reply-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-1);
	}

	.reply-author {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.staff-reply .reply-author {
		color: var(--color-primary-700);
	}

	.staff-tag {
		font-size: var(--font-size-label-small);
		padding: 2px 6px;
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}

	.reply-time {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		margin-left: auto;
	}

	.reply-text {
		color: var(--color-surface-700);
		line-height: 1.5;
		white-space: pre-wrap;
	}

	.no-replies {
		color: var(--color-surface-500);
		text-align: center;
		padding: var(--spacing-4);
	}

	/* Reply Form */
	.reply-form {
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.reply-error {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-error-50);
		color: var(--color-error-700);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
		margin-bottom: var(--spacing-3);
	}

	.reply-input-wrapper {
		position: relative;
	}

	.staff-indicator {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-primary-50);
		color: var(--color-primary-700);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-lg) var(--radius-lg) 0 0;
		border: 1px solid var(--color-primary-200);
		border-bottom: none;
	}

	.reply-textarea {
		width: 100%;
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		resize: vertical;
		min-height: 80px;
		transition: var(--transition-fast);
	}

	.staff-indicator + .reply-textarea {
		border-radius: 0 0 var(--radius-lg) var(--radius-lg);
		border-top-color: var(--color-primary-200);
	}

	.reply-textarea:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.reply-actions {
		display: flex;
		justify-content: flex-end;
		margin-top: var(--spacing-3);
	}

	.ticket-closed-notice {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
		color: var(--color-surface-600);
		margin-top: var(--spacing-4);
	}

	.reopen-btn {
		padding: var(--spacing-1) var(--spacing-3);
		background: white;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		color: var(--color-surface-700);
		font-size: var(--font-size-body-small);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.reopen-btn:hover:not(:disabled) {
		border-color: var(--color-primary-500);
		color: var(--color-primary-700);
	}

	/* Buttons */
	.btn-primary,
	.btn-secondary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
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

	/* Image Modal */
	.image-modal {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.9);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal-close {
		position: absolute;
		top: var(--spacing-4);
		right: var(--spacing-4);
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.1);
		border: none;
		border-radius: var(--radius-full);
		color: white;
		font-size: 20px;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.modal-close:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	.modal-image {
		max-width: 100%;
		max-height: 90vh;
		object-fit: contain;
		border-radius: var(--radius-lg);
	}

	/* Responsive */
	@media (max-width: 640px) {
		.header-row {
			flex-direction: column;
			gap: var(--spacing-3);
		}

		.header-badges {
			align-self: flex-start;
		}

		.attachments-grid {
			grid-template-columns: repeat(3, 1fr);
		}

		.page-meta-row {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-2);
		}
	}
</style>
