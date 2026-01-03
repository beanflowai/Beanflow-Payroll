<script lang="ts">
	/**
	 * Employee Portal - Profile Page
	 * Shows employee profile with Personal, Tax, and Bank information
	 * Fetches real data from Supabase via getMyProfile()
	 */
	import { onMount, getContext } from 'svelte';
	import ProfileSection from '$lib/components/employee-portal/ProfileSection.svelte';
	import ProfileField from '$lib/components/employee-portal/ProfileField.svelte';
	import EditPersonalInfoModal from '$lib/components/employee-portal/EditPersonalInfoModal.svelte';
	import EditTaxInfoModal from '$lib/components/employee-portal/EditTaxInfoModal.svelte';
	import type { EmployeePortalProfile, PersonalInfoFormData, TaxInfoFormData, PortalCompanyContext } from '$lib/types/employee-portal';
	import { PORTAL_COMPANY_CONTEXT_KEY } from '$lib/types/employee-portal';
	import { getMyProfile } from '$lib/services/employeePortalService';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// Get company context from layout
	const portalContext = getContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY);
	const companyId = $derived(portalContext?.company?.id ?? null);

	// Profile data state
	let profile = $state<EmployeePortalProfile | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Modal states
	let showEditPersonal = $state(false);
	let showEditTax = $state(false);

	// Load profile on mount (use onMount to avoid $effect infinite loop)
	onMount(() => {
		loadProfile();
	});

	async function loadProfile() {
		loading = true;
		error = null;
		try {
			profile = await getMyProfile(companyId ?? undefined);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load profile';
		} finally {
			loading = false;
		}
	}

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	// Handle personal info save - refresh profile data
	function handlePersonalInfoSave(_data: PersonalInfoFormData) {
		loadProfile();
	}

	// Handle tax info submit - refresh profile data
	function handleTaxInfoSubmit(_data: TaxInfoFormData) {
		loadProfile();
	}
</script>

<div class="profile-page">
	{#if loading}
		<!-- Loading State -->
		<div class="loading-state">
			<div class="loading-spinner"></div>
			<p>Loading profile...</p>
		</div>
	{:else if error}
		<!-- Error State -->
		<div class="error-state">
			<div class="error-icon">!</div>
			<h2>Unable to load profile</h2>
			<p>{error}</p>
			<button class="retry-btn" onclick={loadProfile}>Try Again</button>
		</div>
	{:else if profile}
		<!-- Profile Content -->
		<header class="page-header">
			<div class="employee-header">
				<div class="avatar">
					<span class="avatar-initials">
						{profile.firstName[0]}{profile.lastName[0]}
					</span>
				</div>
				<div class="employee-info">
					<h1 class="employee-name">{profile.firstName} {profile.lastName}</h1>
					{#if profile.jobTitle}
						<p class="employee-title">{profile.jobTitle}</p>
					{/if}
					{#if profile.hireDate}
						<p class="employee-hire-date">Hired: {formatShortDate(profile.hireDate)}</p>
					{/if}
				</div>
			</div>
		</header>

		<div class="profile-sections">
			<!-- Personal Information -->
			<ProfileSection
				id="personal"
				icon="personal"
				title="Personal Information"
				onEdit={() => (showEditPersonal = true)}
			>
				<ProfileField label="Email" value={profile.email} />
				<ProfileField label="Phone" value={profile.phone || 'Not provided'} />
				<ProfileField
					label="Address"
					value={profile.address.street
						? `${profile.address.street}\n${profile.address.city}, ${profile.address.province} ${profile.address.postalCode}`
						: 'Not provided'}
				/>
				{#if profile.emergencyContact}
					<ProfileField
						label="Emergency Contact"
						value={`${profile.emergencyContact.name} (${profile.emergencyContact.relationship}) - ${profile.emergencyContact.phone}`}
					/>
				{:else}
					<ProfileField label="Emergency Contact" value="Not provided" />
				{/if}
			</ProfileSection>

			<!-- Tax Information -->
			<ProfileSection
				id="tax"
				icon="tax"
				title="Tax Information (TD1)"
				onEdit={() => (showEditTax = true)}
			>
				<ProfileField label="SIN" value={profile.sin || 'Not on file'} />
				<ProfileField
					label="Federal Additional Claims"
					value={formatMoney(profile.federalAdditionalClaims)}
				/>
				<ProfileField
					label="Provincial Additional Claims"
					value={formatMoney(profile.provincialAdditionalClaims)}
				/>
			</ProfileSection>

			<!-- Bank Information - hidden until direct deposit feature is implemented
			<ProfileSection
				id="bank"
				icon="bank"
				title="Bank Information"
			>
				<ProfileField label="Bank" value={profile.bankName || 'Not provided'} />
				<ProfileField label="Account" value={profile.accountNumber} masked />
				<ProfileField label="Transit" value={profile.transitNumber || 'Not provided'} />
				<ProfileField label="Institution" value={profile.institutionNumber || 'Not provided'} />
				<div class="bank-note">
					<p>To update bank information, please contact your employer.</p>
				</div>
			</ProfileSection>
			-->
		</div>

	{/if}
</div>

<!-- Edit Modals - rendered outside conditional to avoid recreation -->
{#if profile && showEditPersonal}
	<EditPersonalInfoModal
		bind:visible={showEditPersonal}
		initialData={{
			phone: profile.phone || '',
			address: {
				street: profile.address.street,
				city: profile.address.city,
				province: profile.address.province,
				postalCode: profile.address.postalCode
			},
			emergencyContact: profile.emergencyContact || {
				name: '',
				relationship: '',
				phone: ''
			}
		}}
		onclose={() => (showEditPersonal = false)}
		onSave={handlePersonalInfoSave}
	/>
{/if}

{#if profile && showEditTax}
	<EditTaxInfoModal
		bind:visible={showEditTax}
		initialData={{
			sin: profile.sin,
			federalAdditionalClaims: profile.federalAdditionalClaims,
			provincialAdditionalClaims: profile.provincialAdditionalClaims,
			provinceOfEmployment: profile.provinceOfEmployment
		}}
		onclose={() => (showEditTax = false)}
		onSubmit={handleTaxInfoSubmit}
	/>
{/if}

<style>
	.profile-page {
		max-width: 800px;
		margin: 0 auto;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12);
		color: var(--color-surface-600);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--spacing-4);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12);
		text-align: center;
	}

	.error-icon {
		width: 48px;
		height: 48px;
		background: var(--color-danger-100);
		color: var(--color-danger-600);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
		margin-bottom: var(--spacing-4);
	}

	.error-state h2 {
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-2) 0;
	}

	.error-state p {
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4) 0;
	}

	.retry-btn {
		padding: var(--spacing-3) var(--spacing-6);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: background var(--transition-fast);
	}

	.retry-btn:hover {
		background: var(--color-primary-600);
	}

	/* Profile Content */
	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.employee-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
	}

	.avatar {
		width: 72px;
		height: 72px;
		background: var(--color-primary-100);
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.avatar-initials {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-primary-600);
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-name {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.employee-title {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin: 0;
	}

	.employee-hire-date {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.profile-sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.employee-header {
			flex-direction: column;
			text-align: center;
		}

		.employee-name {
			font-size: var(--font-size-title-large);
		}
	}
</style>
