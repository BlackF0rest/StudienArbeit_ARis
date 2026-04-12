import { browser } from '$app/environment';

const TRUE_VALUES = new Set(['1', 'true', 'yes', 'on']);

function normalize(value: string | null | undefined): string {
	return String(value ?? '')
		.trim()
		.toLowerCase();
}

export function isArCompactEnabled(): boolean {
	const envValue = normalize(
		((import.meta as unknown as { env?: Record<string, string | undefined> }).env?.AR_COMPACT ??
			(import.meta as unknown as { env?: Record<string, string | undefined> }).env?.VITE_AR_COMPACT) as
			| string
			| undefined
	);
	if (TRUE_VALUES.has(envValue)) return true;

	if (!browser) return false;

	const queryValue = normalize(new URLSearchParams(window.location.search).get('AR_COMPACT'));
	if (TRUE_VALUES.has(queryValue)) return true;

	const storageValue = normalize(window.localStorage.getItem('AR_COMPACT'));
	return TRUE_VALUES.has(storageValue);
}
