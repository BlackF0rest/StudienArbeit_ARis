<script lang="ts">
	import type { InputHint } from '$lib/input-controller';

	let { hint, compact = false }: { hint: InputHint; compact?: boolean } = $props();
</script>

<div class="input-hint" class:compact>{hint.short} · {hint.long}</div>

<style>
	.input-hint {
		position: fixed;
		left: 50%;
		bottom: var(--hud-space-sm);
		transform: translateX(-50%);
		background: rgba(0, 0, 0, 0.72);
		border: 1px solid #2f5a2f;
		color: #b8ffb8;
		padding: var(--hud-space-xs) calc(var(--hud-space-sm) + 0.1rem);
		font-size: var(--hud-font-sm);
		font-family: var(--hud-font-stack);
		z-index: 60;
		white-space: nowrap;
	}

	.input-hint.compact {
		font-size: var(--hud-font-xs);
		padding: 0.15rem var(--hud-space-sm);
		bottom: var(--hud-space-xs);
		opacity: 0.82;
	}
</style>
