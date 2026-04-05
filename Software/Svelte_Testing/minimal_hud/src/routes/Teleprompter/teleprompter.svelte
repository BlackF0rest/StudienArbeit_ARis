<script lang="ts">
	import { onMount } from 'svelte';
	import {
		TeleprompterRuntime,
		defaultTeleprompterConfig,
		type TeleprompterConfig
	} from '$lib/services/teleprompter-runtime';
	import { featureHost } from '$lib/feature-host';

	let config: TeleprompterConfig = defaultTeleprompterConfig;
	let runtimeState = 'booting';
	let scrollPosition = 0;
	let isScrolling = true;
	let teleprompterContainer: HTMLElement;

	onMount(() => {
		const runtime = new TeleprompterRuntime(
			(nextConfig) => {
				config = nextConfig;
				featureHost.emit('teleprompter-runtime', 'teleprompter.update', { speed: nextConfig.speed });
			},
			(state) => {
				runtimeState = state;
			}
		);

		runtime.start();

		let animationId: number;
		const scroll = () => {
			if (isScrolling && teleprompterContainer) {
				scrollPosition += config.speed / 60;
				if (scrollPosition > teleprompterContainer.scrollHeight) {
					scrollPosition = -window.innerHeight;
				}
			}
			animationId = requestAnimationFrame(scroll);
		};
		animationId = requestAnimationFrame(scroll);

		const handleKeyPress = (event: KeyboardEvent) => {
			if (event.key === 'Escape') window.location.href = '/';
		};
		window.addEventListener('keydown', handleKeyPress);

		return () => {
			runtime.stop();
			cancelAnimationFrame(animationId);
			window.removeEventListener('keydown', handleKeyPress);
		};
	});
</script>

<div class="teleprompter-full" style="background-color: {config.backgroundColor};">
	<div class="state">Runtime: {runtimeState}</div>
	<div
		class="teleprompter-content"
		bind:this={teleprompterContainer}
		style="
            transform: translateY({scrollPosition}px);
            font-size: {config.fontSize}rem;
            color: {config.fontColor};
            font-family: {config.fontFamily};
            line-height: {config.lineHeight};
            opacity: {config.opacity};
        "
	>
		{config.text}
	</div>
</div>

<button class="home-button" on:click={() => (window.location.href = '/')}>🏠 Home</button>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		overflow: hidden;
	}
	.teleprompter-full {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.state {
		position: fixed;
		top: 14px;
		right: 14px;
		background: rgba(0, 0, 0, 0.55);
		padding: 6px 10px;
		font-family: 'Courier New', monospace;
		color: #9eff9e;
	}
	.teleprompter-content {
		position: absolute;
		width: 95%;
		max-width: 1200px;
		white-space: pre-wrap;
		word-break: break-word;
		text-align: center;
	}
	.home-button {
		position: fixed;
		bottom: 20px;
		left: 20px;
		padding: 12px 22px;
		background: #0f0;
		color: #000;
		border: none;
		border-radius: 8px;
		cursor: pointer;
	}
</style>
