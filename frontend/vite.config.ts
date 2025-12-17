import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		port: 5176
	},
	resolve: {
		// Preserve symlinks to ensure dependencies are resolved from payroll-frontend/node_modules
		preserveSymlinks: true
	}
});
