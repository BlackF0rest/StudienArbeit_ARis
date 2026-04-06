<script lang="ts">
	import type { InputHint } from '$lib/input-controller';

	let { hint }: { hint: InputHint } = $props();
</script>

<div class="input-hint">short: {hint.short} | long: {hint.long}</div>

<style>
	.input-hint {
		position: fixed;
		left: 50%;
		bottom: 10px;
		transform: translateX(-50%);
		background: rgba(0, 0, 0, 0.72);
		border: 1px solid #2f5a2f;
		color: #b8ffb8;
		padding: 0.25rem 0.6rem;
		font-size: 0.85rem;
		font-family: var(--hud-font-stack);
		z-index: 60;
		white-space: nowrap;
	}
</style>
