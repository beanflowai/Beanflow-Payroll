<script lang="ts">
	// IntegrationTab - Bookkeeping integration (Tab 3)
	import type {
		BookkeepingSyncStatus,
		AccountMapping,
		BookkeepingLedger
	} from '$lib/types/company';
	import { DEFAULT_ACCOUNT_MAPPINGS } from '$lib/types/company';
	import ConnectBookkeepingModal from './ConnectBookkeepingModal.svelte';
	import DisconnectModal from './DisconnectModal.svelte';

	// Mock state - toggle to see connected vs disconnected views
	let isConnected = $state(true);
	let connectedLedgerName = $state('Acme Corp - Main Ledger');
	let connectedAt = $state('December 1, 2025');

	// Sync status mock data
	let syncStatus = $state<BookkeepingSyncStatus>({
		lastSyncAt: 'December 8, 2025 at 2:30 PM',
		entriesCreated: 24,
		status: 'synced'
	});

	// Account mappings
	let accountMappings = $state<AccountMapping[]>(DEFAULT_ACCOUNT_MAPPINGS);

	// Modal state
	let showConnectModal = $state(false);
	let showDisconnectModal = $state(false);

	// Mock ledgers for connect modal
	const availableLedgers: BookkeepingLedger[] = [
		{ id: 'ledger-1', name: 'Acme Corp - Main Ledger', lastUpdated: 'Dec 8, 2025' },
		{ id: 'ledger-2', name: 'Acme Corp - Test Ledger', lastUpdated: 'Nov 15, 2025' },
		{ id: 'ledger-3', name: 'Personal Finance', lastUpdated: 'Dec 1, 2025' }
	];

	function handleConnect(ledgerId: string) {
		const ledger = availableLedgers.find((l) => l.id === ledgerId);
		if (ledger) {
			isConnected = true;
			connectedLedgerName = ledger.name;
			connectedAt = new Date().toLocaleDateString('en-CA', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		}
		showConnectModal = false;
	}

	function handleDisconnect() {
		isConnected = false;
		connectedLedgerName = '';
		connectedAt = '';
		showDisconnectModal = false;
	}
</script>

<div class="integration-tab">
	<section class="settings-section">
		<div class="section-header">
			<div class="section-icon">
				<i class="fas fa-link"></i>
			</div>
			<div class="section-info">
				<h2 class="section-title">Bookkeeping Integration</h2>
				<p class="section-description">
					Connect to BeanFlow Bookkeeping for automatic journal entries
				</p>
			</div>
		</div>

		<div class="settings-card">
			{#if isConnected}
				<!-- Connected State -->
				<div class="connection-status connected">
					<div class="status-badge">
						<i class="fas fa-check-circle"></i>
						<span>Connected</span>
					</div>
				</div>

				<div class="ledger-info">
					<div class="ledger-icon">
						<i class="fas fa-book"></i>
					</div>
					<div class="ledger-details">
						<span class="ledger-name">{connectedLedgerName}</span>
						<span class="ledger-connected">Connected on: {connectedAt}</span>
					</div>
				</div>

				<p class="info-text">
					Payroll journal entries will be automatically created when you approve a payroll run.
				</p>

				<div class="divider"></div>

				<!-- Sync Status -->
				<h3 class="sub-section-title">Sync Status</h3>
				<div class="sync-status-card">
					<div class="sync-row">
						<span class="sync-label"><i class="fas fa-calendar"></i> Last Sync:</span>
						<span class="sync-value">{syncStatus.lastSyncAt ?? 'Never'}</span>
					</div>
					<div class="sync-row">
						<span class="sync-label"><i class="fas fa-file-alt"></i> Entries Created:</span>
						<span class="sync-value">{syncStatus.entriesCreated}</span>
					</div>
					<div class="sync-row">
						<span class="sync-label"><i class="fas fa-check"></i> Status:</span>
						<span class="sync-value status-synced">
							<i class="fas fa-check-circle"></i>
							All synced
						</span>
					</div>
				</div>

				<div class="divider"></div>

				<!-- Account Mapping -->
				<h3 class="sub-section-title">Account Mapping</h3>
				<div class="mapping-table">
					<div class="mapping-header">
						<span>Payroll Type</span>
						<span></span>
						<span>Account</span>
					</div>
					{#each accountMappings as mapping (mapping.payrollType)}
						<div class="mapping-row">
							<span class="mapping-type">{mapping.payrollType}</span>
							<span class="mapping-arrow"><i class="fas fa-arrow-right"></i></span>
							<span class="mapping-account">{mapping.account}</span>
						</div>
					{/each}
				</div>

				<div class="disconnect-action">
					<button class="btn-destructive-outline" onclick={() => (showDisconnectModal = true)}>
						Disconnect
					</button>
				</div>
			{:else}
				<!-- Not Connected State -->
				<div class="connection-status not-connected">
					<div class="status-icon">
						<i class="fas fa-unlink"></i>
					</div>
					<div class="status-badge">
						<span>Not Connected</span>
					</div>
				</div>

				<p class="info-text centered">
					Link to a BeanFlow Bookkeeping company to automatically generate journal entries when you
					run payroll.
				</p>

				<div class="divider"></div>

				<h3 class="sub-section-title">Benefits of connecting:</h3>
				<ul class="benefits-list">
					<li>
						<i class="fas fa-check"></i>
						<div>
							<strong>Automatic payroll expense entries</strong>
							<span>Journal entries created when payroll is approved</span>
						</div>
					</li>
					<li>
						<i class="fas fa-check"></i>
						<div>
							<strong>Liability tracking</strong>
							<span>CPP, EI, and Tax payable accounts updated automatically</span>
						</div>
					</li>
					<li>
						<i class="fas fa-check"></i>
						<div>
							<strong>Bank reconciliation support</strong>
							<span>Payroll payments appear in bank reconciliation</span>
						</div>
					</li>
				</ul>

				<div class="connect-action">
					<button class="btn-primary" onclick={() => (showConnectModal = true)}>
						<i class="fas fa-link"></i>
						<span>Connect to Bookkeeping</span>
					</button>
				</div>
			{/if}
		</div>
	</section>
</div>

<!-- Connect Modal -->
{#if showConnectModal}
	<ConnectBookkeepingModal
		ledgers={availableLedgers}
		onClose={() => (showConnectModal = false)}
		onConnect={handleConnect}
	/>
{/if}

<!-- Disconnect Modal -->
{#if showDisconnectModal}
	<DisconnectModal
		ledgerName={connectedLedgerName}
		onClose={() => (showDisconnectModal = false)}
		onConfirm={handleDisconnect}
	/>
{/if}

<style>
	.integration-tab {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	/* Section */
	.settings-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.section-header {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.section-icon {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-lg);
		background: var(--color-tertiary-100);
		color: var(--color-tertiary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
		flex-shrink: 0;
	}

	.section-info {
		flex: 1;
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.section-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Settings Card */
	.settings-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-6);
	}

	/* Connection Status */
	.connection-status {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-4);
	}

	.status-icon {
		width: 64px;
		height: 64px;
		border-radius: var(--radius-full);
		background: var(--color-surface-100);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28px;
		color: var(--color-surface-400);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border-radius: var(--radius-full);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
	}

	.connected .status-badge {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.connected .status-badge i {
		color: var(--color-success-500);
	}

	.not-connected .status-badge {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	/* Ledger Info */
	.ledger-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-4);
	}

	.ledger-icon {
		width: 48px;
		height: 48px;
		border-radius: var(--radius-lg);
		background: var(--color-primary-100);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
		color: var(--color-primary-600);
	}

	.ledger-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.ledger-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.ledger-connected {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Info Text */
	.info-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.info-text.centered {
		text-align: center;
	}

	/* Divider */
	.divider {
		height: 1px;
		background: var(--color-surface-100);
		margin: var(--spacing-5) 0;
	}

	/* Sub Section */
	.sub-section-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	/* Sync Status */
	.sync-status-card {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
	}

	.sync-row {
		display: flex;
		justify-content: space-between;
		padding: var(--spacing-2) 0;
	}

	.sync-row:not(:last-child) {
		border-bottom: 1px solid var(--color-surface-100);
	}

	.sync-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.sync-label i {
		color: var(--color-surface-400);
		width: 16px;
	}

	.sync-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.sync-value.status-synced {
		color: var(--color-success-600);
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	/* Account Mapping Table */
	.mapping-table {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.mapping-header {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-100);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.mapping-row {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
		font-size: var(--font-size-auxiliary-text);
	}

	.mapping-row:last-child {
		border-bottom: none;
	}

	.mapping-type {
		color: var(--color-surface-700);
	}

	.mapping-arrow {
		color: var(--color-surface-400);
	}

	.mapping-account {
		color: var(--color-primary-600);
		font-family: monospace;
	}

	/* Benefits List */
	.benefits-list {
		list-style: none;
		padding: 0;
		margin: 0 0 var(--spacing-6);
	}

	.benefits-list li {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-3) 0;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.benefits-list li:last-child {
		border-bottom: none;
	}

	.benefits-list i {
		color: var(--color-success-500);
		margin-top: 4px;
	}

	.benefits-list strong {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin-bottom: var(--spacing-1);
	}

	.benefits-list span {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	/* Actions */
	.connect-action,
	.disconnect-action {
		display: flex;
		justify-content: center;
		margin-top: var(--spacing-4);
	}

	/* Buttons */
	.btn-primary {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-destructive-outline {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: 1px solid var(--color-error-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		background: white;
		color: var(--color-error-600);
	}

	.btn-destructive-outline:hover {
		background: var(--color-error-50);
		border-color: var(--color-error-400);
	}

	@media (max-width: 640px) {
		.mapping-table {
			font-size: var(--font-size-auxiliary-text);
		}

		.mapping-account {
			word-break: break-all;
		}
	}
</style>
