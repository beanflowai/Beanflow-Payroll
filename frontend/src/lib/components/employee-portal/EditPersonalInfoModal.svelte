<script lang="ts">
	/**
	 * EditPersonalInfoModal - Edit personal information form
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { PersonalInfoFormData } from '$lib/types/employee-portal';
	import { CANADIAN_PROVINCES, RELATIONSHIP_OPTIONS } from '$lib/types/employee-portal';
	import { updatePersonalInfo } from '$lib/services/employeePortalService';

	interface Props {
		visible: boolean;
		initialData: PersonalInfoFormData;
		onclose: () => void;
		onSave: (data: PersonalInfoFormData) => void;
	}

	let { visible = $bindable(), initialData, onclose, onSave }: Props = $props();

	// Extract initial values once at component creation (form snapshot pattern)
	const initial = (() => {
		const data = initialData;
		return {
			phone: data.phone,
			street: data.address.street,
			city: data.address.city,
			province: data.address.province,
			postalCode: data.address.postalCode,
			emergencyName: data.emergencyContact.name,
			emergencyRelationship: data.emergencyContact.relationship,
			emergencyPhone: data.emergencyContact.phone
		};
	})();

	// Form state
	let phone = $state(initial.phone);
	let street = $state(initial.street);
	let city = $state(initial.city);
	let province = $state(initial.province);
	let postalCode = $state(initial.postalCode);
	let emergencyName = $state(initial.emergencyName);
	let emergencyRelationship = $state(initial.emergencyRelationship);
	let emergencyPhone = $state(initial.emergencyPhone);

	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit() {
		isSubmitting = true;
		error = null;

		const data: PersonalInfoFormData = {
			phone,
			address: {
				street,
				city,
				province,
				postalCode
			},
			emergencyContact: {
				name: emergencyName,
				relationship: emergencyRelationship,
				phone: emergencyPhone
			}
		};

		try {
			await updatePersonalInfo(data);
			onSave(data);
			onclose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save changes';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<BaseModal {visible} {onclose} size="medium" title="Edit Personal Information">
	<form
		class="edit-form"
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
	>
		{#if error}
			<div class="error-banner">{error}</div>
		{/if}
		<!-- Phone -->
		<div class="form-group">
			<label for="phone" class="form-label">Phone Number</label>
			<input
				id="phone"
				type="tel"
				class="form-input"
				bind:value={phone}
				placeholder="(416) 555-1234"
			/>
		</div>

		<div class="form-divider"></div>

		<!-- Address Section -->
		<h3 class="section-subtitle">Home Address</h3>

		<div class="form-group">
			<label for="street" class="form-label">Street Address</label>
			<input
				id="street"
				type="text"
				class="form-input"
				bind:value={street}
				placeholder="123 Main St, Apt 4B"
			/>
		</div>

		<div class="form-row">
			<div class="form-group flex-2">
				<label for="city" class="form-label">City</label>
				<input id="city" type="text" class="form-input" bind:value={city} placeholder="Toronto" />
			</div>
			<div class="form-group flex-1">
				<label for="province" class="form-label">Province</label>
				<select id="province" class="form-select" bind:value={province}>
					{#each CANADIAN_PROVINCES as prov (prov.code)}
						<option value={prov.code}>{prov.name}</option>
					{/each}
				</select>
			</div>
		</div>

		<div class="form-group">
			<label for="postalCode" class="form-label">Postal Code</label>
			<input
				id="postalCode"
				type="text"
				class="form-input postal-code-input"
				bind:value={postalCode}
				placeholder="M5V 2T6"
			/>
		</div>

		<div class="form-divider"></div>

		<!-- Emergency Contact Section -->
		<h3 class="section-subtitle">Emergency Contact</h3>

		<div class="form-row">
			<div class="form-group flex-2">
				<label for="emergencyName" class="form-label">Name</label>
				<input
					id="emergencyName"
					type="text"
					class="form-input"
					bind:value={emergencyName}
					placeholder="John Johnson"
				/>
			</div>
			<div class="form-group flex-1">
				<label for="emergencyRelationship" class="form-label">Relationship</label>
				<select id="emergencyRelationship" class="form-select" bind:value={emergencyRelationship}>
					{#each RELATIONSHIP_OPTIONS as rel (rel)}
						<option value={rel}>{rel}</option>
					{/each}
				</select>
			</div>
		</div>

		<div class="form-group">
			<label for="emergencyPhone" class="form-label">Phone</label>
			<input
				id="emergencyPhone"
				type="tel"
				class="form-input"
				bind:value={emergencyPhone}
				placeholder="(416) 555-5678"
			/>
		</div>

		<!-- Actions -->
		<div class="form-actions">
			<button type="button" class="btn-cancel" onclick={onclose} disabled={isSubmitting}>
				Cancel
			</button>
			<button type="submit" class="btn-save" disabled={isSubmitting}>
				{#if isSubmitting}
					Saving...
				{:else}
					Save Changes
				{/if}
			</button>
		</div>
	</form>
</BaseModal>

<style>
	.edit-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.error-banner {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-md);
		color: var(--color-error-700);
		font-size: var(--font-size-auxiliary-text);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-input,
	.form-select {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		width: 100%;
		box-sizing: border-box;
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.postal-code-input {
		max-width: 150px;
	}

	.form-row {
		display: flex;
		gap: var(--spacing-4);
	}

	.flex-1 {
		flex: 1;
	}

	.flex-2 {
		flex: 2;
	}

	.form-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-2) 0;
	}

	.section-subtitle {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin: 0;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-cancel,
	.btn-save {
		padding: var(--spacing-3) var(--spacing-6);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-cancel {
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-100);
	}

	.btn-save {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.btn-save:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-cancel:disabled,
	.btn-save:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Mobile adjustments */
	@media (max-width: 480px) {
		.form-row {
			flex-direction: column;
			gap: var(--spacing-4);
		}
	}
</style>
