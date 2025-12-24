<script lang="ts">
	// PayGroupSummaryCards - Quick overview cards row
	import type { PayGroup } from '$lib/types/pay-group';
	import { countEnabledBenefits } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
	}

	let { payGroup }: Props = $props();

	// Derived values for summary cards
	const statutorySummary = $derived(() => {
		const exemptions: string[] = [];
		if (payGroup.statutoryDefaults.cppExemptByDefault) exemptions.push('CPP');
		if (payGroup.statutoryDefaults.cpp2ExemptByDefault) exemptions.push('CPP2');
		if (payGroup.statutoryDefaults.eiExemptByDefault) exemptions.push('EI');
		return exemptions.length > 0 ? exemptions.join(', ') + ' Exempt' : 'Standard';
	});

	const wcbSummary = $derived(
		payGroup.wcbConfig.enabled
			? `${(payGroup.wcbConfig.assessmentRate * 100).toFixed(2)}%`
			: 'Not Enabled'
	);

	const benefitsSummary = $derived(() => {
		if (!payGroup.groupBenefits.enabled) return 'Not Enabled';
		const count = countEnabledBenefits(payGroup.groupBenefits);
		return `${count} Active`;
	});

	const deductionsSummary = $derived(() => {
		const customDeductions = payGroup.deductionsConfig?.customDeductions ?? [];
		const count = customDeductions.length;
		if (count === 0) return 'None';
		const defaultEnabled = customDeductions.filter((d) => d.isDefaultEnabled).length;
		return `${count} Total (${defaultEnabled} Default)`;
	});
</script>

<div class="summary-cards">
	<div class="summary-card">
		<div class="card-icon statutory">
			<i class="fas fa-landmark"></i>
		</div>
		<div class="card-content">
			<span class="card-label">Statutory</span>
			<span class="card-value">{statutorySummary()}</span>
		</div>
	</div>

	<div class="summary-card">
		<div class="card-icon wcb" class:disabled={!payGroup.wcbConfig.enabled}>
			<i class="fas fa-hard-hat"></i>
		</div>
		<div class="card-content">
			<span class="card-label">WCB Rate</span>
			<span class="card-value">{wcbSummary}</span>
		</div>
	</div>

	<div class="summary-card">
		<div class="card-icon benefits" class:disabled={!payGroup.groupBenefits.enabled}>
			<i class="fas fa-heartbeat"></i>
		</div>
		<div class="card-content">
			<span class="card-label">Benefits</span>
			<span class="card-value">{benefitsSummary()}</span>
		</div>
	</div>

	<div class="summary-card">
		<div class="card-icon deductions" class:disabled={(payGroup.deductionsConfig?.customDeductions ?? []).length === 0}>
			<i class="fas fa-receipt"></i>
		</div>
		<div class="card-content">
			<span class="card-label">Deductions</span>
			<span class="card-value">{deductionsSummary()}</span>
		</div>
	</div>
</div>

<style>
	.summary-cards {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-4);
	}

	.summary-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-1);
	}

	.card-icon {
		width: 44px;
		height: 44px;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.card-icon i {
		font-size: 18px;
	}

	.card-icon.statutory {
		background: var(--color-primary-50);
		color: var(--color-primary-500);
	}

	.card-icon.wcb {
		background: var(--color-warning-50);
		color: var(--color-warning-600);
	}

	.card-icon.benefits {
		background: var(--color-success-50);
		color: var(--color-success-600);
	}

	.card-icon.deductions {
		background: var(--color-info-50);
		color: var(--color-info-600);
	}

	.card-icon.disabled {
		background: var(--color-surface-100);
		color: var(--color-surface-400);
	}

	.card-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.card-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.card-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	@media (max-width: 900px) {
		.summary-cards {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 480px) {
		.summary-cards {
			grid-template-columns: 1fr;
		}
	}
</style>
