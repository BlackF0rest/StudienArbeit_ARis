<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { buildNavigationProvider, type NavigationSnapshot } from '$lib/services/navigation';
	import { featureHost } from '$lib/feature-host';
	import {
		getHintForContext,
		registerAppActions,
		setInputContext,
		type InputHint
	} from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';

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
			featureHost.emit('navigation-mvp', 'navigation.update', {
				headingDeg: nav.headingDeg,
				source: provider.name
			});
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

<main>
	<h2>Navigation MVP</h2>
	<p><strong>Source:</strong> {provider.name}</p>
	<div class="panel-tabs">
		{#each panels as panel, index}
			<span class:active={index === activePanelIndex}>{panel}</span>
		{/each}
	</div>
	<div class="block">
		{#if panels[activePanelIndex] === 'route'}
			<p><strong>Route:</strong> {nav.routeText}</p>
		{:else if panels[activePanelIndex] === 'next-action'}
			<p><strong>Next Action:</strong> {nav.nextAction}</p>
		{:else}
			<p>Heading: {Math.round(nav.headingDeg)}°</p>
		{/if}
		<p><strong>Updated:</strong> {nav.updatedAt}</p>
	</div>

	<div class="heading-wrap">
		<div class="compass">N</div>
		<div class="needle" style="transform: translate(-50%, -90%) rotate({nav.headingDeg}deg);">↑</div>
	</div>
</main>

<InputHintOverlay {hint} />

<style>
	main { padding: 0.6rem 1rem; }
	.panel-tabs {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}
	.panel-tabs span {
		padding: 0.2rem 0.45rem;
		border: 1px solid #335033;
		opacity: 0.7;
	}
	.panel-tabs span.active {
		opacity: 1;
		color: #9eff9e;
	}
	.block { border: 1px solid #333; padding: 0.6rem; background: #080808; }
	.heading-wrap {
		margin-top: 1rem;
		position: relative;
		width: 160px;
		height: 160px;
		border: 2px solid #3a3a3a;
		border-radius: 50%;
		display: grid;
		place-items: center;
	}
	.compass { position: absolute; top: 10px; color: #7eff7e; font-weight: bold; }
	.needle {
		position: absolute;
		top: 50%;
		left: 50%;
		transform-origin: 50% 90%;
		font-size: 2rem;
		color: #9dff9d;
	}
</style>
