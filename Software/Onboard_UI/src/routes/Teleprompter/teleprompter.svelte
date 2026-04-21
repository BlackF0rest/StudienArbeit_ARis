<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { TeleprompterRuntime, defaultTeleprompterConfig, type TeleprompterConfig } from '$lib/services/teleprompter-runtime';
	import { featureHost } from '$lib/feature-host';
	import { registerAppActions, setInputContext } from '$lib/input-controller';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	let { debugMode = false }: { debugMode?: boolean } = $props();

	let config: TeleprompterConfig = defaultTeleprompterConfig;
	let runtimeState = 'booting';
	let scrollPosition = 0;
	let isScrolling = true;
	let teleprompterContainer: HTMLElement;
	let feedbackText = '';
	let feedbackTimeout: ReturnType<typeof setTimeout> | undefined;

	const SHOW_CLICK_HOME_FALLBACK = debugMode;
	const MIN_FONT_REM = 1.0;
	const MAX_FONT_REM = 1.9;
	const MIN_LINE_HEIGHT = 1.18;
	const MAX_LINE_HEIGHT = 1.52;

	const clampedFontSize = $derived(
		Math.min(
			MAX_FONT_REM,
			Math.max(MIN_FONT_REM, Number(config.fontSize) || defaultTeleprompterConfig.fontSize)
		)
	);

	const clampedLineHeight = $derived(
		Math.min(
			MAX_LINE_HEIGHT,
			Math.max(MIN_LINE_HEIGHT, Number(config.lineHeight) || defaultTeleprompterConfig.lineHeight)
		)
	);
	async function returnHome(): Promise<void> {
		await goto('/');
	}

	function showFeedback(message: string): void {
		feedbackText = message;
		if (feedbackTimeout) clearTimeout(feedbackTimeout);
		feedbackTimeout = setTimeout(() => {
			feedbackText = '';
		}, 900);
	}

	function togglePauseResume(): void {
		isScrolling = !isScrolling;
		const state = isScrolling ? 'running' : 'paused';
		featureHost.emit('teleprompter-runtime', `teleprompter.${state}`, { speed: config.speed });
		showFeedback(state);
	}

	function speedStep(): void {
		const nextSpeed = Math.min(120, config.speed + 5);
		config = { ...config, speed: nextSpeed };
		featureHost.emit('teleprompter-runtime', 'teleprompter.speed_step', { speed: nextSpeed });
		showFeedback(`speed ${nextSpeed}`);
	}

	function onTeleprompterDoubleTap(): void {
		featureHost.emit('teleprompter-runtime', 'teleprompter.open_navigation', { reason: 'double-tap' });
		showFeedback('Opening navigation…');
	}

	onMount(() => {
		setInputContext('teleprompter');
		document.body.style.overflow = 'hidden';
		const unregister = registerAppActions({
			onSingle: speedStep,
			onDouble: onTeleprompterDoubleTap
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
			if (event.key === 'Escape') void returnHome();
			if (event.key === ' ') {
				event.preventDefault();
				togglePauseResume();
			}
			if (event.key === 'Enter') speedStep();
		};
		if (browser) {
			window.addEventListener('keydown', handleKeyPress);
		}

		return () => {
			unregister();
			runtime.stop();
			cancelAnimationFrame(animationId);
			if (browser) {
				window.removeEventListener('keydown', handleKeyPress);
			}
			if (feedbackTimeout) clearTimeout(feedbackTimeout);
			document.body.style.overflow = '';
		};
	});
</script>

{#if debugMode}
	<div class="teleprompter-debug-overlay">
		<HudCard title="Teleprompter Debug" className="is-muted">
			<div class="teleprompter-debug-headline">
				<StatusPill text={isScrolling ? 'Running' : 'Paused'} tone={isScrolling ? 'ok' : 'warn'} />
				<StatusPill text={`State: ${runtimeState}`} tone="info" />
			</div>
			<p class="teleprompter-debug-state">speed={config.speed} · scroll={Math.round(scrollPosition)}</p>
		</HudCard>
	</div>
{/if}

<div class="teleprompter-full" style="background-color: {config.backgroundColor};" on:pointerup={togglePauseResume}>
	<div class="teleprompter-state">
		{isScrolling ? '▶' : '⏸'} {config.speed}
		{#if feedbackText}
			<span class="teleprompter-feedback"> · {feedbackText}</span>
		{/if}
	</div>
	<div
		class="teleprompter-content"
		bind:this={teleprompterContainer}
		style="
            transform: translateY({scrollPosition}px);
            font-size: clamp({MIN_FONT_REM}rem, calc(0.72rem + 2.3vw), {clampedFontSize}rem);
            color: {config.fontColor};
            font-family: {config.fontFamily};
            line-height: {clampedLineHeight};
            opacity: {config.opacity};
        "
	>
		{config.text}
	</div>
</div>

{#if SHOW_CLICK_HOME_FALLBACK}
	<button class="teleprompter-home-button" on:click={() => void returnHome()} aria-label="Back to home">⌂</button>
{/if}
