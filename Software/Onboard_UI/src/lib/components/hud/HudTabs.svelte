<script lang="ts">
	import { onDestroy } from 'svelte';

	let {
		tabs,
		activeIndex = 0,
		pulseToken = 0
	}: { tabs: string[]; activeIndex?: number; pulseToken?: number } = $props();

	let shouldPulse = false;
	let lastPulseToken = pulseToken;
	let pulseTimeout: ReturnType<typeof setTimeout> | undefined;

	$: if (pulseToken !== lastPulseToken) {
		lastPulseToken = pulseToken;
		shouldPulse = true;
		if (pulseTimeout) clearTimeout(pulseTimeout);
		pulseTimeout = setTimeout(() => {
			shouldPulse = false;
		}, 160);
	}

	onDestroy(() => {
		if (pulseTimeout) clearTimeout(pulseTimeout);
	});
</script>

<div class="hud-tabs" role="tablist" aria-label="HUD tabs">
	{#each tabs as tab, index}
		<span
			role="tab"
			aria-selected={index === activeIndex}
			class:active={index === activeIndex}
			class:short-pulse={index === activeIndex && shouldPulse}
		>
			{tab}
		</span>
	{/each}
</div>
