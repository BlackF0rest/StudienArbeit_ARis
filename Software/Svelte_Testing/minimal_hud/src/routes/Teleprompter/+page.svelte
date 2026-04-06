<script lang="ts">
	import { page } from '$app/stores';
	import Teleprompter from './teleprompter.svelte';

	$: debugMode = $page.url.searchParams.get('mode') === 'debug' || $page.url.searchParams.get('debug') === '1';
</script>

<Teleprompter {debugMode} />
