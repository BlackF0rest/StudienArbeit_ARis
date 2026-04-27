<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import { getHintForContext, setInputContext, type InputHint } from '$lib/input-controller';
	import { fetchSensorDiagnostics, type SensorDiagnostics } from '$lib/services/sensor-diagnostics';

	type SensorTile = {
		id: string;
		label: string;
		value: string;
		unit?: string;
	};

	let hint: InputHint = getHintForContext('demo');
	let showRondell = false;
	let activeIndex = 0;
	let diagnostics: SensorDiagnostics = {
		connection: 'offline',
		button: { pin: 40, state: 'unknown', lastEventAt: null },
		mpu6050: {
			sdaPin: 3,
			sclPin: 5,
			gyro: { x: null, y: null, z: null },
			accel: { x: null, y: null, z: null }
		},
		gy63: {
			sdaPin: 3,
			sclPin: 5,
			pressureHpa: null,
			altitudeM: null
		},
		lastUpdated: new Date(0).toISOString()
	};

	function formatNumber(value: number | null, digits = 2): string {
		return value === null ? 'n/a' : value.toFixed(digits);
	}

	$: sensorTiles = [
		{ id: 'button', label: 'Button', value: diagnostics.button.state },
		{ id: 'gyro-x', label: 'Gyro X', value: formatNumber(diagnostics.mpu6050.gyro.x), unit: 'dps' },
		{ id: 'gyro-y', label: 'Gyro Y', value: formatNumber(diagnostics.mpu6050.gyro.y), unit: 'dps' },
		{ id: 'gyro-z', label: 'Gyro Z', value: formatNumber(diagnostics.mpu6050.gyro.z), unit: 'dps' },
		{ id: 'accel-x', label: 'Accel X', value: formatNumber(diagnostics.mpu6050.accel.x), unit: 'g' },
		{ id: 'accel-y', label: 'Accel Y', value: formatNumber(diagnostics.mpu6050.accel.y), unit: 'g' },
		{ id: 'accel-z', label: 'Accel Z', value: formatNumber(diagnostics.mpu6050.accel.z), unit: 'g' },
		{ id: 'pressure', label: 'Druck', value: formatNumber(diagnostics.gy63.pressureHpa), unit: 'hPa' },
		{ id: 'altitude', label: 'Höhe', value: formatNumber(diagnostics.gy63.altitudeM), unit: 'm' }
	] satisfies SensorTile[];

	function handleSinglePress(): void {
		showRondell = true;
		activeIndex = (activeIndex + 1) % sensorTiles.length;
	}

	async function refreshSensors(): Promise<void> {
		diagnostics = await fetchSensorDiagnostics();
	}

	onMount(() => {
		const clearActions = setInputContext('demo', {
			onSingle: () => {
				handleSinglePress();
				void refreshSensors();
			}
		});

		const interval = setInterval(() => {
			if (showRondell) void refreshSensors();
		}, 2500);

		return () => {
			clearActions();
			clearInterval(interval);
		};
	});
</script>

<Header />

<main class="demo-main">
	<section class="hero">
		<p class="hero-subline">AR-Demo Startseite</p>
		<h1>AR-System</h1>
		<button class="single-button" on:click={() => { handleSinglePress(); void refreshSensors(); }}>
			Single Press: Sensordaten im Rondell
		</button>
	</section>

	{#if showRondell}
		<section class="rondell-wrap" aria-label="Sensordaten Rondell">
			<div class="rondell">
				{#each sensorTiles as tile, index}
					<article class="sensor-tile {index === activeIndex ? 'is-active' : ''}" style={`--index:${index}; --total:${sensorTiles.length};`}>
						<p class="tile-label">{tile.label}</p>
						<p class="tile-value">{tile.value} {tile.unit ?? ''}</p>
					</article>
				{/each}
			</div>
			<p class="connection-state">
				Status: {diagnostics.connection === 'connected' ? 'Sensoren online' : 'Fallback / offline'} · Update: {diagnostics.lastUpdated}
			</p>
		</section>
	{/if}

	<footer class="hint-wrap">
		<InputHintOverlay {hint} />
	</footer>
</main>

<style>
	.demo-main {
		min-height: calc(100dvh - 3rem);
		padding: 0.9rem;
		display: grid;
		gap: 1rem;
		align-content: start;
	}

	.hero {
		display: grid;
		justify-items: center;
		gap: 0.45rem;
		text-align: center;
	}

	.hero-subline {
		margin: 0;
		font-size: 0.82rem;
		color: var(--hud-muted);
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	h1 {
		margin: 0;
		font-size: clamp(3.1rem, 19vw, 7.5rem);
		line-height: 0.95;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.single-button {
		margin-top: 0.4rem;
		padding: 0.6rem 1rem;
		border-radius: 0.8rem;
		border: 1px solid var(--hud-border-accent);
		background: #153a15;
		color: var(--hud-text);
		font-size: 1rem;
		font-weight: 700;
	}

	.rondell-wrap {
		display: grid;
		gap: 0.75rem;
		justify-items: center;
	}

	.rondell {
		position: relative;
		width: min(90vw, 25rem);
		aspect-ratio: 1;
		border-radius: 50%;
		border: 1px dashed var(--hud-border-accent);
	}

	.sensor-tile {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 6.3rem;
		padding: 0.42rem;
		border-radius: 0.8rem;
		border: 1px solid var(--hud-border);
		background: #0f0f0f;
		transform: translate(-50%, -50%) rotate(calc(360deg / var(--total) * var(--index))) translate(9.2rem)
			rotate(calc(-360deg / var(--total) * var(--index)));
		text-align: center;
	}

	.sensor-tile.is-active {
		border-color: var(--hud-accent);
		box-shadow: 0 0 0 2px rgb(158 255 158 / 22%);
		background: #143114;
	}

	.tile-label {
		margin: 0;
		font-size: 0.74rem;
		color: var(--hud-muted);
	}

	.tile-value {
		margin: 0.2rem 0 0;
		font-size: 0.88rem;
		font-weight: 700;
	}

	.connection-state {
		margin: 0;
		font-size: 0.8rem;
		color: var(--hud-muted);
		text-align: center;
	}

	.hint-wrap {
		min-height: 1.8rem;
		display: grid;
		align-items: end;
	}
</style>
