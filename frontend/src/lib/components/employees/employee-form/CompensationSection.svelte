<script lang="ts">
	interface Props {
		mode: 'create' | 'edit';
		employeeId?: string;
		compensationType: 'salaried' | 'hourly';
		annualSalary: number;
		hourlyRate: number;
		effectiveDate?: string;
		errors: Record<string, string>;
		onCompensationTypeChange: (type: 'salaried' | 'hourly') => void;
		onAnnualSalaryChange: (value: number) => void;
		onHourlyRateChange: (value: number) => void;
	}

	let {
		mode,
		employeeId,
		compensationType,
		annualSalary,
		hourlyRate,
		effectiveDate,
		errors,
		onCompensationTypeChange,
		onAnnualSalaryChange,
		onHourlyRateChange
	}: Props = $props();

	// Format currency for display
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(amount);
	}

	// Format date for display
	function formatDate(dateString?: string): string {
		if (!dateString) return 'Not set';
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Get display value based on compensation type
	const displayAmount = $derived(() => {
		if (compensationType === 'salaried') {
			return `${formatCurrency(annualSalary)} / year`;
		} else {
			return `${formatCurrency(hourlyRate)} / hour`;
		}
	});

	const displayType = $derived(compensationType === 'salaried' ? 'Salaried' : 'Hourly');
</script>

{#if mode === 'edit'}
	<!-- Edit Mode: Read-only display with CTA button -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">
			Compensation
		</h3>

		<!-- Info Card -->
		<div class="compensation-info-card">
			<!-- Compensation Type -->
			<div class="info-row">
				<div class="info-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
						<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
					</svg>
				</div>
				<div class="info-content">
					<span class="info-label">Compensation Type</span>
					<span class="info-value">{displayType}</span>
				</div>
			</div>

			<!-- Current Amount -->
			<div class="info-row">
				<div class="info-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="12" y1="1" x2="12" y2="23"></line>
						<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
					</svg>
				</div>
				<div class="info-content">
					<span class="info-label"
						>Current {compensationType === 'salaried' ? 'Salary' : 'Rate'}</span
					>
					<span class="info-value">{displayAmount()}</span>
				</div>
			</div>

			<!-- Effective Date -->
			<div class="info-row">
				<div class="info-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
						<line x1="16" y1="2" x2="16" y2="6"></line>
						<line x1="8" y1="2" x2="8" y2="6"></line>
						<line x1="3" y1="10" x2="21" y2="10"></line>
					</svg>
				</div>
				<div class="info-content">
					<span class="info-label">Effective Date</span>
					<span class="info-value">{formatDate(effectiveDate)}</span>
				</div>
			</div>
		</div>

		<!-- CTA Button -->
		<a
			href={`/employees/${employeeId}/compensation`}
			class="adjust-compensation-btn"
			aria-label="Navigate to adjust compensation page"
		>
			<span>Adjust Compensation</span>
			<svg
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				class="arrow-icon"
			>
				<line x1="5" y1="12" x2="19" y2="12"></line>
				<polyline points="12 5 19 12 12 19"></polyline>
			</svg>
		</a>
	</section>
{:else}
	<!-- Create Mode: Editable form (existing behavior) -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">
			Compensation
		</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2 col-span-full">
				<span class="text-body-small font-medium text-surface-700">Compensation Type *</span>
				<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="salaried"
							checked={compensationType === 'salaried'}
							onchange={() => onCompensationTypeChange('salaried')}
						/>
						<span>Annual Salary</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="hourly"
							checked={compensationType === 'hourly'}
							onchange={() => onCompensationTypeChange('hourly')}
						/>
						<span>Hourly Rate</span>
					</label>
				</div>
			</div>

			{#if compensationType === 'salaried'}
				<div class="flex flex-col gap-2">
					<label for="annualSalary" class="text-body-small font-medium text-surface-700"
						>Annual Salary *</label
					>
					<div
						class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10"
					>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="annualSalary"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							value={annualSalary}
							oninput={(e) => onAnnualSalaryChange(parseFloat(e.currentTarget.value) || 0)}
							min="0"
							step="100"
						/>
					</div>
					{#if errors.annualSalary}
						<span class="text-auxiliary-text text-error-600">{errors.annualSalary}</span>
					{/if}
				</div>
			{:else}
				<div class="flex flex-col gap-2">
					<label for="hourlyRate" class="text-body-small font-medium text-surface-700"
						>Hourly Rate *</label
					>
					<div
						class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10"
					>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="hourlyRate"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							value={hourlyRate}
							oninput={(e) => onHourlyRateChange(parseFloat(e.currentTarget.value) || 0)}
							min="0"
							step="0.01"
						/>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">/hr</span>
					</div>
					{#if errors.hourlyRate}
						<span class="text-auxiliary-text text-error-600">{errors.hourlyRate}</span>
					{/if}
				</div>
			{/if}
		</div>
	</section>
{/if}

<style>
	/* Read-only info card */
	.compensation-info-card {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
		border: 1px solid var(--color-surface-300);
		border-radius: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.info-row {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}

	.info-icon {
		flex-shrink: 0;
		width: 2.5rem;
		height: 2.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--color-primary-50), var(--color-primary-100));
		border-radius: 0.5rem;
		color: var(--color-primary-600);
	}

	.info-icon svg {
		width: 1.5rem;
		height: 1.5rem;
	}

	.info-content {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
	}

	.info-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.info-value {
		font-size: var(--font-size-body-content-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		line-height: 1.5;
	}

	/* CTA Button */
	.adjust-compensation-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.875rem 1.5rem;
		background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-700));
		color: white;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		text-decoration: none;
		border-radius: 0.5rem;
		box-shadow: var(--shadow-md3-1);
		cursor: pointer;
		transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
		/* Ensure minimum touch target size */
		min-height: 44px;
	}

	.adjust-compensation-btn:hover {
		background: linear-gradient(135deg, var(--color-primary-700), var(--color-primary-800));
		box-shadow: var(--shadow-md3-2);
		transform: translateY(-1px);
	}

	.adjust-compensation-btn:focus {
		outline: none;
		box-shadow: 0 0 0 4px rgba(152, 16, 250, 0.3);
	}

	.adjust-compensation-btn:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 4px;
	}

	.adjust-compensation-btn:active {
		transform: translateY(0);
	}

	.arrow-icon {
		width: 1.25rem;
		height: 1.25rem;
		transition: transform 150ms cubic-bezier(0.4, 0, 0.2, 1);
	}

	.adjust-compensation-btn:hover .arrow-icon {
		transform: translateX(4px);
	}

	/* Responsive */
	@media (max-width: 640px) {
		.compensation-info-card {
			padding: 1rem;
		}

		.info-icon {
			width: 2rem;
			height: 2rem;
		}

		.info-icon svg {
			width: 1.25rem;
			height: 1.25rem;
		}
	}

	/* Reduced motion preference */
	@media (prefers-reduced-motion: reduce) {
		.adjust-compensation-btn,
		.arrow-icon {
			transition: none;
		}

		.adjust-compensation-btn:hover {
			transform: none;
		}

		.adjust-compensation-btn:hover .arrow-icon {
			transform: none;
		}
	}
</style>
