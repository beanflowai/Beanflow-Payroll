<script lang="ts">
	/**
	 * ProfileSection - Collapsible section for profile information
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		id?: string;
		icon: 'personal' | 'tax' | 'bank';
		title: string;
		onEdit?: () => void;
		children: Snippet;
	}

	let { id: _id, icon, title, onEdit, children }: Props = $props();
</script>

<div class="profile-section">
	<div class="section-header">
		<div class="section-title-wrapper">
			<span class="section-icon">
				{#if icon === 'personal'}
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
						<polyline points="16,17 21,12 16,7" />
						<line x1="21" y1="12" x2="9" y2="12" />
					</svg>
				{:else if icon === 'tax'}
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
						<polyline points="14,2 14,8 20,8" />
						<line x1="16" y1="13" x2="8" y2="13" />
						<line x1="16" y1="17" x2="8" y2="17" />
					</svg>
				{:else if icon === 'bank'}
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
						<line x1="1" y1="10" x2="23" y2="10" />
					</svg>
				{/if}
			</span>
			<h3 class="section-title">{title}</h3>
		</div>
		{#if onEdit}
			<button class="edit-btn" onclick={onEdit}>
				<svg viewBox="0 0 20 20" fill="currentColor">
					<path
						d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
					/>
				</svg>
				Edit
			</button>
		{/if}
	</div>

	<div class="section-divider"></div>

	<div class="section-content">
		{@render children()}
	</div>
</div>

<style>
	.profile-section {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.section-title-wrapper {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.section-icon {
		width: 24px;
		height: 24px;
		color: var(--color-surface-500);
	}

	.section-icon svg {
		width: 100%;
		height: 100%;
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
		margin: 0;
	}

	.edit-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-2) var(--spacing-3);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary-500);
		background: transparent;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.edit-btn:hover {
		background: var(--color-primary-50);
		color: var(--color-primary-600);
	}

	.edit-btn svg {
		width: 14px;
		height: 14px;
	}

	.section-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-4) 0;
	}

	.section-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}
</style>
