<script lang="ts">
	/**
	 * ProfileField - Single field display in profile section
	 */

	interface Props {
		label: string;
		value: string;
		masked?: boolean;
	}

	let { label, value, masked = false }: Props = $props();
</script>

<div class="profile-field">
	<span class="field-label">{label}</span>
	<span class="field-value" class:masked>{value}</span>
</div>

<style>
	.profile-field {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.field-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		flex-shrink: 0;
		min-width: 140px;
	}

	.field-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-900);
		text-align: right;
		word-break: break-word;
	}

	.field-value.masked {
		font-family: monospace;
		letter-spacing: 1px;
	}

	/* Mobile adjustments */
	@media (max-width: 480px) {
		.profile-field {
			flex-direction: column;
			gap: var(--spacing-1);
		}

		.field-value {
			text-align: left;
		}
	}
</style>
