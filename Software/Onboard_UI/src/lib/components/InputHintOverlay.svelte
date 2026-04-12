<script lang="ts">
	import type { InputHint } from '$lib/input-controller';

	let { hint, compact = false }: { hint: InputHint; compact?: boolean } = $props();
</script>

<div class="input-hint" class:compact>{hint.short} · {hint.long}</div>

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

	.input-hint.compact {
		font-size: 0.7rem;
		padding: 0.15rem 0.4rem;
		bottom: 6px;
		opacity: 0.82;
	}
</style>
