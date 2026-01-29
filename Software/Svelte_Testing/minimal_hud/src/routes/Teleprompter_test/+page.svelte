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
        text: 'Test Text für die AR-Brille...\n\nZeile 2\nZeile 3',
        speed: 30,
        fontSize: 2,
        fontColor: '#0f0',
        backgroundColor: '#000',
        fontFamily: 'Courier New',
        lineHeight: 1.5,
        opacity: 0.9
    };
    
    let scrollPosition = 0;
    let isScrolling = true;
    let teleprompterContainer: HTMLElement;
    let statusMessage = '';
    let isSending = false;
    
    async function fetchConfig() {
        try {
            const res = await fetch('http://localhost:5000/api/teleprompter');
            config = await res.json();
            scrollPosition = 0;
            statusMessage = '✓ Konfiguration geladen';
        } catch (error) {
            statusMessage = '❌ Fehler beim Laden';
            console.error(error);
        }
    }
    
    async function sendToGlasses() {
        isSending = true;
        statusMessage = '📡 Wird übertragen...';
        
        try {
            const res = await fetch('http://localhost:5000/api/teleprompter/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (res.ok) {
                statusMessage = '✓ Erfolgreich zur Brille gesendet!';
            } else {
                statusMessage = '❌ Fehler beim Senden';
            }
        } catch (error) {
            statusMessage = '❌ Verbindungsfehler';
            console.error(error);
        }
        
        isSending = false;
    }

    onMount(() => {
        fetchConfig();
        
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
        return () => cancelAnimationFrame(animationId);
    });
</script>

<style>
    Header {
        position: sticky;
        top: 0;
        z-index: 500;
    }
    
    .container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        padding: 20px;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .preview {
        border: 2px solid #0f0;
        border-radius: 8px;
        overflow: hidden;
        background: #000;
        position: relative;
        height: 600px;
    }
    
    .preview-content {
        position: absolute;
        width: 100%;
        white-space: pre-wrap;
        word-break: break-word;
        text-align: center;
        padding: 20px;
        overflow: hidden;
    }
    
    .controls-panel {
        display: flex;
        flex-direction: column;
        gap: 15px;
        background: #1a1a1a;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #0f0;
    }
    
    .control-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    label {
        color: #0f0;
        font-weight: bold;
        font-size: 0.9rem;
        font-family: 'Courier New', monospace;
    }
    
    input[type="text"],
    input[type="number"],
    input[type="range"],
    select {
        padding: 10px;
        background: #000;
        color: #0f0;
        border: 1px solid #0f0;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    
    input[type="text"] {
        min-height: 80px;
        resize: vertical;
    }
    
    textarea {
        padding: 10px;
        background: #000;
        color: #0f0;
        border: 1px solid #0f0;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        min-height: 120px;
        resize: vertical;
    }
    
    .slider-container {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    input[type="range"] {
        flex: 1;
    }
    
    .value-display {
        color: #0f0;
        font-family: 'Courier New', monospace;
        min-width: 60px;
        text-align: right;
    }
    
    .button-group {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 10px;
    }
    
    button {
        padding: 12px;
        background: #0f0;
        color: #000;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        font-size: 0.95rem;
        transition: all 0.3s;
        font-family: 'Courier New', monospace;
    }
    
    button:hover {
        background: #00ff00;
        transform: scale(1.02);
    }
    
    button:disabled {
        background: #666;
        cursor: not-allowed;
        opacity: 0.6;
    }
    
    .status-message {
        padding: 12px;
        background: #0f0;
        color: #000;
        border-radius: 4px;
        font-weight: bold;
        text-align: center;
        font-family: 'Courier New', monospace;
        min-height: 20px;
    }
    
    .send-button {
        grid-column: 1 / -1;
        background: #ff6b00;
        padding: 15px;
        font-size: 1.1rem;
    }
    
    .send-button:hover {
        background: #ff8c00;
    }
    
    .playback-controls {
        display: flex;
        gap: 10px;
        grid-column: 1 / -1;
    }
    
    .playback-controls button {
        flex: 1;
    }
</style>

<div class="container">
    <!-- Linke Seite: Preview -->
    <div>
        <h2 style="color: #0f0; margin-top: 0;">📺 Vorschau (AR-Brille Ansicht)</h2>
        <div class="preview" style="background-color: {config.backgroundColor};">
            <div
                class="preview-content"
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
    </div>
    
    <!-- Rechte Seite: Steuerung -->
    <div>
        <h2 style="color: #0f0; margin-top: 0;">⚙️ Konfiguration</h2>
        <div class="controls-panel">
            <!-- Text -->
            <div class="control-group">
                <label for="text-input">📝 Text:</label>
                <textarea id="text-input" bind:value={config.text} placeholder="Gib deinen Text ein..."></textarea>
            </div>
            
            <!-- Geschwindigkeit -->
            <div class="control-group">
                <label for="speed-slider">⚡ Scrollgeschwindigkeit:</label>
                <div class="slider-container">
                    <input 
                        id="speed-slider"
                        type="range" 
                        min="5" 
                        max="150" 
                        bind:value={config.speed}
                    >
                    <span class="value-display">{config.speed.toFixed(0)} px/s</span>
                </div>
            </div>
            
            <!-- Schriftgröße -->
            <div class="control-group">
                <label for="size-slider">🔤 Schriftgröße:</label>
                <div class="slider-container">
                    <input 
                        id="size-slider"
                        type="range" 
                        min="0.5" 
                        max="5" 
                        step="0.1"
                        bind:value={config.fontSize}
                    >
                    <span class="value-display">{config.fontSize.toFixed(1)} rem</span>
                </div>
            </div>
            
            <!-- Zeilenabstand -->
            <div class="control-group">
                <label for="lineheight-slider">📏 Zeilenabstand:</label>
                <div class="slider-container">
                    <input 
                        id="lineheight-slider"
                        type="range" 
                        min="1" 
                        max="2.5" 
                        step="0.1"
                        bind:value={config.lineHeight}
                    >
                    <span class="value-display">{config.lineHeight.toFixed(1)}</span>
                </div>
            </div>
            
            <!-- Schriftart -->
            <div class="control-group">
                <label for="font-select">🔤 Schriftart:</label>
                <select id="font-select" bind:value={config.fontFamily}>
                    <option value="Courier New">Courier New (Standard)</option>
                    <option value="Arial">Arial</option>
                    <option value="Georgia">Georgia</option>
                    <option value="Verdana">Verdana</option>
                    <option value="monospace">Monospace</option>
                </select>
            </div>
            
            <!-- Textfarbe -->
            <div class="control-group">
                <label for="color-input">🎨 Textfarbe:</label>
                <input 
                    id="color-input"
                    type="color" 
                    bind:value={config.fontColor}
                >
            </div>
            
            <!-- Hintergrundfarbe -->
            <div class="control-group">
                <label for="bg-color-input">🌑 Hintergrundfarbe:</label>
                <input 
                    id="bg-color-input"
                    type="color" 
                    bind:value={config.backgroundColor}
                >
            </div>
            
            <!-- Deckkraft -->
            <div class="control-group">
                <label for="opacity-slider">👁️ Deckkraft:</label>
                <div class="slider-container">
                    <input 
                        id="opacity-slider"
                        type="range" 
                        min="0.1" 
                        max="1" 
                        step="0.1"
                        bind:value={config.opacity}
                    >
                    <span class="value-display">{(config.opacity * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <!-- Playback-Steuerung -->
            <div class="playback-controls">
                <button on:click={() => isScrolling = !isScrolling}>
                    {isScrolling ? '⏸ Pause' : '▶ Start'}
                </button>
                <button on:click={() => scrollPosition = 0}>
                    🔄 Zurücksetzen
                </button>
            </div>
            
            <!-- Status -->
            <div class="status-message">
                {statusMessage || '✓ Bereit'}
            </div>
            
            <!-- Send Button -->
            <button 
                class="send-button"
                on:click={sendToGlasses}
                disabled={isSending}
            >
                {isSending ? '📡 Wird gesendet...' : '📤 An AR-Brille senden'}
            </button>
            
            <button on:click={fetchConfig}>
                🔄 Laden
            </button>
        </div>
    </div>
</div>
