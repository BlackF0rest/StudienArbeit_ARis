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
		const direct = Number(value);
		if (Number.isFinite(direct)) return direct;

		const match = value.match(/-?\d+(\.\d+)?/);
		if (!match) return null;
		const parsed = Number(match[0]);
		if (Number.isFinite(parsed)) return parsed;
	}
	return null;
}

export async function fetchHudStatus(): Promise<HudStatus> {
	try {
		const response = await fetch('http://localhost:5000/api/mainInfo');
		if (!response.ok) throw new Error(`mainInfo returned ${response.status}`);
		const responseBody = (await response.json()) as { data?: Record<string, unknown> } & Record<
			string,
			unknown
		>;
		const data = (responseBody.data as Record<string, unknown> | undefined) ?? responseBody;

		return {
			battery: pickNumber(data.battery_percent ?? data.Battery),
			temperature: pickNumber(data.temperature_c ?? data.Temperature),
			humidity: pickNumber(data.humidity_percent ?? data.Humidity),
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
