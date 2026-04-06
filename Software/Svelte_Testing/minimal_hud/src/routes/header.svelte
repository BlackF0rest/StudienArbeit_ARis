<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchHudStatus, type HudStatus } from '$lib/services/basic-hud';
	import { featureHost } from '$lib/feature-host';

	let now = new Date();
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

<nav class="main-nav">
	<a href="/">Host</a>
	<a href="/Navigation">Navigation</a>
	<a href="/Teleprompter">Teleprompter</a>
	<a href="/Messages">AI Chat</a>
</nav>

<style>
	.hud-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 0.8rem 1rem;
		border: 1px dashed #2fff44;
		color: #9dff9d;
		font-family: var(--hud-font-stack);
	}

	.divider {
		opacity: 0.55;
		margin: 0 0.3rem;
	}

	.connection {
		font-size: 0.9rem;
	}

	.main-nav {
		display: flex;
		gap: 1rem;
		padding: 0.8rem 0.4rem 0.4rem;
		font-family: var(--hud-font-stack);
	}

	a {
		color: #80ff80;
		text-decoration: none;
		border: 1px solid #1f5e1f;
		padding: 0.25rem 0.55rem;
	}
</style>
