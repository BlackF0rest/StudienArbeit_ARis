export interface HudStatus {
	battery: number | null;
	temperature: number | null;
	humidity: number | null;
	connection: 'connected' | 'degraded' | 'offline';
	lastUpdated: string;
}

const FALLBACK_STATUS: HudStatus = {
	battery: null,
	temperature: null,
	humidity: null,
	connection: 'offline',
	lastUpdated: new Date(0).toISOString()
};

function pickNumber(value: unknown): number | null {
	if (typeof value === 'number' && Number.isFinite(value)) return value;
	if (typeof value === 'string') {
		const parsed = Number(value);
		if (Number.isFinite(parsed)) return parsed;
	}
	return null;
}

export async function fetchHudStatus(): Promise<HudStatus> {
	try {
		const response = await fetch('http://localhost:5000/api/mainInfo');
		if (!response.ok) throw new Error(`mainInfo returned ${response.status}`);
		const data = (await response.json()) as Record<string, unknown>;

		return {
			battery: pickNumber(data.Battery),
			temperature: pickNumber(data.Temperature),
			humidity: pickNumber(data.Humidity),
			connection: 'connected',
			lastUpdated: new Date().toISOString()
		};
	} catch {
		return {
			...FALLBACK_STATUS,
			lastUpdated: new Date().toISOString()
		};
	}
}
