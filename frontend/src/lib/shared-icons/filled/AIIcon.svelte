<script lang="ts">
	import type { BaseIconProps } from '../types';

	let {
		size = 20,
		color = 'currentColor',
		class: className = '',
		ariaLabel,
		ariaHidden = false,
		...restProps
	}: BaseIconProps = $props();
</script>

<div
	class="icon-ai {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'AI'}
	aria-hidden={ariaHidden}
	role="img"
	{...restProps}
>
	<svg
		width={size}
		height={size}
		viewBox="0 0 20 20"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
	>
		<!-- 主体星形 -->
		<path
			d="M8.48861 1.63623L9.03419 3.75123C9.62922 6.05794 11.4305 7.85922 13.7372 8.45426L15.8522 8.99984L13.7372 9.54542C11.4305 10.1405 9.62922 11.9417 9.03419 14.2484L8.48861 16.3634L7.94302 14.2484C7.34799 11.9417 5.5467 10.1405 3.24 9.54542L1.125 8.99984L3.24 8.45426C5.5467 7.85922 7.34799 6.05793 7.94303 3.75123L8.48861 1.63623Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>

		<!-- 小星形装饰 -->
		<path
			d="M15.8523 3L16.0412 3.7323C16.3387 4.88565 17.2394 5.78629 18.3927 6.08381L19.125 6.27271L18.3927 6.46162C17.2394 6.75913 16.3387 7.65978 16.0412 8.81313L15.8523 9.54543L15.6634 8.81313C15.3659 7.65978 14.4652 6.75913 13.3119 6.46162L12.5796 6.27271L13.3119 6.08381C14.4652 5.78629 15.3659 4.88565 15.6634 3.7323L15.8523 3Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-ai {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>
