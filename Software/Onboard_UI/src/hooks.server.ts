import { error } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';
import { isProductionProfile } from '$lib/runtime-flags';

function isDevRoute(pathname: string): boolean {
	return pathname === '/dev' || pathname.startsWith('/dev/');
}

export const handle: Handle = async ({ event, resolve }) => {
	if (isProductionProfile() && isDevRoute(event.url.pathname)) {
		throw error(404, 'Not found');
	}

	return resolve(event);
};
