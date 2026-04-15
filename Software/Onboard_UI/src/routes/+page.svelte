<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import Header from './header.svelte';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import {
		homeCarouselIndex,
		shortPressPulse,
		getHintForContext,
		setInputContext,
		type InputHint
	} from '$lib/input-controller';

	const apps = [
		{ name: 'Navigation', route: '/Navigation', info: 'Pfeile, Kompass und Richtung' },
		{ name: 'Teleprompter', route: '/Teleprompter', info: 'Text groß und klar anzeigen' },
		{ name: 'Messages', route: '/Messages', info: 'Kurze Mitteilungen lesen' }
	] as const;

	let selectedIndex = 0;
	let pulseCard = false;
	let pulseTimeout: ReturnType<typeof setTimeout> | undefined;
	let hint: InputHint = getHintForContext('home');

	$: selectedApp = apps[selectedIndex] ?? apps[0];

	onMount(() => {
		setInputContext('home');
		selectedIndex = get(homeCarouselIndex);

		const unsubscribeIndex = homeCarouselIndex.subscribe((index) => {
			selectedIndex = index;
		});

		const unsubscribePulse = shortPressPulse.subscribe(() => {
			pulseCard = true;
			if (pulseTimeout) clearTimeout(pulseTimeout);
			pulseTimeout = setTimeout(() => {
				pulseCard = false;
			}, 180);
		});

		return () => {
			unsubscribeIndex();
			unsubscribePulse();
			if (pulseTimeout) clearTimeout(pulseTimeout);
		};
	});
</script>

<Header />

<main class="main-compact">
	<section class="focus-card {pulseCard ? 'pulse' : ''}">
		<p class="label">Aktive Ansicht</p>
		<h1>{selectedApp.name}</h1>
		<p class="description">{selectedApp.info}</p>
		<a class="open-link" href={selectedApp.route}>Öffnen</a>
	</section>

	<section class="quick-grid">
		{#each apps as app, index}
			<a class="quick-item" class:is-active={index === selectedIndex} href={app.route}>
				<span class="quick-title">{app.name}</span>
				<span class="quick-route">{app.route}</span>
			</a>
		{/each}
	</section>

	<footer class="hint-wrap">
		<InputHintOverlay {hint} />
	</footer>
</main>

<style>
	.main-compact {
		min-height: calc(100dvh - 3rem);
		padding: 0.75rem;
		display: grid;
		gap: 0.75rem;
		align-content: start;
	}

	.focus-card {
		border: 1px solid var(--hud-border-accent);
		border-radius: 0.75rem;
		padding: 0.8rem;
		background: linear-gradient(160deg, #0f1f0f 0%, #090909 100%);
	}

	.focus-card.pulse {
		box-shadow: 0 0 0 2px rgb(158 255 158 / 25%);
	}

	.label {
		margin: 0;
		font-size: 0.82rem;
		color: var(--hud-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	h1 {
		margin: 0.2rem 0;
		font-size: clamp(1.55rem, 9vw, 2.4rem);
		line-height: 1.05;
	}

	.description {
		margin: 0;
		font-size: 1rem;
		color: #d5f2d5;
	}

	.open-link {
		display: inline-flex;
		margin-top: 0.75rem;
		padding: 0.45rem 0.9rem;
		border-radius: 0.55rem;
		border: 1px solid var(--hud-border-accent);
		background: #143614;
		font-size: 1rem;
		font-weight: 700;
		text-decoration: none;
		color: var(--hud-text);
	}

	.quick-grid {
		display: grid;
		gap: 0.55rem;
	}

	.quick-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		padding: 0.62rem 0.68rem;
		border-radius: 0.65rem;
		border: 1px solid var(--hud-border);
		text-decoration: none;
		background: var(--hud-surface);
		color: var(--hud-text);
	}

	.quick-item.is-active {
		border-color: var(--hud-border-accent);
		background: #0f1b0f;
	}

	.quick-title {
		font-size: 1.05rem;
		font-weight: 650;
	}

	.quick-route {
		font-size: 0.9rem;
		color: var(--hud-muted);
		font-family: var(--hud-font-mono);
	}

	.hint-wrap {
		min-height: 1.8rem;
		display: grid;
		align-items: end;
	}
</style>
