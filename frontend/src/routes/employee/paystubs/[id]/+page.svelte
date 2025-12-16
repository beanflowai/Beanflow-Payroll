<script lang="ts">
	/**
	 * Employee Portal - Paystub Detail Page
	 * Shows full paystub details for a specific pay period
	 */
	import { page } from '$app/stores';
	import PaystubDetail from '$lib/components/employee-portal/PaystubDetail.svelte';
	import type { PaystubDetail as PaystubDetailType } from '$lib/types/employee-portal';

	const paystubId = $page.params.id;

	// Mock data for static UI
	const paystub: PaystubDetailType = {
		id: paystubId,
		payDate: '2025-12-20',
		payPeriodStart: '2025-12-01',
		payPeriodEnd: '2025-12-15',
		grossPay: 2884.62,
		totalDeductions: 689.17,
		netPay: 2195.45,
		companyName: 'Acme Corporation',
		companyAddress: '123 Business St, Toronto ON',
		employeeName: 'Sarah Johnson',
		earnings: [
			{ type: 'Regular Pay', hours: 80, amount: 2884.62 },
			{ type: 'Overtime', hours: 0, amount: 0 },
			{ type: 'Vacation Pay', amount: 0 }
		],
		deductions: [
			{ type: 'CPP', amount: 140.42 },
			{ type: 'EI', amount: 49.04 },
			{ type: 'Federal Tax', amount: 310.0 },
			{ type: 'Provincial Tax', amount: 139.71 },
			{ type: 'RRSP', amount: 50.0 }
		],
		ytd: {
			grossEarnings: 69230.88,
			cppPaid: 3356.1,
			eiPaid: 1077.48,
			taxPaid: 12450.0
		}
	};

	function handleDownload() {
		// TODO: Implement PDF download
		console.log('Download PDF for paystub:', paystubId);
	}
</script>

<div class="paystub-detail-page">
	<header class="page-header">
		<a href="/employee/paystubs" class="back-link">
			<svg viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
					clip-rule="evenodd"
				/>
			</svg>
			Back to Paystubs
		</a>
		<button class="download-btn" onclick={handleDownload}>
			<svg viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
					clip-rule="evenodd"
				/>
			</svg>
			Download PDF
		</button>
	</header>

	<PaystubDetail {paystub} onDownload={handleDownload} />
</div>

<style>
	.paystub-detail-page {
		max-width: 700px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
	}

	.back-link {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.back-link:hover {
		color: var(--color-surface-900);
	}

	.back-link svg {
		width: 16px;
		height: 16px;
	}

	.download-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: white;
		background: var(--color-primary-500);
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.download-btn:hover {
		background: var(--color-primary-600);
	}

	.download-btn svg {
		width: 16px;
		height: 16px;
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.page-header {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-4);
		}

		.download-btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
