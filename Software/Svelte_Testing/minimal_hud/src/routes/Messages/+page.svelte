<script lang="ts">
    import { onMount } from 'svelte';

    let data: never[] = [];
    let messages: never[] = [];

    let time = new Date();
    let hours: number;
    let minutes: number;
    let seconds: number;

    // Reaktive Variablen – werden jedes Mal aktualisiert, wenn "time" ODER "messages" sich ändert
    $: hours = time.getHours();
    $: minutes = time.getMinutes();
    $: seconds = time.getSeconds();

    $: latestMsgs = messages.slice(0,3);

    // Set für gerade angezeigte "neue" Nachrichten
    const shownRecently = new Set<string>();
    const NEW_SHOW_MS = 5000; // ms


    function two(n: number) { return String(n).padStart(2, '0'); }

    async function fetchData() {
    const res = await fetch('http://localhost:5000/api/mainInfo');
    data = await res.json();
    }

    async function fetchMessages() {
    const res = await fetch('http://localhost:5000/api/messages');
    messages = await res.json();
    }

    onMount(() => {
        const interval = setInterval(() => {
            time = new Date();
            fetchData();
            fetchMessages();
        }, 5000);
        return () => clearInterval(interval);
    });
</script>

<main>
    <div id="interface">
        <h1>{two(hours)}:{two(minutes)} | 🔋{data.Battery} | 🌡️{data.Temperature} | 💧{data.Humidity}</h1>
        <hr>
        <p>Messages:</p>
        {#each latestMsgs as msg}
        <p>{msg.content}</p>
        {/each}
    </div>
</main>
