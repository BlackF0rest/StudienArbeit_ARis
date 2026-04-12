<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import { detachInputControl, subscribeInputControl } from '$lib/input-controller';
	import { isArCompactEnabled } from '$lib/runtime-flags';
	import { hudTokens } from '$lib/ui/tokens';

	let { children } = $props();

	onMount(() => {
		subscribeInputControl();

		const body = document.body;
		const applyViewportBreakpointClasses = () => {
			body.classList.toggle('hud-breakpoint-width-640', window.innerWidth <= 640);
			body.classList.toggle('hud-breakpoint-height-420', window.innerHeight <= 420);
		};

		body.classList.add('ar-mode', hudTokens.density.compactClass);
		body.classList.toggle('ar-compact', isArCompactEnabled());
		body.style.setProperty('--hud-font-stack', hudTokens.font.stack);
		body.style.setProperty('--hud-font-mono', hudTokens.font.mono);
		applyViewportBreakpointClasses();
		window.addEventListener('resize', applyViewportBreakpointClasses);

		return () => {
			detachInputControl();
			window.removeEventListener('resize', applyViewportBreakpointClasses);
			body.classList.remove('hud-breakpoint-width-640', 'hud-breakpoint-height-420');
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
