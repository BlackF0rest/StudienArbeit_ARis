<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" type="image/svg+xml" href="{favicon}" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<title>Minimal HUD</title>
</svelte:head>

{@render children?.()}
