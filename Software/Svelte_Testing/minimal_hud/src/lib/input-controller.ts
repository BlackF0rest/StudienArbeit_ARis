import { goto } from '$app/navigation';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type InputGesture = 'short' | 'long';
export type InputFsmState = 'home-carousel' | 'feature-active' | 'confirm-exit';
export type AppContext = 'home' | 'teleprompter' | 'navigation' | 'messages' | 'chat' | 'debug';

export interface InputHint {
	short: string;
	long: string;
}

interface InputControlEvent {
	gesture: InputGesture;
	source?: string;
}

interface AppActionHandlers {
	onShort?: () => void;
	onLong?: () => void;
}

const HOME_APPS = [
	{ route: '/Navigation', name: 'Navigation' },
	{ route: '/Teleprompter', name: 'Teleprompter' },
	{ route: '/Messages', name: 'Messages/HUD' }
] as const;

export const inputFsmState = writable<InputFsmState>('home-carousel');
export const homeCarouselIndex = writable(0);

let currentContext: AppContext = 'home';
let handlers: AppActionHandlers = {};
let teardownInput: (() => void) | null = null;
let confirmExitTimer: ReturnType<typeof setTimeout> | null = null;

function normalizeGesture(payload: unknown): InputGesture | null {
	if (!payload || typeof payload !== 'object') return null;
	const value = (payload as Record<string, unknown>).gesture;
	if (value === 'short' || value === 'long') return value;
	return null;
}

function enterConfirmExitState(): void {
	inputFsmState.set('confirm-exit');
	if (confirmExitTimer) clearTimeout(confirmExitTimer);
	confirmExitTimer = setTimeout(() => {
		inputFsmState.set('home-carousel');
		void goto('/');
	}, 120);
}

function onHomeShort(): void {
	homeCarouselIndex.update((index) => (index + 1) % HOME_APPS.length);
}

function onHomeLong(): void {
	let target = HOME_APPS[0];
	homeCarouselIndex.update((index) => {
		target = HOME_APPS[index] ?? HOME_APPS[0];
		return index;
	});
	inputFsmState.set('feature-active');
	void goto(target.route);
}

function onGesture(gesture: InputGesture): void {
	if (currentContext === 'chat') return;

	if (currentContext === 'home') {
		if (gesture === 'short') onHomeShort();
		if (gesture === 'long') onHomeLong();
		return;
	}

	if (gesture === 'short') {
		handlers.onShort?.();
		return;
	}

	if (currentContext === 'teleprompter') {
		handlers.onLong?.();
		return;
	}

	handlers.onLong?.();
	enterConfirmExitState();
}

function eventHandler(event: Event): void {
	const custom = event as CustomEvent<InputControlEvent>;
	const gesture = normalizeGesture(custom.detail);
	if (!gesture) return;
	onGesture(gesture);
}

function keyboardFallback(event: KeyboardEvent): void {
	if (event.key === ' ' || event.key === 'ArrowRight') {
		event.preventDefault();
		onGesture('short');
	}

	if (event.key === 'Enter') {
		event.preventDefault();
		onGesture('long');
	}
}

export function subscribeInputControl(): void {
	if (!browser || teardownInput) return;

	window.addEventListener('input.control', eventHandler as EventListener);
	window.addEventListener('keydown', keyboardFallback);
	teardownInput = () => {
		window.removeEventListener('input.control', eventHandler as EventListener);
		window.removeEventListener('keydown', keyboardFallback);
		teardownInput = null;
	};
}

export function detachInputControl(): void {
	teardownInput?.();
	if (confirmExitTimer) clearTimeout(confirmExitTimer);
	confirmExitTimer = null;
}

export function setInputContext(context: AppContext): void {
	currentContext = context;
	if (context === 'home') {
		inputFsmState.set('home-carousel');
		handlers = {};
		return;
	}
	if (context === 'chat') {
		inputFsmState.set('feature-active');
		handlers = {};
		return;
	}
	inputFsmState.set('feature-active');
}

export function registerAppActions(actionHandlers: AppActionHandlers): () => void {
	handlers = actionHandlers;
	return () => {
		handlers = {};
	};
}

export function getHintForContext(context: AppContext): InputHint {
	switch (context) {
		case 'home':
			return {
				short: 'next app',
				long: 'open selected app'
			};
		case 'teleprompter':
			return {
				short: 'speed + step',
				long: 'pause / resume'
			};
		case 'navigation':
			return {
				short: 'cycle info panel',
				long: 'return home'
			};
		case 'messages':
			return {
				short: 'cycle sections',
				long: 'return home'
			};
		case 'chat':
			return {
				short: 'n/a',
				long: 'AI chat input via companion app'
			};
		case 'debug':
			return {
				short: 'refresh diagnostics',
				long: 'return home'
			};
	}
}

export function emitInputControl(gesture: InputGesture): void {
	if (!browser) return;
	window.dispatchEvent(new CustomEvent<InputControlEvent>('input.control', { detail: { gesture } }));
}
