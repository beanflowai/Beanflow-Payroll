<script lang="ts">
	/**
	 * Employee Portal - Profile Page
	 * Shows employee profile with Personal, Tax, and Bank information
	 */
	import ProfileSection from '$lib/components/employee-portal/ProfileSection.svelte';
	import ProfileField from '$lib/components/employee-portal/ProfileField.svelte';
	import type { EmployeePortalProfile } from '$lib/types/employee-portal';

	// Modal states
	let showEditPersonal = $state(false);
	let showEditTax = $state(false);
	let showEditBank = $state(false);

	// Mock data for static UI
	const profile: EmployeePortalProfile = {
		id: 'emp-001',
		firstName: 'Sarah',
		lastName: 'Johnson',
		email: 'sarah@example.com',
		phone: '(416) 555-1234',
		address: {
			street: '123 Main St, Apt 4B',
			city: 'Toronto',
			province: 'ON',
			postalCode: 'M5V 2T6'
		},
		emergencyContact: {
			name: 'John Johnson',
			relationship: 'Spouse',
			phone: '(416) 555-5678'
		},
		sin: '***-***-789',
		federalClaimAmount: 16129,
		provincialClaimAmount: 12399,
		additionalTaxPerPeriod: 0,
		bankName: 'TD Canada Trust',
		transitNumber: '12345',
		institutionNumber: '004',
		accountNumber: '****4567',
		hireDate: '2023-01-15',
		jobTitle: 'Software Developer',
		provinceOfEmployment: 'Ontario'
	};

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' });
	}
</script>

<div class="profile-page">
	<header class="page-header">
		<div class="employee-header">
			<div class="avatar">
				<span class="avatar-initials">
					{profile.firstName[0]}{profile.lastName[0]}
				</span>
			</div>
			<div class="employee-info">
				<h1 class="employee-name">{profile.firstName} {profile.lastName}</h1>
				<p class="employee-title">{profile.jobTitle}</p>
				<p class="employee-hire-date">Hired: {formatDate(profile.hireDate)}</p>
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
				value={`${profile.address.street}\n${profile.address.city}, ${profile.address.province} ${profile.address.postalCode}`}
			/>
			{#if profile.emergencyContact}
				<ProfileField
					label="Emergency Contact"
					value={`${profile.emergencyContact.name} (${profile.emergencyContact.relationship}) - ${profile.emergencyContact.phone}`}
				/>
			{/if}
		</ProfileSection>

		<!-- Tax Information -->
		<ProfileSection
			id="tax"
			icon="tax"
			title="Tax Information (TD1)"
			onEdit={() => (showEditTax = true)}
		>
			<ProfileField label="SIN" value={profile.sin} masked />
			<ProfileField
				label="Federal Claim"
				value={`${formatMoney(profile.federalClaimAmount)} (Basic Personal Amount)`}
			/>
			<ProfileField
				label="Provincial Claim"
				value={`${formatMoney(profile.provincialClaimAmount)} (Ontario BPA)`}
			/>
			<ProfileField
				label="Additional Tax"
				value={`${formatMoney(profile.additionalTaxPerPeriod)} per pay period`}
			/>
		</ProfileSection>

		<!-- Bank Information -->
		<ProfileSection
			id="bank"
			icon="bank"
			title="Bank Information"
			onEdit={() => (showEditBank = true)}
		>
			<ProfileField label="Bank" value={profile.bankName} />
			<ProfileField label="Account" value={profile.accountNumber} masked />
			<ProfileField label="Transit" value={profile.transitNumber} />
			<ProfileField label="Institution" value={profile.institutionNumber} />
		</ProfileSection>
	</div>
</div>

<!-- Edit Modals (placeholders - will be implemented next) -->
{#if showEditPersonal}
	<div class="modal-placeholder" onclick={() => (showEditPersonal = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<h2>Edit Personal Information</h2>
			<p>Modal content will be implemented</p>
			<button onclick={() => (showEditPersonal = false)}>Close</button>
		</div>
	</div>
{/if}

{#if showEditTax}
	<div class="modal-placeholder" onclick={() => (showEditTax = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<h2>Edit Tax Information</h2>
			<p>Modal content will be implemented</p>
			<button onclick={() => (showEditTax = false)}>Close</button>
		</div>
	</div>
{/if}

{#if showEditBank}
	<div class="modal-placeholder" onclick={() => (showEditBank = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<h2>Edit Bank Information</h2>
			<p>Modal content will be implemented</p>
			<button onclick={() => (showEditBank = false)}>Close</button>
		</div>
	</div>
{/if}

<style>
	.profile-page {
		max-width: 800px;
		margin: 0 auto;
	}

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

	/* Placeholder modal styles */
	.modal-placeholder {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
	}

	.modal-content {
		background: white;
		padding: var(--spacing-6);
		border-radius: var(--radius-xl);
		max-width: 400px;
		width: 90%;
	}

	.modal-content h2 {
		margin: 0 0 var(--spacing-4) 0;
	}

	.modal-content button {
		margin-top: var(--spacing-4);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
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
