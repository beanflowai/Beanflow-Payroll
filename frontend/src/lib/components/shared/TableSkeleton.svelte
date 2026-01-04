<script lang="ts">
	/**
	 * TableSkeleton - Loading placeholder for table data
	 */
	import Skeleton from './Skeleton.svelte';

	interface Props {
		rows?: number;
		columns?: number;
		showHeader?: boolean;
	}

	let { rows = 5, columns = 4, showHeader = true }: Props = $props();
</script>

<div class="table-skeleton">
	{#if showHeader}
		<div class="table-header">
			{#each Array(columns) as _unused, colIndex (colIndex)}
				<div class="header-cell">
					<Skeleton variant="text" width="60%" />
				</div>
			{/each}
		</div>
	{/if}

	<div class="table-body">
		{#each Array(rows) as _unused, rowIndex (rowIndex)}
			<div class="table-row">
				{#each Array(columns) as _unused, colIndex (`${rowIndex}-${colIndex}`)}
					<div class="table-cell">
						{#if colIndex === 0}
							<div class="cell-with-avatar">
								<Skeleton variant="circular" width="32px" height="32px" />
								<Skeleton variant="text" width="80%" />
							</div>
						{:else}
							<Skeleton variant="text" width={`${60 + Math.random() * 30}%`} />
						{/if}
					</div>
				{/each}
			</div>
		{/each}
	</div>
</div>

<style>
	.table-skeleton {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.table-header {
		display: flex;
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-200);
		padding: var(--spacing-3) var(--spacing-4);
	}

	.header-cell {
		flex: 1;
		padding: 0 var(--spacing-2);
	}

	.table-body {
		padding: var(--spacing-2) 0;
	}

	.table-row {
		display: flex;
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.table-row:last-child {
		border-bottom: none;
	}

	.table-cell {
		flex: 1;
		padding: 0 var(--spacing-2);
		display: flex;
		align-items: center;
	}

	.cell-with-avatar {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
	}
</style>
