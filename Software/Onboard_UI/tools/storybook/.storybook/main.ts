import type { StorybookConfig } from '@storybook/sveltekit';

const config: StorybookConfig = {
	stories: ['../stories/**/*.mdx', '../stories/**/*.stories.@(js|jsx|mjs|ts|tsx|svelte)'],
	addons: ['@storybook/addon-a11y', '@storybook/addon-docs', '@storybook/addon-vitest'],
	framework: {
		name: '@storybook/sveltekit',
		options: {}
	}
};

export default config;
