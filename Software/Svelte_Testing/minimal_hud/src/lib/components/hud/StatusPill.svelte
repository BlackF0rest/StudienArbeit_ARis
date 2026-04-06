<script lang="ts">
	type Tone = 'neutral' | 'ok' | 'warn' | 'danger' | 'info';
	let { text, tone = 'neutral' }: { text: string; tone?: Tone } = $props();
</script>

<span class={`status-pill tone-${tone}`}>{text}</span>
