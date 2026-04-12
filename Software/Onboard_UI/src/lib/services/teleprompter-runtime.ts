export interface TeleprompterConfig {
	text: string;
	speed: number;
	fontSize: number;
	fontColor: string;
	backgroundColor: string;
	fontFamily: string;
	lineHeight: number;
	opacity: number;
}

interface CacheEnvelope {
	config: TeleprompterConfig;
	updatedAt: string;
}

const CACHE_KEY = 'aris.teleprompter.cache';

export const defaultTeleprompterConfig: TeleprompterConfig = {
	text: 'Warte auf Signal...',
	speed: 30,
	fontSize: 2,
	fontColor: '#0f0',
	backgroundColor: '#000',
	fontFamily: 'Courier New',
	lineHeight: 1.5,
	opacity: 1
};

function readCache(): CacheEnvelope | null {
	if (typeof localStorage === 'undefined') return null;
	const raw = localStorage.getItem(CACHE_KEY);
	if (!raw) return null;
	try {
		return JSON.parse(raw) as CacheEnvelope;
	} catch {
		return null;
	}
}

function writeCache(config: TeleprompterConfig): void {
	if (typeof localStorage === 'undefined') return;
	const payload: CacheEnvelope = { config, updatedAt: new Date().toISOString() };
	localStorage.setItem(CACHE_KEY, JSON.stringify(payload));
}

export class TeleprompterRuntime {
	private pollIntervalMs = 1000;
	private backoffSteps = 0;
	private timer: ReturnType<typeof setTimeout> | null = null;
	private onConfig: (config: TeleprompterConfig) => void;
	private onState: (state: string) => void;

	constructor(onConfig: (config: TeleprompterConfig) => void, onState: (state: string) => void) {
		this.onConfig = onConfig;
		this.onState = onState;
	}

	start(): void {
		const cached = readCache();
		if (cached?.config) {
			this.onConfig(cached.config);
			this.onState('cached');
		}
		void this.tick();
	}

	stop(): void {
		if (this.timer) clearTimeout(this.timer);
		this.timer = null;
	}

	private schedule(): void {
		if (this.timer) clearTimeout(this.timer);
		const effective = Math.min(this.pollIntervalMs * 2 ** this.backoffSteps, 8000);
		this.timer = setTimeout(() => void this.tick(), effective);
	}

	private async tick(): Promise<void> {
		try {
			const response = await fetch('http://localhost:5000/api/teleprompter/current');
			if (!response.ok) throw new Error(`teleprompter returned ${response.status}`);
			const config = (await response.json()) as TeleprompterConfig;
			this.onConfig({ ...defaultTeleprompterConfig, ...config });
			writeCache({ ...defaultTeleprompterConfig, ...config });
			this.backoffSteps = 0;
			this.onState('live');
		} catch {
			this.backoffSteps += 1;
			const cached = readCache();
			if (cached?.config) {
				this.onConfig(cached.config);
				this.onState('fallback-cache');
			} else {
				this.onConfig(defaultTeleprompterConfig);
				this.onState('fallback-default');
			}
		}

		this.schedule();
	}
}
