import { goto } from '$app/navigation';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type InputGesture = 'single' | 'double';
export type InputFsmState = 'home-carousel' | 'feature-active';
export type AppContext = 'home' | 'teleprompter' | 'navigation' | 'messages' | 'chat' | 'debug';

export interface InputHint {
	single: string;
	double: string;
}

interface InputControlEvent {
	gesture: InputGesture;
	source?: string;
}

interface AppActionHandlers {
	onSingle?: () => void;
	onDouble?: () => void;
}

const HOME_APPS = [
	{ route: '/Teleprompter', name: 'Teleprompter' },
	{ route: '/Messages', name: 'Messages/HUD' }
] as const;

export const inputFsmState = writable<InputFsmState>('home-carousel');
export const homeCarouselIndex = writable(0);
export const shortPressPulse = writable(0);
export const inputStatus = writable('');

let currentContext: AppContext = 'home';
let handlers: AppActionHandlers = {};
let teardownInput: (() => void) | null = null;
let inputStatusTimer: ReturnType<typeof setTimeout> | null = null;

function normalizeGesture(payload: unknown): InputGesture | null {
	if (!payload || typeof payload !== 'object') return null;
	const value = (payload as Record<string, unknown>).gesture;
	if (value === 'single' || value === 'double') return value;
	return null;
}

function triggerGlobalNavigation(): void {
	inputFsmState.set('feature-active');
	inputStatus.set('Opening navigation…');
	if (inputStatusTimer) clearTimeout(inputStatusTimer);
	inputStatusTimer = setTimeout(() => {
		inputStatus.set('');
	}, 950);
	void goto('/Navigation');
}

export function openNavigationViaInput(): void {
	triggerGlobalNavigation();
}

function onHomeSingle(): void {
	homeCarouselIndex.update((index) => (index + 1) % HOME_APPS.length);
}

function onGesture(gesture: InputGesture): void {
	if (gesture === 'double') {
		if (currentContext === 'home') {
			triggerGlobalNavigation();
			return;
		}
		if (handlers.onDouble) {
			handlers.onDouble();
			return;
		}
		triggerGlobalNavigation();
		return;
	}

	if (currentContext === 'chat') return;

	if (currentContext === 'home') {
		shortPressPulse.update((value) => value + 1);
		onHomeSingle();
		return;
	}

	shortPressPulse.update((value) => value + 1);
	handlers.onSingle?.();
}

function eventHandler(event: Event): void {
	const custom = event as CustomEvent<InputControlEvent>;
	const gesture = normalizeGesture(custom.detail);
	if (!gesture) return;
	onGesture(gesture);
}

function keyboardFallback(event: KeyboardEvent): void {
	if (event.key === ' ') {
		event.preventDefault();
		onGesture('single');
	}

	if (event.key === 'Enter') {
		event.preventDefault();
		onGesture('double');
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
	if (inputStatusTimer) clearTimeout(inputStatusTimer);
	inputStatusTimer = null;
	inputStatus.set('');
}

export function setInputContext(context: AppContext, actionHandlers: AppActionHandlers = {}): () => void {
	currentContext = context;
	handlers = actionHandlers;

	if (context === 'home') {
		inputFsmState.set('home-carousel');
		inputStatus.set('');
		return () => {
			handlers = {};
		};
	}

	inputFsmState.set('feature-active');
	inputStatus.set('');
	return () => {
		handlers = {};
	};
}

export function getHintForContext(context: AppContext): InputHint {
	switch (context) {
		case 'home':
			return {
				single: 'next app',
				double: 'open navigation'
			};
		case 'teleprompter':
			return {
				single: 'speed + step',
				double: 'open navigation'
			};
		case 'navigation':
			return {
				single: 'cycle info panel',
				double: 'open navigation'
			};
		case 'messages':
			return {
				single: 'cycle sections',
				double: 'open navigation'
			};
		case 'chat':
			return {
				single: 'n/a',
				double: 'open navigation'
			};
		case 'debug':
			return {
				single: 'refresh diagnostics',
				double: 'open navigation'
			};
	}
}

export function emitInputControl(gesture: InputGesture): void {
	if (!browser) return;
	window.dispatchEvent(new CustomEvent<InputControlEvent>('input.control', { detail: { gesture } }));
}
