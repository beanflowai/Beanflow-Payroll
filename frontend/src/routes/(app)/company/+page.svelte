<script lang="ts">
	// Company page - Tab-based layout for company settings
	// Phase 0 static UI prototype with 3 tabs: Profile, Pay Groups, Integration
	import ProfileTab from '$lib/components/company/ProfileTab.svelte';
	import PayGroupsTab from '$lib/components/company/PayGroupsTab.svelte';
	import IntegrationTab from '$lib/components/company/IntegrationTab.svelte';

	// Tab types
	type TabId = 'profile' | 'pay-groups' | 'integration';

	interface Tab {
		id: TabId;
		label: string;
		icon: string;
	}

	const tabs: Tab[] = [
		{ id: 'profile', label: 'Profile', icon: 'fa-building' },
		{ id: 'pay-groups', label: 'Pay Groups', icon: 'fa-clipboard-list' },
		{ id: 'integration', label: 'Integration', icon: 'fa-link' }
	];

	// Active tab state
	let activeTab = $state<TabId>('profile');

	function handleTabClick(tabId: TabId) {
		activeTab = tabId;
	}
</script>

<svelte:head>
	<title>Company - BeanFlow Payroll</title>
</svelte:head>

<div class="company-page">
	<header class="page-header">
		<h1 class="page-title">Company</h1>
		<p class="page-subtitle">Manage your company settings and payroll configuration</p>
	</header>

	<!-- Tab Navigation -->
	<!-- svelte-ignore a11y_no_noninteractive_element_to_interactive_role -->
	<nav class="tab-navigation" role="tablist" aria-label="Company settings">
		{#each tabs as tab (tab.id)}
			<button
				class="tab-button"
				class:active={activeTab === tab.id}
				role="tab"
				aria-selected={activeTab === tab.id}
				aria-controls="tabpanel-{tab.id}"
				id="tab-{tab.id}"
				onclick={() => handleTabClick(tab.id)}
			>
				<i class="fas {tab.icon}"></i>
				<span>{tab.label}</span>
			</button>
		{/each}
	</nav>

	<!-- Tab Content -->
	<div class="tab-content">
		{#if activeTab === 'profile'}
			<div
				id="tabpanel-profile"
				role="tabpanel"
				aria-labelledby="tab-profile"
				class="tab-panel"
			>
				<ProfileTab />
			</div>
		{:else if activeTab === 'pay-groups'}
			<div
				id="tabpanel-pay-groups"
				role="tabpanel"
				aria-labelledby="tab-pay-groups"
				class="tab-panel"
			>
				<PayGroupsTab />
			</div>
		{:else if activeTab === 'integration'}
			<div
				id="tabpanel-integration"
				role="tabpanel"
				aria-labelledby="tab-integration"
				class="tab-panel"
			>
				<IntegrationTab />
			</div>
		{/if}
	</div>
</div>

<style>
	.company-page {
		max-width: 900px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.page-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Tab Navigation */
	.tab-navigation {
		display: flex;
		gap: var(--spacing-1);
		border-bottom: 1px solid var(--color-surface-200);
		margin-bottom: var(--spacing-6);
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
		scrollbar-width: none;
	}

	.tab-navigation::-webkit-scrollbar {
		display: none;
	}

	.tab-button {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
		white-space: nowrap;
		margin-bottom: -1px;
	}

	.tab-button:hover {
		color: var(--color-surface-800);
		background: var(--color-surface-50);
	}

	.tab-button.active {
		color: var(--color-primary-600);
		border-bottom-color: var(--color-primary-500);
		font-weight: var(--font-weight-semibold);
	}

	.tab-button i {
		font-size: 14px;
	}

	/* Tab Content */
	.tab-content {
		min-height: 400px;
	}

	.tab-panel {
		animation: fadeIn 0.2s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 640px) {
		.tab-button {
			padding: var(--spacing-3);
		}

		.tab-button span {
			display: none;
		}

		.tab-button i {
			font-size: 18px;
		}
	}
</style>
