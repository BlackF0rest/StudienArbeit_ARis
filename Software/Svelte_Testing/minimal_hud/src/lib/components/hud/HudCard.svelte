<script lang="ts">
	let {
		title,
		className = '',
		muted = false
	}: { title?: string; className?: string; muted?: boolean } = $props();
</script>

<section class={`hud-card ${muted ? 'is-muted' : ''} ${className}`.trim()}>
	{#if title}<h3>{title}</h3>{/if}
	<slot />
</section>
