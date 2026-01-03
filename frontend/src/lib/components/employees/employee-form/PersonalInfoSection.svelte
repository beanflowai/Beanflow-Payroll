<script lang="ts">
	import type { Employee } from '$lib/types/employee';

	interface Props {
		firstName: string;
		lastName: string;
		sin: string;
		email: string;
		addressStreet: string;
		addressCity: string;
		addressPostalCode: string;
		mode: 'create' | 'edit';
		employee: Employee | null;
		errors: Record<string, string>;
		onFirstNameChange: (value: string) => void;
		onLastNameChange: (value: string) => void;
		onSinChange: (value: string) => void;
		onEmailChange: (value: string) => void;
		onAddressStreetChange: (value: string) => void;
		onAddressCityChange: (value: string) => void;
		onAddressPostalCodeChange: (value: string) => void;
	}

	let {
		firstName,
		lastName,
		sin,
		email,
		addressStreet,
		addressCity,
		addressPostalCode,
		mode,
		employee,
		errors,
		onFirstNameChange,
		onLastNameChange,
		onSinChange,
		onEmailChange,
		onAddressStreetChange,
		onAddressCityChange,
		onAddressPostalCodeChange
	}: Props = $props();
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Personal Information</h3>
	<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
		<div class="flex flex-col gap-2">
			<label for="firstName" class="text-body-small font-medium text-surface-700">First Name *</label>
			<input
				id="firstName"
				type="text"
				class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.firstName ? 'border-error-500' : 'border-surface-300'}"
				value={firstName}
				oninput={(e) => onFirstNameChange(e.currentTarget.value)}
			/>
			{#if errors.firstName}
				<span class="text-auxiliary-text text-error-600">{errors.firstName}</span>
			{/if}
		</div>

		<div class="flex flex-col gap-2">
			<label for="lastName" class="text-body-small font-medium text-surface-700">Last Name *</label>
			<input
				id="lastName"
				type="text"
				class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.lastName ? 'border-error-500' : 'border-surface-300'}"
				value={lastName}
				oninput={(e) => onLastNameChange(e.currentTarget.value)}
			/>
			{#if errors.lastName}
				<span class="text-auxiliary-text text-error-600">{errors.lastName}</span>
			{/if}
		</div>

		<div class="flex flex-col gap-2">
			<label for="sin" class="text-body-small font-medium text-surface-700">SIN {mode === 'create' ? '*' : ''}</label>
			{#if mode === 'create'}
				<input
					id="sin"
					type="text"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.sin ? 'border-error-500' : 'border-surface-300'}"
					value={sin}
					oninput={(e) => onSinChange(e.currentTarget.value)}
					placeholder="123-456-789"
					maxlength="11"
				/>
				{#if errors.sin}
					<span class="text-auxiliary-text text-error-600">{errors.sin}</span>
				{/if}
			{:else}
				<input
					id="sin"
					type="text"
					class="p-3 border border-surface-300 rounded-md text-body-content bg-surface-100 text-surface-500 cursor-not-allowed"
					value={employee?.sin ?? '***-***-***'}
					readonly
					disabled
				/>
				<span class="text-auxiliary-text text-surface-500">SIN cannot be changed after creation</span>
			{/if}
		</div>

		<div class="flex flex-col gap-2">
			<label for="email" class="text-body-small font-medium text-surface-700">Email</label>
			<input
				id="email"
				type="email"
				class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.email ? 'border-error-500' : 'border-surface-300'}"
				value={email}
				oninput={(e) => onEmailChange(e.currentTarget.value)}
				placeholder="employee@company.com"
			/>
			{#if errors.email}
				<span class="text-auxiliary-text text-error-600">{errors.email}</span>
			{/if}
		</div>

		<!-- Address Fields -->
		<div class="flex flex-col gap-2 col-span-full">
			<label for="addressStreet" class="text-body-small font-medium text-surface-700">Street Address</label>
			<input
				id="addressStreet"
				type="text"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={addressStreet}
				oninput={(e) => onAddressStreetChange(e.currentTarget.value)}
				placeholder="e.g., 123 Main St, Unit 4"
			/>
		</div>

		<div class="flex flex-col gap-2">
			<label for="addressCity" class="text-body-small font-medium text-surface-700">City</label>
			<input
				id="addressCity"
				type="text"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={addressCity}
				oninput={(e) => onAddressCityChange(e.currentTarget.value)}
				placeholder="e.g., Toronto"
			/>
		</div>

		<div class="flex flex-col gap-2">
			<label for="addressPostalCode" class="text-body-small font-medium text-surface-700">Postal Code</label>
			<input
				id="addressPostalCode"
				type="text"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={addressPostalCode}
				oninput={(e) => onAddressPostalCodeChange(e.currentTarget.value)}
				placeholder="e.g., M5V 1A1"
				maxlength="7"
			/>
		</div>
	</div>
</section>
