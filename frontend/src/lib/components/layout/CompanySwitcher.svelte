<script lang="ts">
	import { companyState, switchCompany } from '$lib/stores/company.svelte';

	interface Props {
		collapsed?: boolean;
		onAddCompany?: () => void;
	}

	let { collapsed = false, onAddCompany }: Props = $props();

	let isOpen = $state(false);

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function closeDropdown() {
		isOpen = false;
	}

	async function handleSelectCompany(companyId: string) {
		closeDropdown();
		if (companyId !== companyState.currentCompany?.id) {
			await switchCompany(companyId);
		}
	}

	function handleAddCompany() {
		closeDropdown();
		onAddCompany?.();
	}

	// Close dropdown when clicking outside
	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.company-switcher')) {
			closeDropdown();
		}
	}

	// Get initials for logo placeholder
	function getInitials(name: string): string {
		return name
			.split(' ')
			.map((word) => word[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="company-switcher" class:collapsed>
	<button class="switcher-trigger" onclick={toggleDropdown} aria-expanded={isOpen}>
		<div class="company-logo">
			{#if companyState.currentCompany?.logoUrl}
				<img src={companyState.currentCompany.logoUrl} alt="Company logo" />
			{:else}
				<span class="logo-initials">
					{companyState.currentCompany ? getInitials(companyState.currentCompany.companyName) : '?'}
				</span>
			{/if}
		</div>
		{#if !collapsed}
			<span class="company-name">
				{companyState.currentCompany?.companyName ?? 'Select Company'}
			</span>
			<i class="fas fa-chevron-down dropdown-icon" class:rotated={isOpen}></i>
		{/if}
	</button>

	{#if isOpen}
		<div class="dropdown-menu">
			<div class="dropdown-section">
				{#each companyState.companies as company (company.id)}
					<button
						class="dropdown-item"
						class:active={company.id === companyState.currentCompany?.id}
						onclick={() => handleSelectCompany(company.id)}
					>
						<div class="item-logo">
							{#if company.logoUrl}
								<img src={company.logoUrl} alt="" />
							{:else}
								<span class="logo-initials-small">{getInitials(company.companyName)}</span>
							{/if}
						</div>
						<span class="item-name">{company.companyName}</span>
						{#if company.id === companyState.currentCompany?.id}
							<i class="fas fa-check check-icon"></i>
						{/if}
					</button>
				{/each}
			</div>

			<div class="dropdown-divider"></div>

			<button class="dropdown-item add-company" onclick={handleAddCompany}>
				<div class="item-icon">
					<i class="fas fa-plus"></i>
				</div>
				<span class="item-name">Add new company</span>
			</button>
		</div>
	{/if}
</div>

<style>
	.company-switcher {
		position: relative;
		padding: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.company-switcher.collapsed {
		padding: var(--spacing-3) var(--spacing-2);
	}

	.switcher-trigger {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.switcher-trigger:hover {
		background: var(--color-surface-100);
		border-color: var(--color-surface-300);
	}

	.collapsed .switcher-trigger {
		justify-content: center;
		padding: var(--spacing-2);
	}

	.company-logo {
		width: 32px;
		height: 32px;
		min-width: 32px;
		border-radius: var(--radius-md);
		background: var(--gradient-primary);
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.company-logo img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.logo-initials {
		color: white;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
	}

	.company-name {
		flex: 1;
		text-align: left;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dropdown-icon {
		font-size: 10px;
		color: var(--color-surface-500);
		transition: transform var(--transition-fast);
	}

	.dropdown-icon.rotated {
		transform: rotate(180deg);
	}

	/* Dropdown Menu */
	.dropdown-menu {
		position: absolute;
		top: 100%;
		left: var(--spacing-3);
		right: var(--spacing-3);
		margin-top: var(--spacing-1);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-2);
		z-index: 100;
		overflow: hidden;
	}

	.collapsed .dropdown-menu {
		left: 100%;
		top: 0;
		right: auto;
		width: 240px;
		margin-top: 0;
		margin-left: var(--spacing-2);
	}

	.dropdown-section {
		max-height: 240px;
		overflow-y: auto;
	}

	.dropdown-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
		padding: var(--spacing-3);
		background: none;
		border: none;
		cursor: pointer;
		transition: var(--transition-fast);
		text-align: left;
	}

	.dropdown-item:hover {
		background: var(--color-surface-50);
	}

	.dropdown-item.active {
		background: var(--color-primary-50);
	}

	.item-logo {
		width: 28px;
		height: 28px;
		min-width: 28px;
		border-radius: var(--radius-sm);
		background: var(--gradient-primary);
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.item-logo img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.logo-initials-small {
		color: white;
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-semibold);
	}

	.item-icon {
		width: 28px;
		height: 28px;
		min-width: 28px;
		border-radius: var(--radius-sm);
		background: var(--color-surface-100);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-surface-600);
	}

	.item-name {
		flex: 1;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.check-icon {
		font-size: 12px;
		color: var(--color-primary-500);
	}

	.dropdown-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-1) 0;
	}

	.add-company {
		color: var(--color-primary-600);
	}

	.add-company .item-icon {
		background: var(--color-primary-50);
		color: var(--color-primary-600);
	}

	.add-company .item-name {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-medium);
	}
</style>
