<script lang="ts">
	import { onMount } from 'svelte';
	import { TeleprompterRuntime, defaultTeleprompterConfig, type TeleprompterConfig } from '$lib/services/teleprompter-runtime';
	import { featureHost } from '$lib/feature-host';
	import { getHintForContext, registerAppActions, setInputContext, type InputHint } from '$lib/input-controller';
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
		document.body.style.overflow = 'hidden';
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
			document.body.style.overflow = '';
		};
	});
</script>

<div class="teleprompter-full" style="background-color: {config.backgroundColor};">
	<div class="teleprompter-state">Runtime: {runtimeState} · {isScrolling ? 'running' : 'paused'} · speed {config.speed}</div>
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

<button class="teleprompter-home-button" on:click={() => (window.location.href = '/')}>🏠 Home</button>
<InputHintOverlay {hint} />
