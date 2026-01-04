<script lang="ts">
	interface AIIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 18, color: _color = 'currentColor', class: className = '' }: AIIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 20 20"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<g filter="url(#filter0_f_14_1903)">
		<circle cx="8.43748" cy="10.9941" r="3.93748" fill="#D9D8FF" />
	</g>
	<path
		d="M8.48861 1.63623L9.03419 3.75123C9.62922 6.05794 11.4305 7.85922 13.7372 8.45426L15.8522 8.99984L13.7372 9.54542C11.4305 10.1405 9.62922 11.9417 9.03419 14.2484L8.48861 16.3634L7.94302 14.2484C7.34799 11.9417 5.5467 10.1405 3.24 9.54542L1.125 8.99984L3.24 8.45426C5.5467 7.85922 7.34799 6.05793 7.94303 3.75123L8.48861 1.63623Z"
		fill="url(#paint0_linear_14_1903)"
	/>
	<path
		d="M15.8523 0L16.0412 0.732299C16.3387 1.88565 17.2394 2.78629 18.3927 3.08381L19.125 3.27271L18.3927 3.46162C17.2394 3.75913 16.3387 4.65978 16.0412 5.81313L15.8523 6.54543L15.6634 5.81313C15.3659 4.65978 14.4652 3.75913 13.3119 3.46162L12.5796 3.27271L13.3119 3.08381C14.4652 2.78629 15.3659 1.88565 15.6634 0.732298L15.8523 0Z"
		fill="#612AE1"
	/>
	<defs>
		<filter
			id="filter0_f_14_1903"
			x="1.85966e-05"
			y="2.55666"
			width="16.875"
			height="16.875"
			filterUnits="userSpaceOnUse"
			color-interpolation-filters="sRGB"
		>
			<feFlood flood-opacity="0" result="BackgroundImageFix" />
			<feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
			<feGaussianBlur stdDeviation="2.24999" result="effect1_foregroundBlur_14_1903" />
		</filter>
		<linearGradient
			id="paint0_linear_14_1903"
			x1="5.62498"
			y1="0.869182"
			x2="10.6875"
			y2="16.0566"
			gradientUnits="userSpaceOnUse"
		>
			<stop stop-color="#615DE0" />
			<stop offset="1" stop-color="#35337A" />
		</linearGradient>
	</defs>
</svg>
