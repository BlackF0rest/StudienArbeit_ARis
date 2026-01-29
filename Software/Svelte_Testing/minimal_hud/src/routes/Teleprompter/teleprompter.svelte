<script lang="ts">
    import { onMount } from 'svelte';
    
    interface TeleprompterConfig {
        text: string;
        speed: number;
        fontSize: number;
        fontColor: string;
        backgroundColor: string;
        fontFamily: string;
        lineHeight: number;
        opacity: number;
    }
    
    let config: TeleprompterConfig = {
        text: 'Warte auf Signal...',
        speed: 30,
        fontSize: 2,
        fontColor: '#0f0',
        backgroundColor: '#000',
        fontFamily: 'Courier New',
        lineHeight: 1.5,
        opacity: 1
    };
    
    let scrollPosition = 0;
    let isScrolling = true;
    let teleprompterContainer: HTMLElement;
    
    async function fetchLatestConfig() {
        try {
            const res = await fetch('http://localhost:5000/api/teleprompter/current');
            config = await res.json();
            scrollPosition = 0;
            isScrolling = true;
        } catch (error) {
            console.error('Fehler beim Abrufen:', error);
        }
    }
    
    onMount(() => {
        // Einmalig beim Laden abrufen
        fetchLatestConfig();
        
        // Dann jede Sekunde prüfen (für Aktualisierungen von der Companion App)
        const pollInterval = setInterval(fetchLatestConfig, 1000);
        
        // Animation Loop
        let animationId: number;
        
        const scroll = () => {
            if (isScrolling && teleprompterContainer) {
                scrollPosition += config.speed / 60;
                
                if (scrollPosition > teleprompterContainer.scrollHeight) {
                    scrollPosition = -window.innerHeight;
                }
            }
            animationId = requestAnimationFrame(scroll);
        };
        
        animationId = requestAnimationFrame(scroll);
        
        // Keyboard: ESC für Home
        const handleKeyPress = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                window.location.href = '/';
            }
        };
        
        window.addEventListener('keydown', handleKeyPress);
        
        return () => {
            clearInterval(pollInterval);
            cancelAnimationFrame(animationId);
            window.removeEventListener('keydown', handleKeyPress);
        };
    });
</script>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    
    .teleprompter-full {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .teleprompter-content {
        position: absolute;
        width: 95%;
        max-width: 1200px;
        white-space: pre-wrap;
        word-break: break-word;
        text-align: center;
    }
    
    .home-button {
        position: fixed;
        bottom: 20px;
        left: 20px;
        padding: 15px 25px;
        background: #0f0;
        color: #000;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        font-size: 0.95rem;
        z-index: 1000;
        transition: all 0.3s;
        font-family: 'Courier New', monospace;
    }
    
    .home-button:hover {
        background: #00ff00;
        transform: scale(1.1);
    }
    
    .home-button:active {
        transform: scale(0.95);
    }
</style>

<div 
    class="teleprompter-full" 
    style="background-color: {config.backgroundColor};"
>
    <div
        class="teleprompter-content"
        bind:this={teleprompterContainer}
        style="
            transform: translateY({scrollPosition}px);
            font-size: {config.fontSize}rem;
            color: {config.fontColor};
            font-family: {config.fontFamily};
            line-height: {config.lineHeight};
            opacity: {config.opacity};
        "
    >
        {config.text}
    </div>
</div>

<button class="home-button" on:click={() => window.location.href = '/'}>
    🏠 Home
</button>
