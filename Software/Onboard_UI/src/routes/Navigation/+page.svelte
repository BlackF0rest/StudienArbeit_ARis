<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { buildNavigationProvider, type NavigationSnapshot } from '$lib/services/navigation';
	import { featureHost } from '$lib/feature-host';
	import { shortPressPulse, getHintForContext, openNavigationViaInput, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import HudTabs from '$lib/components/hud/HudTabs.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	const USE_REAL_PROVIDER = false;
	const provider = buildNavigationProvider(USE_REAL_PROVIDER);
	const panels = ['route', 'next-action', 'heading'];

	let activePanelIndex = 0;
	let pulseToken = 0;
	let hint: InputHint = getHintForContext('navigation');
	let nav: NavigationSnapshot = {
		routeText: 'Lade Routendaten…',
		headingDeg: 0,
		nextAction: 'Warte auf Daten',
		source: 'mock',
		updatedAt: new Date(0).toISOString()
	};

	function cycleInfoPanel(): void {
		activePanelIndex = (activePanelIndex + 1) % panels.length;
		featureHost.emit('navigation-mvp', 'navigation.panel_cycle', { panel: panels[activePanelIndex] });
	}

	async function refreshNavigation(): Promise<void> {
		try {
			nav = await provider.getLatest();
			featureHost.emit('navigation-mvp', 'navigation.update', { headingDeg: nav.headingDeg, source: provider.name });
		} catch {
			nav = {
				...nav,
				nextAction: 'Provider nicht erreichbar – Mock/letzter Stand aktiv',
				updatedAt: new Date().toISOString()
			};
		}
	}

	onMount(() => {
		const clearActions = setInputContext('navigation', {
			onSingle: cycleInfoPanel,
			onDouble: () => {
				openNavigationViaInput();
				featureHost.emit('navigation-mvp', 'navigation.return_home', { reason: 'double-tap' });
			}
		});
		const unsubscribePulse = shortPressPulse.subscribe((value) => {
			pulseToken = value;
		});

		void refreshNavigation();
		const timer = setInterval(() => void refreshNavigation(), 3000);
		return () => {
			clearActions();
			unsubscribePulse();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Navigation MVP" subtitle={`Source: ${provider.name}`}>
	<svelte:fragment slot="header">
		<StatusPill text={nav.source === 'real' ? 'Live Source' : 'Mock Source'} tone={nav.source === 'real' ? 'ok' : 'info'} />
	</svelte:fragment>

	<HudTabs tabs={panels} activeIndex={activePanelIndex} {pulseToken} />

	<HudCard>
		{#if panels[activePanelIndex] === 'route'}
			<p class="nav-panel-heading">Route</p>
			<p class="nav-panel-main">{nav.routeText}</p>
		{:else if panels[activePanelIndex] === 'next-action'}
			<p class="nav-panel-heading">Next action</p>
			<p class="nav-panel-main">{nav.nextAction}</p>
		{:else}
			<p class="nav-panel-heading">Heading marker</p>
			<div class="compass-wrap nav-marker-large">
				<div class="nav-marker-n">N</div>
				<div class="nav-marker-arrow" style={`--heading-deg:${nav.headingDeg}deg;`}>↑</div>
			</div>
			<p class="nav-panel-main">{Math.round(nav.headingDeg)}°</p>
		{/if}
		<p class="hud-muted"><strong>Updated:</strong> {nav.updatedAt}</p>
	</HudCard>

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
