import { browser } from '$app/environment';

const TRUE_VALUES = new Set(['1', 'true', 'yes', 'on']);
const PRODUCTION_PROFILE_VALUES = new Set(['prod', 'production', 'launch']);

function normalize(value: string | null | undefined): string {
	return String(value ?? '')
		.trim()
		.toLowerCase();
}

function readEnvFlag(names: string[]): string {
	const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env ?? {};
	for (const name of names) {
		const value = normalize(env[name]);
		if (value) return value;
	}
	return '';
}

export function isArCompactEnabled(): boolean {
	const envValue = readEnvFlag(['AR_COMPACT', 'VITE_AR_COMPACT']);
	if (TRUE_VALUES.has(envValue)) return true;

	if (!browser) return false;

	const queryValue = normalize(new URLSearchParams(window.location.search).get('AR_COMPACT'));
	if (TRUE_VALUES.has(queryValue)) return true;

	const storageValue = normalize(window.localStorage.getItem('AR_COMPACT'));
	return TRUE_VALUES.has(storageValue);
}

export function isProductionProfile(): boolean {
	const profileValue = readEnvFlag(['ONBOARD_PROFILE', 'VITE_ONBOARD_PROFILE', 'PROFILE']);
	if (PRODUCTION_PROFILE_VALUES.has(profileValue)) return true;
	return import.meta.env.PROD;
}

export function shouldExposeDevRoutes(): boolean {
	return !isProductionProfile();
}
