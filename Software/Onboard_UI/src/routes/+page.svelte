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
	import { isDebugUiEnabled } from '$lib/runtime-flags';

	const COMPACT_MODE_POLL_INTERVAL_MS = 6000;

	const carouselApps = ['Navigation', 'Teleprompter', 'Messages/HUD'];
	const routeByApp: Record<string, string> = {
		Navigation: '/Navigation',
		Teleprompter: '/Teleprompter',
		'Messages/HUD': '/Messages'
	};

	let selectedApp = carouselApps[0];
	let hint: InputHint = getHintForContext('home');

	let debugUiEnabled = false;

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

	$: selectedModule =
		snapshot.registered.find((module) => {
			if (selectedApp === 'Messages/HUD') return module.id === 'ai-chat-scaffold';
			if (selectedApp === 'Navigation') return module.id === 'navigation-mvp';
			if (selectedApp === 'Teleprompter') return module.id === 'teleprompter-runtime';
			return false;
		}) ?? null;

	$: selectedHealth = selectedModule ? snapshot.health[selectedModule.id] : undefined;

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
		debugUiEnabled = isDebugUiEnabled();
		bootstrapFeatureHost();
		void refreshSnapshot();
		const timer = setInterval(() => void refreshSnapshot(), COMPACT_MODE_POLL_INTERVAL_MS);
		return () => {
			unsubscribe();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Host Home" subtitle="600x400 profile: 3 compact blocks, 2 lines per block">
	<svelte:fragment slot="header">
		<StatusPill text={pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'} tone={pcDiagnostics.pc_link.active ? 'ok' : 'warn'} />
	</svelte:fragment>

	<div class="hud-grid-3">
		<HudCard title="Selected app" className="hud-compact-block">
			<p class="hud-primary-point">{selectedApp}</p>
			<p class="hud-secondary-line">Long press to open · Route: {routeByApp[selectedApp]}</p>
			<p class="hud-compact-line">Health: {selectedHealth?.ok ? 'Healthy' : 'Pending'}</p>
		</HudCard>

		<HudCard title="Connection summary" className="hud-compact-block">
			<p class="hud-compact-line">PC Link: {pcDiagnostics.pc_link.active ? 'Connected' : 'Offline'} · Sessions: {pcDiagnostics.pc_link.sessions.length}</p>
			<p class="hud-compact-line">Stream: {pcDiagnostics.stream_metrics.connected ? 'Connected' : 'Disconnected'} · Quality: {pcDiagnostics.stream_metrics.quality}</p>
		</HudCard>

		<HudCard title="Current hint" className="hud-compact-block">
			<p class="hud-compact-line">short: {hint.short}</p>
			<p class="hud-compact-line">long: {hint.long}</p>
		</HudCard>
	</div>

	{#if debugUiEnabled}
		<p class="hud-muted hud-home-debug-link">Detailed telemetry/diagnostics moved to <a href="/Debug">Debug</a>.</p>
	{/if}

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
