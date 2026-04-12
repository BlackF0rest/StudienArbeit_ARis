import { error } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import { shouldExposeDevRoutes } from '$lib/runtime-flags';

export const load: LayoutLoad = () => {
	if (!shouldExposeDevRoutes()) {
		throw error(404, 'Not found');
	}
};
