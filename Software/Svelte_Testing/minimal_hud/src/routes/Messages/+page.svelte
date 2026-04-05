<script lang="ts">
	import Header from '../header.svelte';
	import {
		createChatProvider,
		loadHistory,
		saveHistory,
		newMessage,
		type ChatMessage
	} from '$lib/services/ai-chat';
	import { featureHost } from '$lib/feature-host';

	const ENABLE_REAL_PROVIDER = false;
	const provider = createChatProvider(ENABLE_REAL_PROVIDER);

	let input = '';
	let busy = false;
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
</script>

<Header />

<main>
	<h2>AI Chat Scaffold</h2>
	<p>Provider: {provider.name} ({provider.enabled ? 'enabled' : 'disabled for demo'})</p>

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

<style>
	main { padding: 0.6rem 1rem; }
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
