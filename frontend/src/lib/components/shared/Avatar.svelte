<script lang="ts">
	interface Props {
		name: string;
		size?: 'small' | 'medium' | 'large';
	}

	let { name, size = 'medium' }: Props = $props();

	function getInitials(fullName: string): string {
		return fullName
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	const initials = $derived(getInitials(name));
</script>

<div class="avatar" class:small={size === 'small'} class:large={size === 'large'}>
	{initials}
</div>

<style>
	.avatar {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-full);
		background: var(--gradient-primary);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		flex-shrink: 0;
	}

	.avatar.small {
		width: 28px;
		height: 28px;
		font-size: 10px;
	}

	.avatar.large {
		width: 48px;
		height: 48px;
		font-size: var(--font-size-body-content);
	}
</style>
