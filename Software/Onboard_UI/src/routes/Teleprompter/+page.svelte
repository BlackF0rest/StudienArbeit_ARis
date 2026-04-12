<script lang="ts">
	import Teleprompter from './teleprompter.svelte';
	import { isDebugUiEnabled } from '$lib/runtime-flags';

	$: debugMode = isDebugUiEnabled();
</script>

<Teleprompter {debugMode} />
