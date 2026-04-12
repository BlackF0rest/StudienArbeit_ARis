<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchHudStatus, type HudStatus } from '$lib/services/basic-hud';
	import { featureHost } from '$lib/feature-host';
	import { isArCompactEnabled, isDebugUiEnabled } from '$lib/runtime-flags';

	let now = new Date();
	let compactMode = false;
	let debugUiEnabled = false;
	let status: HudStatus = {
		battery: null,
		temperature: null,
		humidity: null,
		connection: 'offline',
		lastUpdated: new Date(0).toISOString()
	};

	function two(n: number): string {
		return String(n).padStart(2, '0');
	}

	async function refresh(): Promise<void> {
		status = await fetchHudStatus();
		featureHost.emit('basic-hud', 'hud.refresh', { connection: status.connection });
	}

	onMount(() => {
		compactMode = isArCompactEnabled();
		debugUiEnabled = isDebugUiEnabled();
		now = new Date();
		void refresh();

		const secondTick = setInterval(() => {
			now = new Date();
		}, 1000);

		const hudTick = setInterval(() => {
			void refresh();
		}, 5000);

		return () => {
			clearInterval(secondTick);
			clearInterval(hudTick);
		};
	});
</script>

<div class="hud-header">
	<div>
		<strong>{two(now.getHours())}:{two(now.getMinutes())}:{two(now.getSeconds())}</strong>
		<span class="divider">|</span>
		🔋 {status.battery ?? '?'}%
		<span class="divider">|</span>
		🌡️ {status.temperature ?? '?'}°C
		<span class="divider">|</span>
		💧 {status.humidity ?? '?'}%
	</div>
	<div class="connection {status.connection}">
		{status.connection === 'connected' ? '🟢 Connected' : status.connection === 'degraded' ? '🟡 Degraded' : '🔴 Offline'}
	</div>
</div>

{#if debugUiEnabled && !compactMode}
	<nav class="hud-nav-row" aria-label="Debug navigation shortcuts">
		<a href="/">Home</a>
		<a href="/Navigation">Navigation</a>
		<a href="/Teleprompter?debug=1">Teleprompter</a>
		<a href="/Messages">Messages</a>
		<a href="/Debug">Debug</a>
	</nav>
{/if}

<style>
	.hud-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--hud-space-sm);
		padding: var(--hud-space-sm) var(--hud-space-md);
		border: 1px dashed #2fff44;
		color: #9dff9d;
		font-family: var(--hud-font-stack);
		font-size: var(--hud-font-sm);
	}

	.divider {
		opacity: 0.55;
		margin: 0 0.3rem;
	}

	.connection {
		font-size: var(--hud-font-xs);
	}

	.hud-nav-row {
		display: flex;
		align-items: center;
		gap: var(--hud-space-sm);
		padding: 0 var(--hud-space-md) var(--hud-space-xs);
		font-size: var(--hud-font-xs);
	}

	.hud-nav-row a {
		color: var(--hud-accent);
		text-decoration: none;
		padding: 0.1rem 0.35rem;
		border: 1px solid var(--hud-border-accent);
		border-radius: 999px;
	}
</style>
