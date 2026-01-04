<script lang="ts">
	import { goto } from '$app/navigation';
	import { getTickets, checkIsAdmin, getTicketStats } from '$lib/services/ticketService';
	import {
		TICKET_STATUS_INFO,
		TICKET_PRIORITY_INFO,
		type Ticket,
		type TicketStatus
	} from '$lib/types/ticket';
	import { TableSkeleton, AlertBanner, EmptyState } from '$lib/components/shared';
	import { timeAgo } from '$lib/utils/dateUtils';

	// State
	let tickets = $state<Ticket[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let selectedStatus = $state<TicketStatus | 'all'>('all');

	// Admin state
	let isAdmin = $state(false);
	let stats = $state<{
		total: number;
		open: number;
		inProgress: number;
		resolved: number;
		closed: number;
	} | null>(null);

	// Filter options
	const statusOptions: { value: TicketStatus | 'all'; label: string }[] = [
		{ value: 'all', label: 'All Tickets' },
		{ value: 'open', label: 'Open' },
		{ value: 'in_progress', label: 'In Progress' },
		{ value: 'resolved', label: 'Resolved' },
		{ value: 'closed', label: 'Closed' }
	];

	// Check admin status on load
	async function checkAdminStatus() {
		try {
			isAdmin = await checkIsAdmin();
			if (isAdmin) {
				stats = await getTicketStats();
			}
		} catch (err) {
			console.error('Error checking admin status:', err);
		}
	}

	// Load tickets
	async function loadTickets() {
		loading = true;
		error = null;

		try {
			const status = selectedStatus === 'all' ? undefined : selectedStatus;
			tickets = await getTickets(status);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load tickets';
		} finally {
			loading = false;
		}
	}

	// Initial load
	$effect(() => {
		checkAdminStatus();
	});

	// Reload on filter change
	$effect(() => {
		// This effect depends on selectedStatus
		void selectedStatus;
		loadTickets();
	});
</script>

<div class="page-container">
	<!-- Header -->
	<div class="page-header">
		<div class="header-content">
			<h1 class="page-title">
				<i class="fas fa-life-ring"></i>
				Support Tickets
				{#if isAdmin}
					<span class="admin-badge">Admin</span>
				{/if}
			</h1>
			<p class="page-subtitle">
				{#if isAdmin}
					Manage all support requests
				{:else}
					Submit and track your support requests
				{/if}
			</p>
		</div>
		{#if !isAdmin}
			<button class="btn-primary" onclick={() => goto('/support/new')}>
				<i class="fas fa-plus"></i>
				New Ticket
			</button>
		{/if}
	</div>

	<!-- Admin Stats -->
	{#if isAdmin && stats}
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon total">
					<i class="fas fa-ticket-alt"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{stats.total}</span>
					<span class="stat-label">Total</span>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon open">
					<i class="fas fa-circle-dot"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{stats.open}</span>
					<span class="stat-label">Open</span>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon in-progress">
					<i class="fas fa-spinner"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{stats.inProgress}</span>
					<span class="stat-label">In Progress</span>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon resolved">
					<i class="fas fa-check-circle"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{stats.resolved}</span>
					<span class="stat-label">Resolved</span>
				</div>
			</div>
		</div>
	{/if}

	<!-- Filters -->
	<div class="filters-bar">
		<div class="filter-group">
			<label for="status-filter">Status:</label>
			<select id="status-filter" bind:value={selectedStatus} class="filter-select">
				{#each statusOptions as option (option.value)}
					<option value={option.value}>{option.label}</option>
				{/each}
			</select>
		</div>
		<div class="ticket-count">
			{tickets.length} ticket{tickets.length !== 1 ? 's' : ''}
		</div>
	</div>

	<!-- Content -->
	{#if loading}
		<TableSkeleton rows={5} columns={4} />
	{:else if error}
		<AlertBanner type="error" title="Failed to load tickets" message={error}>
			<button class="btn-secondary mt-2" onclick={loadTickets}>Try Again</button>
		</AlertBanner>
	{:else if tickets.length === 0}
		<EmptyState
			icon="fa-ticket-alt"
			title="No tickets found"
			description={selectedStatus === 'all'
				? isAdmin
					? 'No support tickets have been submitted yet.'
					: "You haven't submitted any support tickets yet."
				: `No tickets with status "${TICKET_STATUS_INFO[selectedStatus].label}".`}
			actionLabel={!isAdmin ? 'Create Your First Ticket' : undefined}
			onAction={!isAdmin ? () => goto('/support/new') : undefined}
			variant="card"
		/>
	{:else}
		<div class="tickets-list">
			{#each tickets as ticket (ticket.id)}
				<a href="/support/{ticket.id}" class="ticket-card">
					<div class="ticket-header">
						<h3 class="ticket-title">{ticket.title}</h3>
						<div class="ticket-badges">
							<span class="status-badge {TICKET_STATUS_INFO[ticket.status].colorClass}">
								<i class="fas {TICKET_STATUS_INFO[ticket.status].icon}"></i>
								{TICKET_STATUS_INFO[ticket.status].label}
							</span>
							<span class="priority-badge {TICKET_PRIORITY_INFO[ticket.priority].colorClass}">
								<i class="fas {TICKET_PRIORITY_INFO[ticket.priority].icon}"></i>
								{TICKET_PRIORITY_INFO[ticket.priority].label}
							</span>
						</div>
					</div>
					<p class="ticket-description">{ticket.description}</p>
					<div class="ticket-footer">
						<span class="ticket-meta">
							<i class="fas fa-clock"></i>
							{timeAgo(ticket.createdAt)}
						</span>
						{#if ticket.replyCount && ticket.replyCount > 0}
							<span class="ticket-meta">
								<i class="fas fa-comment"></i>
								{ticket.replyCount} repl{ticket.replyCount === 1 ? 'y' : 'ies'}
							</span>
						{/if}
						{#if isAdmin}
							<span class="ticket-meta user-id">
								<i class="fas fa-user"></i>
								{ticket.userId.slice(0, 8)}...
							</span>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.page-container {
		max-width: 900px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--spacing-6);
		gap: var(--spacing-4);
	}

	.header-content {
		flex: 1;
	}

	.page-title {
		font-size: var(--font-size-headline-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		margin: 0;
	}

	.page-title i {
		color: var(--color-primary-600);
	}

	.admin-badge {
		font-size: var(--font-size-label-small);
		font-weight: var(--font-weight-medium);
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		border-radius: var(--radius-md);
	}

	.page-subtitle {
		color: var(--color-surface-600);
		margin-top: var(--spacing-1);
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		transform: translateY(-1px);
		box-shadow: var(--shadow-md3-2);
	}

	.btn-secondary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-lg);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	/* Admin Stats */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.stat-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-200);
	}

	.stat-icon {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-lg);
		font-size: 20px;
	}

	.stat-icon.total {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.stat-icon.open {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.stat-icon.in-progress {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.stat-icon.resolved {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.stat-content {
		display: flex;
		flex-direction: column;
	}

	.stat-value {
		font-size: var(--font-size-headline-small);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-900);
		line-height: 1;
	}

	.stat-label {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Filters */
	.filters-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-200);
	}

	.filter-group {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.filter-group label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.filter-select {
		padding: var(--spacing-2) var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		background: white;
		cursor: pointer;
	}

	.ticket-count {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	/* Tickets List */
	.tickets-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.ticket-card {
		display: block;
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-200);
		text-decoration: none;
		transition: var(--transition-fast);
	}

	.ticket-card:hover {
		border-color: var(--color-primary-300);
		box-shadow: var(--shadow-md3-1);
		transform: translateY(-1px);
	}

	.ticket-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-2);
	}

	.ticket-title {
		font-size: var(--font-size-body-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
		flex: 1;
	}

	.ticket-badges {
		display: flex;
		gap: var(--spacing-2);
		flex-shrink: 0;
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

	.ticket-description {
		color: var(--color-surface-600);
		font-size: var(--font-size-body-content);
		margin: 0 0 var(--spacing-3) 0;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.ticket-footer {
		display: flex;
		gap: var(--spacing-4);
	}

	.ticket-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
	}

	.ticket-meta.user-id {
		font-family: monospace;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 640px) {
		.page-header {
			flex-direction: column;
		}

		.ticket-header {
			flex-direction: column;
			gap: var(--spacing-2);
		}

		.ticket-badges {
			align-self: flex-start;
		}

		.filters-bar {
			flex-direction: column;
			gap: var(--spacing-2);
			align-items: stretch;
		}

		.ticket-count {
			text-align: center;
		}

		.stats-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
