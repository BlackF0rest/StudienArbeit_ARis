<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { buildNavigationProvider, type NavigationSnapshot } from '$lib/services/navigation';
	import { featureHost } from '$lib/feature-host';

	const USE_REAL_PROVIDER = false;
	const provider = buildNavigationProvider(USE_REAL_PROVIDER);

	let nav: NavigationSnapshot = {
		routeText: 'Lade Routendaten…',
		headingDeg: 0,
		nextAction: 'Warte auf Daten',
		source: 'mock',
		updatedAt: new Date(0).toISOString()
	};

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
		void refreshNavigation();
		const timer = setInterval(() => void refreshNavigation(), 3000);
		return () => clearInterval(timer);
	});
</script>

<Header />

<main>
	<h2>Navigation MVP</h2>
	<p><strong>Source:</strong> {provider.name}</p>
	<div class="block">
		<p><strong>Route:</strong> {nav.routeText}</p>
		<p><strong>Next Action:</strong> {nav.nextAction}</p>
		<p><strong>Updated:</strong> {nav.updatedAt}</p>
	</div>

	<div class="heading-wrap">
		<div class="compass">N</div>
		<div class="needle" style="transform: translate(-50%, -90%) rotate({nav.headingDeg}deg);">↑</div>
	</div>
	<p>Heading: {Math.round(nav.headingDeg)}°</p>
</main>

<style>
	main { padding: 0.6rem 1rem; }
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
