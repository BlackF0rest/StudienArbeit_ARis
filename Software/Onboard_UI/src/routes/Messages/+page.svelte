<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { createChatProvider, loadHistory, saveHistory, newMessage, type ChatMessage } from '$lib/services/ai-chat';
	import { featureHost } from '$lib/feature-host';
	import { getHintForContext, registerAppActions, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import HudTabs from '$lib/components/hud/HudTabs.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	const ENABLE_REAL_PROVIDER = false;
	const provider = createChatProvider(ENABLE_REAL_PROVIDER);
	const sections = ['status', 'compose', 'history'];

	let input = '';
	let busy = false;
	let activeSectionIndex = 0;
	let hint: InputHint = getHintForContext('messages');
	let history: ChatMessage[] = loadHistory();

	$: previewMessages = history.slice(0, 2);

	async function submit(): Promise<void> {
		if (!input.trim() || busy) return;
		const prompt = input.trim();
		input = '';
		busy = true;

		const userMessage = newMessage('user', prompt);
		history = [userMessage, ...history].slice(0, 40);
		saveHistory(history);

		try {
			const reply = await provider.request(history, prompt);
			const assistantMessage = newMessage('assistant', reply);
			history = [assistantMessage, ...history].slice(0, 40);
			featureHost.emit('ai-chat-scaffold', 'chat.reply', {
				provider: provider.name,
				enabled: provider.enabled
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Provider Fehler';
			history = [newMessage('assistant', `Fehler: ${message}`), ...history].slice(0, 40);
		}

		saveHistory(history);
		busy = false;
	}

	function cycleSections(): void {
		activeSectionIndex = (activeSectionIndex + 1) % sections.length;
		featureHost.emit('ai-chat-scaffold', 'chat.section_cycle', { section: sections[activeSectionIndex] });
	}

	async function returnHome(): Promise<void> {
		featureHost.emit('ai-chat-scaffold', 'chat.return_home', { reason: 'long-press' });
		await goto('/');
	}

	onMount(() => {
		setInputContext('messages');
		const unregister = registerAppActions({
			onShort: cycleSections,
			onLong: () => {
				void returnHome();
			}
		});

		return () => unregister();
	});
</script>

<Header />

<HudScaffold title="AI Chat Scaffold" subtitle={`Provider: ${provider.name}`}>
	<svelte:fragment slot="header">
		<StatusPill text={provider.enabled ? 'Provider Enabled' : 'Demo Mode'} tone={provider.enabled ? 'ok' : 'warn'} />
	</svelte:fragment>

	<HudTabs tabs={sections} activeIndex={activeSectionIndex} />

	{#if activeSectionIndex === 0}
		<HudCard title="Compact status">
			<p class="hud-compact-line">{provider.name} · {provider.enabled ? 'live' : 'mock/demo'} · {busy ? 'working' : 'idle'}</p>
			<p class="hud-compact-line">Stored messages: {history.length} · Showing latest {Math.min(previewMessages.length, 2)}</p>
		</HudCard>

		<HudCard title="Latest messages">
			{#if previewMessages.length === 0}
				<p>Noch keine Nachrichten.</p>
			{:else}
				{#each previewMessages as message}
					<p class="hud-compact-line"><strong>{message.role}:</strong> {message.content}</p>
				{/each}
			{/if}
		</HudCard>
	{:else if activeSectionIndex === 1}
		<form class="hud-form-row" on:submit={(event) => {
			event.preventDefault();
			void submit();
		}}>
			<input class="hud-input" bind:value={input} placeholder="Prompt eingeben..." />
			<button class="hud-button" type="submit" disabled={busy}>{busy ? 'Sende...' : 'Senden'}</button>
		</form>
	{:else}
		<section style="display:grid;gap:0.4rem;">
			{#if history.length === 0}
				<p>Noch keine Nachrichten.</p>
			{:else}
				{#each history as message}
					<HudCard>
						<div class="hud-muted" style="font-size:0.8rem;">{message.role} · {message.createdAt}</div>
						<div style={`border-left:3px solid ${message.role === 'user' ? '#7eff7e' : '#7ea9ff'};padding-left:0.5rem;margin-top:0.2rem;`}>
							{message.content}
						</div>
					</HudCard>
				{/each}
			{/if}
		</section>
	{/if}

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
