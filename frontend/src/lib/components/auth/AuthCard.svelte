<script lang="ts">
	interface Props {
		title: string;
		subtitle: string;
		error?: string | null;
		loading?: boolean;
		children?: import('svelte').Snippet;
	}

	let { title, subtitle, error = null, loading = false, children }: Props = $props();
</script>

<div
	class="bg-white/85 backdrop-blur-xl border border-white/50 rounded-3xl p-8 max-sm:p-6 max-sm:rounded-[20px] shadow-[0_8px_32px_rgba(31,38,135,0.1),0_2px_8px_rgba(31,38,135,0.05)] animate-fade-in-up"
	role="main"
	aria-busy={loading}
>
	<!-- Header -->
	<div class="text-center mb-6">
		<h2 class="text-title-large max-sm:text-title-medium font-semibold text-surface-800 mb-2 leading-tight">
			{title}
		</h2>
		<p class="text-body-content text-surface-600 leading-relaxed">
			{subtitle}
		</p>
	</div>

	<!-- Error message -->
	{#if error}
		<div
			class="flex items-center gap-3 px-4 py-3 bg-error-500/10 border border-error-500/20 rounded-xl mb-4 animate-shake"
			role="alert"
			aria-live="polite"
		>
			<svg
				class="w-5 h-5 text-error-600 shrink-0"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				aria-hidden="true"
			>
				<path
					fill-rule="evenodd"
					d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
					clip-rule="evenodd"
				/>
			</svg>
			<span class="text-body-content text-error-700 leading-relaxed">{error}</span>
		</div>
	{/if}

	<!-- Content -->
	<div class="flex flex-col gap-4">
		{@render children?.()}
	</div>
</div>
