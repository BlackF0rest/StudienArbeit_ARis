<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import {
		createChatProvider,
		loadHistory,
		saveHistory,
		newMessage,
		type ChatMessage
	} from '$lib/services/ai-chat';
	import { featureHost } from '$lib/feature-host';
	import {
		getHintForContext,
		registerAppActions,
		setInputContext,
		type InputHint
	} from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';

	const ENABLE_REAL_PROVIDER = false;
	const provider = createChatProvider(ENABLE_REAL_PROVIDER);
	const sections = ['provider', 'compose', 'history'];

	let input = '';
	let busy = false;
	let activeSectionIndex = 0;
	let hint: InputHint = getHintForContext('messages');
	let history: ChatMessage[] = loadHistory();

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

<main>
	<h2>AI Chat Scaffold</h2>
	<div class="sections">
		{#each sections as section, index}
			<span class:active={index === activeSectionIndex}>{section}</span>
		{/each}
	</div>

	{#if activeSectionIndex === 0}
		<p>Provider: {provider.name} ({provider.enabled ? 'enabled' : 'disabled for demo'})</p>
	{:else if activeSectionIndex === 1}
		<p>Compose is intentionally not bound to HID; companion input app handles text entry.</p>
	{:else}
		<p>History view active ({history.length} entries).</p>
	{/if}

	<form
		on:submit={(event) => {
			event.preventDefault();
			void submit();
		}}
	>
		<input bind:value={input} placeholder="Prompt eingeben..." />
		<button type="submit" disabled={busy}>{busy ? 'Sende...' : 'Senden'}</button>
	</form>

	<section class="history">
		{#if history.length === 0}
			<p>Noch keine Nachrichten.</p>
		{:else}
			{#each history as message}
				<article class="msg {message.role}">
					<div class="meta">{message.role} · {message.createdAt}</div>
					<div>{message.content}</div>
				</article>
			{/each}
		{/if}
	</section>
</main>

<InputHintOverlay {hint} />

<style>
	main { padding: 0.6rem 1rem; }
	.sections {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}
	.sections span {
		padding: 0.2rem 0.45rem;
		border: 1px solid #335033;
		opacity: 0.7;
	}
	.sections span.active {
		opacity: 1;
		color: #9eff9e;
	}
	form { display: flex; gap: 0.4rem; margin-bottom: 0.8rem; }
	input {
		flex: 1;
		padding: 0.5rem;
		background: #111;
		border: 1px solid #2f2f2f;
		color: #fff;
	}
	button { padding: 0.5rem 0.8rem; }
	.history { display: grid; gap: 0.4rem; }
	.msg { border: 1px solid #2e2e2e; padding: 0.5rem; }
	.msg.user { border-left: 3px solid #7eff7e; }
	.msg.assistant { border-left: 3px solid #7ea9ff; }
	.meta { font-size: 0.8rem; opacity: 0.7; }
</style>
