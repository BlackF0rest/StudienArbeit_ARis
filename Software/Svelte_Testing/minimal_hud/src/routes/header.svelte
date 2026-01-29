<script lang="ts">
    import { onMount } from 'svelte';
    
    interface DataType {
        Battery?: number;
        Temperature?: number;
        Humidity?: number;
    }
    
    let data: DataType = {};
    let time = new Date();
    let hours: number;
    let minutes: number;
    let seconds: number;
    
    $: hours = time.getHours();
    $: minutes = time.getMinutes();
    $: seconds = time.getSeconds();
    
    function two(n: number) { 
        return String(n).padStart(2, '0'); 
    }
    
    async function fetchData() {
        try {
            const res = await fetch('http://localhost:5000/api/mainInfo');
            data = await res.json();
        } catch (error) {
            console.error('Fehler beim Abrufen der Daten:', error);
        }
    }
    
    onMount(() => {
        fetchData();
        const interval = setInterval(() => {
            time = new Date();
            fetchData();
        }, 5000);
        return () => clearInterval(interval);
    });
</script>

<style>
    #interface {
        position: sticky;
        top: 0;
        background: #000;
        color: #0f0;
        padding: 10px 20px;
        font-family: 'Courier New', monospace;
        z-index: 1000;
    }
    
    h1 {
        margin: 0;
        font-size: 1.2rem;
        letter-spacing: 2px;
    }
</style>

<div id="interface">
    <h1>{two(hours)}:{two(minutes)} | 🔋{data.Battery ?? '?'} | 🌡️{data.Temperature ?? '?'} | 💧{data.Humidity ?? '?'}</h1>
</div>
