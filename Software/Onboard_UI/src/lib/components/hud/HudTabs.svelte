<script lang="ts">
	let {
		tabs,
		activeIndex = 0
	}: { tabs: string[]; activeIndex?: number } = $props();
</script>

<div class="hud-tabs" role="tablist" aria-label="HUD tabs">
	{#each tabs as tab, index}
		<span role="tab" aria-selected={index === activeIndex} class:active={index === activeIndex}>{tab}</span>
	{/each}
</div>
