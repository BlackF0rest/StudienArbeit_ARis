<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { createChatProvider, loadHistory, saveHistory, newMessage, type ChatMessage } from '$lib/services/ai-chat';
	import { featureHost } from '$lib/feature-host';
	import { shortPressPulse, getHintForContext, openNavigationViaInput, setInputContext, type InputHint } from '$lib/input-controller';
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
	let pulseToken = 0;
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

	onMount(() => {
		const clearActions = setInputContext('messages', {
			onSingle: cycleSections,
			onDouble: () => {
				openNavigationViaInput();
				featureHost.emit('ai-chat-scaffold', 'chat.return_home', { reason: 'double-tap' });
			}
		});
		const unsubscribePulse = shortPressPulse.subscribe((value) => {
			pulseToken = value;
		});

		return () => {
			clearActions();
			unsubscribePulse();
		};
	});
</script>

<Header />

<HudScaffold title="AI Chat Scaffold" subtitle={`Provider: ${provider.name}`}>
	<svelte:fragment slot="header">
		<StatusPill text={provider.enabled ? 'Provider Enabled' : 'Demo Mode'} tone={provider.enabled ? 'ok' : 'warn'} />
	</svelte:fragment>

	<HudTabs tabs={sections} activeIndex={activeSectionIndex} {pulseToken} />

	{#if activeSectionIndex === 0}
		<HudCard title="Compact status" className="hud-compact-block">
			<p class="hud-primary-point">{history.length}</p>
			<p class="hud-secondary-line">messages stored</p>
			<p class="hud-compact-line">{provider.name} · {provider.enabled ? 'live' : 'mock/demo'} · {busy ? 'working' : 'idle'}</p>
			<p class="hud-compact-line">Showing latest {Math.min(previewMessages.length, 2)} entries</p>
		</HudCard>

		<HudCard title="Latest messages" className="hud-compact-block">
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
		<section class="hud-stack-sm">
			{#if history.length === 0}
				<p>Noch keine Nachrichten.</p>
			{:else}
				{#each history as message}
					<HudCard>
						<div class="hud-muted hud-meta-line">{message.role} · {message.createdAt}</div>
						<div class={`hud-message-content ${message.role === 'user' ? 'is-user' : 'is-assistant'}`}>
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
