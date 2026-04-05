<script lang="ts">
	import { onMount } from 'svelte';
	import Header from './header.svelte';
	import { bootstrapFeatureHost } from '$lib/feature-registration';
	import { featureHost, type FeatureRuntimeSnapshot } from '$lib/feature-host';

	let snapshot: FeatureRuntimeSnapshot = {
		registered: [],
		health: {},
		telemetry: []
	};

	async function refreshSnapshot(): Promise<void> {
		snapshot = await featureHost.snapshot();
	}

	onMount(() => {
		bootstrapFeatureHost();
		void refreshSnapshot();
		const timer = setInterval(() => void refreshSnapshot(), 3000);
		return () => clearInterval(timer);
	});
</script>

<Header />

<main>
	<h2>Feature Host Runtime</h2>
	<div class="grid">
		{#each snapshot.registered as module}
			<section class="card">
				<h3>{module.name}</h3>
				<p>{module.description}</p>
				<p><strong>Version:</strong> {module.version}</p>
				<p><strong>Permissions:</strong> {module.permissions.join(', ')}</p>
				<p><strong>Dependencies:</strong> {module.dependencies.join(', ')}</p>
				<p>
					<strong>Health:</strong>
					{snapshot.health[module.id]?.ok ? '✅' : '❌'} {snapshot.health[module.id]?.details}
				</p>
			</section>
		{/each}
	</div>

	<section class="telemetry">
		<h3>Telemetry (latest)</h3>
		{#if snapshot.telemetry.length === 0}
			<p>No telemetry yet.</p>
		{:else}
			{#each snapshot.telemetry.slice(0, 8) as event}
				<p>{event.createdAt} · {event.featureId} · {event.type}</p>
			{/each}
		{/if}
	</section>
</main>

<style>
	main {
		padding: 0.4rem 0.8rem;
		font-family: Arial, sans-serif;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.8rem;
	}
	.card {
		border: 1px solid #2f2f2f;
		padding: 0.7rem;
		background: #090909;
	}
	.telemetry {
		margin-top: 1rem;
		border-top: 1px solid #292929;
		padding-top: 0.7rem;
	}
</style>
