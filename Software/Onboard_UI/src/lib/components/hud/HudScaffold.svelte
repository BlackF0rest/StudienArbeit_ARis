<script lang="ts">
	let {
		title,
		subtitle
	}: { title: string; subtitle?: string } = $props();
</script>

<section class="hud-scaffold">
	<header class="hud-scaffold-header">
		<div>
			<h2>{title}</h2>
			{#if subtitle}<p class="hud-subtitle">{subtitle}</p>{/if}
		</div>
		<slot name="header" />
	</header>

	<div class="hud-scaffold-content">
		<slot />
	</div>

	<footer class="hud-scaffold-hint">
		<slot name="hint" />
	</footer>
</section>
