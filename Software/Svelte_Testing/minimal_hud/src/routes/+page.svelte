<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import Header from './header.svelte';
	import { bootstrapFeatureHost } from '$lib/feature-registration';
	import { featureHost, type FeatureRuntimeSnapshot } from '$lib/feature-host';
	import { fetchPcLinkDiagnostics, type PcLinkDiagnostics } from '$lib/services/pc-link-diagnostics';
	import { homeCarouselIndex, getHintForContext, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	const carouselApps = ['Navigation', 'Teleprompter', 'Messages/HUD'];
	let selectedApp = carouselApps[0];
	let hint: InputHint = getHintForContext('home');

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

	onMount(() => {
		setInputContext('home');
		selectedApp = carouselApps[get(homeCarouselIndex)] ?? carouselApps[0];
		const unsubscribe = homeCarouselIndex.subscribe((index) => {
			selectedApp = carouselApps[index] ?? carouselApps[0];
		});
		bootstrapFeatureHost();
		void refreshSnapshot();
		const timer = setInterval(() => void refreshSnapshot(), 3000);
		return () => {
			unsubscribe();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Feature Host Runtime" subtitle={`Home carousel selection: ${selectedApp}`}>
	<svelte:fragment slot="header">
		<StatusPill text={pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'} tone={pcDiagnostics.pc_link.active ? 'ok' : 'warn'} />
	</svelte:fragment>

	<div class="hud-grid-2">
		{#each snapshot.registered as module}
			<HudCard title={module.name}>
				<p>{module.description}</p>
				<p><strong>Version:</strong> {module.version}</p>
				<p><strong>Permissions:</strong> {module.permissions.join(', ')}</p>
				<p><strong>Dependencies:</strong> {module.dependencies.join(', ')}</p>
				<p><strong>Health:</strong> {snapshot.health[module.id]?.ok ? '✅' : '❌'} {snapshot.health[module.id]?.details}</p>
			</HudCard>
		{/each}
	</div>

	<HudCard title="Telemetry (latest)" muted>
		{#if snapshot.telemetry.length === 0}
			<p>No telemetry yet.</p>
		{:else}
			{#each snapshot.telemetry.slice(0, 8) as event}
				<p>{event.createdAt} · {event.featureId} · {event.type}</p>
			{/each}
		{/if}
	</HudCard>

	<HudCard title="PC Link Diagnostics">
		<p><strong>PC Link:</strong> {pcDiagnostics.pc_link.active ? 'Connected' : 'Offline'}</p>
		<p><strong>Stream:</strong> {pcDiagnostics.stream_metrics.connected ? 'Connected' : 'Disconnected'} ({pcDiagnostics.stream_metrics.quality})</p>
		<p><strong>Reconnects:</strong> {pcDiagnostics.stream_metrics.reconnect_attempts} · <strong>Bandwidth:</strong> {pcDiagnostics.stream_metrics.avg_bandwidth_mbps ?? 'n/a'} Mbps · <strong>Frame Drop:</strong> {pcDiagnostics.stream_metrics.avg_frame_drop_ratio ?? 'n/a'}</p>
		<p><strong>Display Mode:</strong> {pcDiagnostics.stream_metrics.onboard_only_mode ? 'Onboard-only fallback' : 'Hybrid streaming'}</p>
		<p><strong>Overlay Contract:</strong> v{pcDiagnostics.overlay_contract.contract_version} · {pcDiagnostics.overlay_contract.coordinate_space} · {pcDiagnostics.overlay_contract.z_order.join(' → ')}</p>
	</HudCard>

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
