export interface NavigationSnapshot {
	routeText: string;
	headingDeg: number;
	nextAction: string;
	source: 'mock' | 'provider';
	updatedAt: string;
}

export interface NavigationProvider {
	name: string;
	getLatest: () => Promise<NavigationSnapshot>;
}

export class MockNavigationProvider implements NavigationProvider {
	name = 'mock';
	private step = 0;

	async getLatest(): Promise<NavigationSnapshot> {
		this.step = (this.step + 1) % 4;
		const demos = [
			{ routeText: 'Campus Nord → Werkstatt', headingDeg: 35, nextAction: 'In 120m rechts halten' },
			{ routeText: 'Werkstatt → Haupttor', headingDeg: 90, nextAction: 'Geradeaus für 300m' },
			{ routeText: 'Haupttor → Parkplatz B', headingDeg: 180, nextAction: 'Am Kreisverkehr Ausfahrt 2' },
			{ routeText: 'Parkplatz B → Ladepunkt', headingDeg: 250, nextAction: 'In 30m links zum Ladepunkt' }
		][this.step];

		return {
			...demos,
			source: 'mock',
			updatedAt: new Date().toISOString()
		};
	}
}

export class ApiNavigationProvider implements NavigationProvider {
	name = 'api';

	async getLatest(): Promise<NavigationSnapshot> {
		const response = await fetch('http://localhost:5000/api/navigation/current');
		if (!response.ok) {
			throw new Error(`navigation returned ${response.status}`);
		}
		const payload = (await response.json()) as Partial<NavigationSnapshot>;
		return {
			routeText: payload.routeText ?? 'Keine Route',
			headingDeg: payload.headingDeg ?? 0,
			nextAction: payload.nextAction ?? 'Warte auf Navigationsdaten',
			source: 'provider',
			updatedAt: new Date().toISOString()
		};
	}
}

export function buildNavigationProvider(enableRealProvider = false): NavigationProvider {
	if (enableRealProvider) return new ApiNavigationProvider();
	return new MockNavigationProvider();
}
