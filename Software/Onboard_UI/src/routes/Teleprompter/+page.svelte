<script lang="ts">
	import Teleprompter from './teleprompter.svelte';
	import Header from '../header.svelte';
	import { isDebugUiEnabled } from '$lib/runtime-flags';
	import { getHintForContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	$: debugMode = isDebugUiEnabled();
	const hint: InputHint = getHintForContext('teleprompter');
</script>

{#if debugMode}
	<Header />
	<HudScaffold title="Teleprompter Runtime" subtitle="Live scroll mode · double press to open navigation">
		<svelte:fragment slot="header">
			<StatusPill text="Debug Overlay Enabled" tone="info" />
		</svelte:fragment>
		<HudCard title="Runtime mode" muted={true}>
			<p class="hud-primary-point">LIVE</p>
			<p class="hud-secondary-line">Teleprompter overlay running</p>
			<p class="hud-compact-line">Fullscreen teleprompter is active in the overlay below.</p>
		</HudCard>
		<svelte:fragment slot="hint">
			<InputHintOverlay {hint} />
		</svelte:fragment>
	</HudScaffold>
{/if}

<Teleprompter {debugMode} />

{#if !debugMode}
	<InputHintOverlay {hint} compact={true} />
{/if}
