<script lang="ts">
	/**
	 * QuickActionCard - Quick action button for dashboard
	 */

	interface Props {
		icon: 'paystubs' | 'profile' | 'bank' | 'tax' | 'ytd' | 'download';
		label: string;
		href?: string;
		onclick?: () => void;
	}

	let { icon, label, href, onclick }: Props = $props();
</script>

{#if href}
	<a {href} class="quick-action">
		<span class="action-icon">
			{#if icon === 'paystubs'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
					<polyline points="14,2 14,8 20,8" />
					<line x1="16" y1="13" x2="8" y2="13" />
					<line x1="16" y1="17" x2="8" y2="17" />
				</svg>
			{:else if icon === 'profile'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
					<circle cx="12" cy="7" r="4" />
				</svg>
			{:else if icon === 'bank'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
					<line x1="1" y1="10" x2="23" y2="10" />
				</svg>
			{:else if icon === 'tax'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
					<polyline points="16,17 21,12 16,7" />
					<line x1="21" y1="12" x2="9" y2="12" />
				</svg>
			{:else if icon === 'ytd'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="20" x2="18" y2="10" />
					<line x1="12" y1="20" x2="12" y2="4" />
					<line x1="6" y1="20" x2="6" y2="14" />
				</svg>
			{:else if icon === 'download'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="7,10 12,15 17,10" />
					<line x1="12" y1="15" x2="12" y2="3" />
				</svg>
			{/if}
		</span>
		<span class="action-label">{label}</span>
	</a>
{:else}
	<button class="quick-action" {onclick}>
		<span class="action-icon">
			{#if icon === 'paystubs'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
					<polyline points="14,2 14,8 20,8" />
					<line x1="16" y1="13" x2="8" y2="13" />
					<line x1="16" y1="17" x2="8" y2="17" />
				</svg>
			{:else if icon === 'profile'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
					<circle cx="12" cy="7" r="4" />
				</svg>
			{:else if icon === 'bank'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
					<line x1="1" y1="10" x2="23" y2="10" />
				</svg>
			{:else if icon === 'tax'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
					<polyline points="16,17 21,12 16,7" />
					<line x1="21" y1="12" x2="9" y2="12" />
				</svg>
			{:else if icon === 'ytd'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="20" x2="18" y2="10" />
					<line x1="12" y1="20" x2="12" y2="4" />
					<line x1="6" y1="20" x2="6" y2="14" />
				</svg>
			{:else if icon === 'download'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="7,10 12,15 17,10" />
					<line x1="12" y1="15" x2="12" y2="3" />
				</svg>
			{/if}
		</span>
		<span class="action-label">{label}</span>
	</button>
{/if}

<style>
	.quick-action {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		text-decoration: none;
		color: var(--color-surface-700);
		cursor: pointer;
		transition: all var(--transition-fast);
		min-width: 100px;
	}

	.quick-action:hover {
		background: var(--color-surface-50);
		border-color: var(--color-primary-300);
		color: var(--color-primary-600);
	}

	.action-icon {
		width: 32px;
		height: 32px;
		color: var(--color-surface-500);
		transition: color var(--transition-fast);
	}

	.quick-action:hover .action-icon {
		color: var(--color-primary-500);
	}

	.action-icon svg {
		width: 100%;
		height: 100%;
	}

	.action-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		text-align: center;
	}
</style>
