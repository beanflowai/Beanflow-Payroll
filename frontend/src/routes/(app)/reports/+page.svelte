<script lang="ts">
	const reportTypes = [
		{ id: 'remittance', title: 'CRA Remittance Summary', description: 'Monthly payroll deduction remittance report', icon: 'fa-file-invoice-dollar', href: '/remittance', color: 'bg-primary-100 text-primary-600' },
		{ id: 'ytd', title: 'Year-to-Date Summary', description: 'Cumulative payroll totals for the year', icon: 'fa-calendar-alt', color: 'bg-success-100 text-success-600' },
		{ id: 't4', title: 'T4 Summary', description: 'Annual T4 slip preparation and submission', icon: 'fa-file-alt', href: '/reports/t4', color: 'bg-warning-100 text-warning-600' },
		{ id: 'roe', title: 'ROE Report', description: 'Record of Employment generation', icon: 'fa-user-minus', color: 'bg-secondary-100 text-secondary-600' },
		{ id: 'payroll-register', title: 'Payroll Register', description: 'Detailed breakdown of each payroll run', icon: 'fa-list-alt', color: 'bg-tertiary-100 text-tertiary-600' },
		{ id: 'deduction', title: 'Deduction Report', description: 'Summary of all payroll deductions', icon: 'fa-minus-circle', color: 'bg-error-100 text-error-600' }
	];

</script>

<svelte:head>
	<title>Reports - BeanFlow Payroll</title>
</svelte:head>

<div class="max-w-[1200px] mx-auto">
	<header class="mb-8">
		<h1 class="text-headline-minimum font-semibold text-surface-800 mb-1">Reports</h1>
		<p class="text-body-content text-surface-600">Generate and download payroll reports</p>
	</header>

	<!-- Report Types Grid -->
	<section class="mb-8">
		<h2 class="text-title-medium font-semibold text-surface-800 mb-4">Generate Report</h2>
		<div class="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4">
			{#each reportTypes as report (report.id)}
				{#if report.href}
					<a href={report.href} class="flex items-center gap-4 p-5 bg-white border border-surface-200 rounded-xl hover:border-primary-300 hover:shadow-md3-1 hover:-translate-y-0.5 transition-all no-underline">
						<div class="w-12 h-12 min-w-12 rounded-lg flex items-center justify-center text-xl {report.color}">
							<i class="fas {report.icon}"></i>
						</div>
						<div class="flex-1">
							<h3 class="text-body-content-large font-semibold text-surface-800 mb-1">{report.title}</h3>
							<p class="text-auxiliary-text text-surface-600">{report.description}</p>
						</div>
						<i class="fas fa-chevron-right text-sm text-surface-400"></i>
					</a>
				{:else}
					<button disabled class="flex items-center gap-4 p-5 bg-white border border-surface-200 rounded-xl opacity-70 cursor-not-allowed text-left">
						<div class="w-12 h-12 min-w-12 rounded-lg flex items-center justify-center text-xl {report.color}">
							<i class="fas {report.icon}"></i>
						</div>
						<div class="flex-1">
							<h3 class="text-body-content-large font-semibold text-surface-800 mb-1">{report.title}</h3>
							<p class="text-auxiliary-text text-surface-600">{report.description}</p>
						</div>
						<span class="text-auxiliary-text font-medium text-surface-500 bg-surface-100 px-2 py-1 rounded whitespace-nowrap">Coming Soon</span>
					</button>
				{/if}
			{/each}
		</div>
	</section>

	<!-- Recent Reports -->
	<section class="mb-8">
		<h2 class="text-title-medium font-semibold text-surface-800 mb-4">Recent Reports</h2>
		<div class="bg-white rounded-xl shadow-md3-1 p-8 text-center">
			<i class="fas fa-inbox text-4xl text-surface-300 mb-4"></i>
			<p class="text-body-content text-surface-500 m-0">No reports generated yet. Select a report type above to get started.</p>
		</div>
	</section>
</div>
