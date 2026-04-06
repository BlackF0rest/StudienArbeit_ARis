<script lang="ts">
    import { onMount } from 'svelte';
	import Header from './header.svelte';

    let data: never[] = [];

    let time = new Date();
    let hours: number;
    let minutes: number;
    let seconds: number;

    // Reaktive Variablen – werden jedes Mal aktualisiert, wenn "time" ODER "messages" sich ändert
    $: hours = time.getHours();
    $: minutes = time.getMinutes();
    $: seconds = time.getSeconds();


    function two(n: number) { return String(n).padStart(2, '0'); }

    async function fetchData() {
    const res = await fetch('http://localhost:5000/api/mainInfo');
    data = await res.json();
    }

    onMount(() => {
        const interval = setInterval(() => {
            time = new Date();
            fetchData();
        }, 5000);
        return () => clearInterval(interval);
    });
</script>

<Header />

<main>
    
</main>