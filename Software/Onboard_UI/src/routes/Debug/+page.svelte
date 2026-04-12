<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { bootstrapFeatureHost } from '$lib/feature-registration';
	import { featureHost, type FeatureRuntimeSnapshot } from '$lib/feature-host';
	import { fetchPcLinkDiagnostics, type PcLinkDiagnostics } from '$lib/services/pc-link-diagnostics';
	import { getHintForContext, registerAppActions, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	let hint: InputHint = getHintForContext('debug');
	let snapshot: FeatureRuntimeSnapshot = {
		registered: [],
		health: {},
		telemetry: []
	};

	let pcDiagnostics: PcLinkDiagnostics = {
		pc_link: { active: false, sessions: [] },
		stream_metrics: {
			connected: false,
			reconnect_attempts: 0,
			quality: 'medium',
			avg_bandwidth_mbps: null,
			avg_frame_drop_ratio: null,
			onboard_only_mode: false,
			last_updated: new Date(0).toISOString()
		},
		overlay_contract: {
			contract_version: '1.0',
			coordinate_space: 'normalized',
			safe_area: { x: 0, y: 0, width: 1, height: 1 },
			z_order: ['streamed-scene', 'streamed-overlay', 'onboard-hud'],
			last_synced_at: new Date(0).toISOString()
		}
	};

	async function refreshSnapshot(): Promise<void> {
		snapshot = await featureHost.snapshot();
		pcDiagnostics = await fetchPcLinkDiagnostics();
	}

	async function returnHome(): Promise<void> {
		await goto('/');
	}

	onMount(() => {
		bootstrapFeatureHost();
		setInputContext('debug');
		const unregister = registerAppActions({
			onShort: () => {
				void refreshSnapshot();
			},
			onLong: () => {
				void returnHome();
			}
		});
		void refreshSnapshot();
		const timer = setInterval(() => void refreshSnapshot(), 3000);
		return () => {
			unregister();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Debug Diagnostics" subtitle="Telemetry and integration diagnostics">
	<svelte:fragment slot="header">
		<StatusPill text={pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'} tone={pcDiagnostics.pc_link.active ? 'ok' : 'warn'} />
	</svelte:fragment>

	<HudCard title="Telemetry (latest)">
		{#if snapshot.telemetry.length === 0}
			<p>No telemetry yet.</p>
		{:else}
			{#each snapshot.telemetry.slice(0, 12) as event}
				<p>{event.createdAt} · {event.featureId} · {event.type}</p>
			{/each}
		{/if}
	</HudCard>

	<HudCard title="PC Link Diagnostics">
		<p class="hud-primary-point">{pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'}</p>
		<p class="hud-secondary-line">Stream {pcDiagnostics.stream_metrics.connected ? 'connected' : 'disconnected'} ({pcDiagnostics.stream_metrics.quality})</p>
		<p><strong>Reconnects:</strong> {pcDiagnostics.stream_metrics.reconnect_attempts} · <strong>Bandwidth:</strong> {pcDiagnostics.stream_metrics.avg_bandwidth_mbps ?? 'n/a'} Mbps · <strong>Frame Drop:</strong> {pcDiagnostics.stream_metrics.avg_frame_drop_ratio ?? 'n/a'}</p>
		<p><strong>Display Mode:</strong> {pcDiagnostics.stream_metrics.onboard_only_mode ? 'Onboard-only fallback' : 'Hybrid streaming'}</p>
		<p><strong>Overlay Contract:</strong> v{pcDiagnostics.overlay_contract.contract_version} · {pcDiagnostics.overlay_contract.coordinate_space} · {pcDiagnostics.overlay_contract.z_order.join(' → ')}</p>
	</HudCard>

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
