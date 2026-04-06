<script lang="ts">
	import { onMount } from 'svelte';
	import {
		TeleprompterRuntime,
		defaultTeleprompterConfig,
		type TeleprompterConfig
	} from '$lib/services/teleprompter-runtime';
	import { featureHost } from '$lib/feature-host';
	import {
		getHintForContext,
		registerAppActions,
		setInputContext,
		type InputHint
	} from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';

	let config: TeleprompterConfig = defaultTeleprompterConfig;
	let runtimeState = 'booting';
	let scrollPosition = 0;
	let isScrolling = true;
	let teleprompterContainer: HTMLElement;
	let hint: InputHint = getHintForContext('teleprompter');

	function speedStep(): void {
		const nextSpeed = Math.min(120, config.speed + 5);
		config = { ...config, speed: nextSpeed };
		featureHost.emit('teleprompter-runtime', 'teleprompter.speed_step', { speed: nextSpeed });
	}

	function togglePauseResume(): void {
		isScrolling = !isScrolling;
		featureHost.emit('teleprompter-runtime', 'teleprompter.pause_toggle', { isScrolling });
	}

	onMount(() => {
		setInputContext('teleprompter');
		const unregister = registerAppActions({
			onShort: speedStep,
			onLong: togglePauseResume
		});

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
			unregister();
			runtime.stop();
			cancelAnimationFrame(animationId);
			window.removeEventListener('keydown', handleKeyPress);
		};
	});
</script>

<div class="teleprompter-full" style="background-color: {config.backgroundColor};">
	<div class="state">Runtime: {runtimeState} · {isScrolling ? 'running' : 'paused'} · speed {config.speed}</div>
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
<InputHintOverlay {hint} />

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
		bottom: 46px;
		left: 20px;
		padding: 12px 22px;
		background: #0f0;
		color: #000;
		border: none;
		border-radius: 8px;
		cursor: pointer;
	}
</style>
