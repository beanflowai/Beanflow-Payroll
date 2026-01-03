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

<div class="max-w-3xl mx-auto">
	{#if loading}
		<div class="flex flex-col items-center justify-center p-12 text-center bg-white rounded-xl border border-surface-200 gap-3 text-surface-500">
			<i class="fas fa-spinner fa-spin text-2xl text-primary-500"></i>
			<span>Loading ticket...</span>
		</div>
	{:else if error}
		<div class="flex flex-col items-center justify-center p-12 text-center bg-white rounded-xl border border-surface-200 gap-4">
			<i class="fas fa-exclamation-circle text-3xl text-error-500"></i>
			<p class="text-surface-600 m-0">{error}</p>
			<a href="/support" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-white text-surface-700 border border-surface-300 hover:bg-surface-50 hover:border-surface-400 no-underline">
				<i class="fas fa-arrow-left"></i>
				Back to Tickets
			</a>
		</div>
	{:else if ticket}
		<!-- Header -->
		<div class="mb-6">
			<a href="/support" class="inline-flex items-center gap-2 text-surface-600 text-sm mb-3 hover:text-primary-600 transition no-underline">
				<i class="fas fa-arrow-left"></i>
				Back to Tickets
			</a>
			<div class="flex justify-between items-start gap-4 max-sm:flex-col max-sm:gap-3">
				<h1 class="text-xl font-semibold text-surface-900 m-0 flex-1">{ticket.title}</h1>
				<div class="flex gap-2 shrink-0 items-center max-sm:self-start">
					{#if isAdmin}
						<!-- Admin can change status -->
						<div class="relative flex items-center">
							<select
								class="py-1 pl-2 pr-6 rounded-md text-xs font-medium border border-transparent cursor-pointer appearance-none bg-[url('data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22currentColor%22%3E%3Cpath%20d%3D%22M7%2010l5%205%205-5z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_4px_center] bg-[length:16px] {TICKET_STATUS_INFO[ticket.status].colorClass}"
								value={ticket.status}
								onchange={(e) => handleStatusChange(e.currentTarget.value as TicketStatus)}
								disabled={updatingStatus}
							>
								{#each statusOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
							{#if updatingStatus}
								<i class="fas fa-spinner fa-spin absolute right-2 text-xs"></i>
							{/if}
						</div>
					{:else}
						<span class="inline-flex items-center gap-1 py-1 px-2 rounded-md text-xs font-medium {TICKET_STATUS_INFO[ticket.status].colorClass}">
							<i class="fas {TICKET_STATUS_INFO[ticket.status].icon}"></i>
							{TICKET_STATUS_INFO[ticket.status].label}
						</span>
					{/if}
					<span class="inline-flex items-center gap-1 py-1 px-2 rounded-md text-xs font-medium {TICKET_PRIORITY_INFO[ticket.priority].colorClass}">
						<i class="fas {TICKET_PRIORITY_INFO[ticket.priority].icon}"></i>
						{TICKET_PRIORITY_INFO[ticket.priority].label}
					</span>
				</div>
			</div>
			<div class="flex items-center justify-between mt-2 max-sm:flex-col max-sm:items-start max-sm:gap-2">
				<p class="text-surface-500 text-sm m-0">
					Created {formatDate(ticket.createdAt)}
					{#if ticket.updatedAt !== ticket.createdAt}
						&middot; Updated {formatDate(ticket.updatedAt)}
					{/if}
				</p>
				{#if isAdmin}
					<span class="inline-flex items-center gap-1 py-1 px-2 bg-primary-100 text-primary-700 rounded-md text-xs font-medium">
						<i class="fas fa-shield-alt"></i>
						Admin View
					</span>
				{/if}
			</div>
		</div>

		<!-- Ticket Content -->
		<div class="bg-white rounded-xl border border-surface-200 overflow-hidden">
			<div class="p-5 border-b border-surface-200">
				<h2 class="text-lg font-semibold text-surface-800 m-0 mb-3 flex items-center gap-2">Description</h2>
				<div class="text-surface-700 leading-relaxed whitespace-pre-wrap">
					{ticket.description}
				</div>
			</div>

			<!-- Attachments -->
			{#if ticket.attachments && ticket.attachments.length > 0}
				<div class="p-5 border-b border-surface-200">
					<h2 class="text-lg font-semibold text-surface-800 m-0 mb-3 flex items-center gap-2">
						<i class="fas fa-paperclip text-surface-400"></i>
						Attachments ({ticket.attachments.length})
					</h2>
					<div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3 max-sm:grid-cols-3">
						{#each ticket.attachments as attachment}
							{#if attachment.url}
								<button
									class="group relative aspect-square rounded-lg overflow-hidden cursor-pointer border border-surface-200 bg-surface-100 transition hover:border-primary-300 hover:scale-[1.02]"
									onclick={() => openImage(attachment.url!)}
									type="button"
								>
									<img src={attachment.url} alt={attachment.fileName} class="w-full h-full object-cover" />
									<div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition text-white text-2xl">
										<i class="fas fa-search-plus"></i>
									</div>
								</button>
							{:else}
								<div class="relative aspect-square rounded-lg overflow-hidden border border-surface-200 bg-surface-100 flex flex-col items-center justify-center gap-2 text-surface-500 text-sm">
									<i class="fas fa-image text-2xl"></i>
									<span>{attachment.fileName}</span>
								</div>
							{/if}
						{/each}
					</div>
				</div>
			{/if}

			<!-- Replies -->
			<div class="p-5">
				<h2 class="text-lg font-semibold text-surface-800 m-0 mb-3 flex items-center gap-2">
					<i class="fas fa-comments text-surface-400"></i>
					Conversation ({ticket.replies?.length || 0})
				</h2>

				{#if ticket.replies && ticket.replies.length > 0}
					<div class="flex flex-col gap-4">
						{#each ticket.replies as reply}
							<div class="flex gap-3">
								<div class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 {reply.isStaff ? 'bg-primary-100 text-primary-600' : 'bg-surface-100 text-surface-500'}">
									{#if reply.isStaff}
										<i class="fas fa-headset"></i>
									{:else}
										<i class="fas fa-user"></i>
									{/if}
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2 mb-1">
										<span class="font-medium {reply.isStaff ? 'text-primary-700' : 'text-surface-800'}">
											{reply.isStaff ? 'Support Team' : 'Customer'}
										</span>
										{#if reply.isStaff}
											<span class="text-xs py-0.5 px-1.5 bg-primary-100 text-primary-700 rounded font-medium">Staff</span>
										{/if}
										<span class="text-sm text-surface-500 ml-auto">{formatShortDate(reply.createdAt)}</span>
									</div>
									<div class="text-surface-700 leading-normal whitespace-pre-wrap">{reply.content}</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-surface-500 text-center py-4">No replies yet.</p>
				{/if}

				<!-- Add Reply Form -->
				{#if ticket.status !== 'closed'}
					<form class="mt-4 pt-4 border-t border-surface-200" onsubmit={(e) => { e.preventDefault(); handleSubmitReply(); }}>
						{#if replyError}
							<div class="flex items-center gap-2 py-2 px-3 bg-error-50 text-error-700 rounded-md text-sm mb-3">
								<i class="fas fa-exclamation-circle"></i>
								{replyError}
							</div>
						{/if}
						<div class="relative">
							{#if isAdmin}
								<div class="flex items-center gap-2 py-2 px-3 bg-primary-50 text-primary-700 text-sm font-medium rounded-t-lg border border-primary-200 border-b-0">
									<i class="fas fa-headset"></i>
									Replying as Support Team
								</div>
							{/if}
							<textarea
								bind:value={replyContent}
								placeholder={isAdmin ? 'Write a staff reply...' : 'Add a reply...'}
								rows="3"
								class="w-full p-3 border border-surface-300 rounded-lg text-base resize-y min-h-20 transition focus:outline-none focus:border-primary-500 focus:ring-3 focus:ring-primary-100 disabled:opacity-60 {isAdmin ? 'rounded-t-none border-t-primary-200' : ''}"
								disabled={submittingReply}
							></textarea>
						</div>
						<div class="flex justify-end mt-3">
							<button
								type="submit"
								class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md hover:-translate-y-px hover:shadow-lg transition disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
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
					<div class="flex items-center justify-center gap-3 p-4 bg-surface-100 rounded-lg text-surface-600 mt-4">
						<i class="fas fa-lock"></i>
						This ticket is closed.
						{#if isAdmin}
							<button
								class="py-1 px-3 bg-white border border-surface-300 rounded-md text-surface-700 text-sm cursor-pointer transition hover:border-primary-500 hover:text-primary-700 disabled:opacity-60"
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
	<div class="fixed inset-0 bg-black/90 flex items-center justify-center z-[1000] p-4" onclick={closeImage} role="dialog" aria-modal="true">
		<button class="absolute top-4 right-4 w-10 h-10 flex items-center justify-center bg-white/10 border-none rounded-full text-white text-xl cursor-pointer hover:bg-white/20 transition" onclick={closeImage} aria-label="Close">
			<i class="fas fa-times"></i>
		</button>
		<img src={selectedImage} alt="Attachment" class="max-w-full max-h-[90vh] object-contain rounded-lg" onclick={(e) => e.stopPropagation()} />
	</div>
{/if}
