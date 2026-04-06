<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { buildNavigationProvider, type NavigationSnapshot } from '$lib/services/navigation';
	import { featureHost } from '$lib/feature-host';
	import { getHintForContext, registerAppActions, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import HudTabs from '$lib/components/hud/HudTabs.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	const USE_REAL_PROVIDER = false;
	const provider = buildNavigationProvider(USE_REAL_PROVIDER);
	const panels = ['route', 'next-action', 'heading'];

	let activePanelIndex = 0;
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

	async function returnHome(): Promise<void> {
		featureHost.emit('navigation-mvp', 'navigation.return_home', { reason: 'long-press' });
		await goto('/');
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
		setInputContext('navigation');
		const unregister = registerAppActions({
			onShort: cycleInfoPanel,
			onLong: () => {
				void returnHome();
			}
		});

		void refreshNavigation();
		const timer = setInterval(() => void refreshNavigation(), 3000);
		return () => {
			unregister();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Navigation MVP" subtitle={`Source: ${provider.name}`}>
	<svelte:fragment slot="header">
		<StatusPill text={nav.source === 'real' ? 'Live Source' : 'Mock Source'} tone={nav.source === 'real' ? 'ok' : 'info'} />
	</svelte:fragment>

	<HudTabs tabs={panels} activeIndex={activePanelIndex} />

	<HudCard>
		{#if panels[activePanelIndex] === 'route'}
			<p><strong>Route:</strong> {nav.routeText}</p>
		{:else if panels[activePanelIndex] === 'next-action'}
			<p><strong>Next Action:</strong> {nav.nextAction}</p>
		{:else}
			<p>Heading: {Math.round(nav.headingDeg)}°</p>
		{/if}
		<p class="hud-muted"><strong>Updated:</strong> {nav.updatedAt}</p>
	</HudCard>

	<HudCard>
		<div class="compass-wrap">
			<div style="position:absolute;top:10px;color:#7eff7e;font-weight:bold;">N</div>
			<div style="position:absolute;top:50%;left:50%;transform-origin:50% 90%;font-size:2rem;color:#9dff9d;transform:translate(-50%,-90%) rotate({nav.headingDeg}deg);">↑</div>
		</div>
	</HudCard>

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
