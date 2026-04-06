<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import { detachInputControl, subscribeInputControl } from '$lib/input-controller';
	import { hudTokens } from '$lib/ui/tokens';

	let { children } = $props();

	onMount(() => {
		subscribeInputControl();

		const body = document.body;
		body.classList.add('ar-mode', hudTokens.density.compactClass);
		body.style.setProperty('--hud-font-stack', hudTokens.font.stack);
		body.style.setProperty('--hud-font-mono', hudTokens.font.mono);

		return () => {
			detachInputControl();
			body.classList.remove('ar-mode', hudTokens.density.compactClass);
		};
	});
</script>

<svelte:head>
	<link rel="icon" type="image/svg+xml" href="{favicon}" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<title>Minimal HUD</title>
</svelte:head>

{@render children?.()}
