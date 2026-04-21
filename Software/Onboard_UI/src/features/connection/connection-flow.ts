import { writable, type Readable } from 'svelte/store';

export type ConnectionState =
	| 'idle'
	| 'discovering'
	| 'connecting'
	| 'connected'
	| 'degraded'
	| 'disconnected';

export interface DeviceMetadata {
	device_id: string;
	friendly_name: string;
	firmware_version: string;
	app_version: string;
	capabilities: string[];
}

export interface DeviceProfile {
	base_url: string;
	metadata: DeviceMetadata;
	last_seen_at: string;
}

export interface ConnectionSnapshot {
	state: ConnectionState;
	target_url: string | null;
	device: DeviceMetadata | null;
	message: string | null;
	updated_at: string;
}

interface StatusHandshakeData {
	health: string;
	version: string;
	hardware_ready?: { ok?: boolean };
	handshake?: {
		protocol: 'status-handshake-v1';
		device: DeviceMetadata;
	};
}

interface StatusResponse {
	ok: boolean;
	data: StatusHandshakeData;
	timestamp: string;
	trace_id: string;
}

interface JsonStorage {
	getItem(key: string): string | null;
	setItem(key: string, value: string): void;
}

export interface DiscoveryCandidate {
	base_url: string;
	source: 'mdns' | 'bonjour';
}

export interface ConnectionFlowOptions {
	fetchImpl?: typeof fetch;
	discoverDevices?: () => Promise<DiscoveryCandidate[]>;
	storage?: JsonStorage;
}

const PROFILE_STORAGE_KEY = 'onboard.connection.successful-profiles.v1';

export class ConnectionFlow {
	private readonly fetchImpl: typeof fetch;
	private readonly discoverDevices?: () => Promise<DiscoveryCandidate[]>;
	private readonly storage: JsonStorage | null;
	private readonly stateStore = writable<ConnectionSnapshot>(this.makeSnapshot('idle'));

	constructor(options: ConnectionFlowOptions = {}) {
		this.fetchImpl = options.fetchImpl ?? fetch;
		this.discoverDevices = options.discoverDevices;
		this.storage = options.storage ?? (typeof localStorage !== 'undefined' ? localStorage : null);
	}

	public get state(): Readable<ConnectionSnapshot> {
		return this.stateStore;
	}

	public async discover(): Promise<DiscoveryCandidate[]> {
		this.setState('discovering', { message: 'Searching devices on LAN…' });

		if (!this.discoverDevices) {
			this.setState('idle', { message: 'LAN discovery unavailable. Enter device IP manually.' });
			return [];
		}

		const devices = await this.discoverDevices();
		this.setState('idle', {
			message:
				devices.length > 0
					? `Found ${devices.length} device(s). You can still enter an IP manually.`
					: 'No device discovered. Manual IP entry is required fallback.'
		});
		return devices;
	}

	public async connect(input: { manualIp?: string; discoveredUrl?: string }): Promise<DeviceProfile> {
		const target = input.manualIp ? normalizeBaseUrl(input.manualIp) : input.discoveredUrl;
		if (!target) {
			this.setState('disconnected', { message: 'Manual IP entry is required when discovery is unavailable.' });
			throw new Error('No connection target provided. Manual IP fallback is mandatory.');
		}

		this.setState('connecting', { targetUrl: target, message: 'Performing status handshake…' });

		const response = await this.fetchImpl(buildStatusUrl(target), {
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'X-Handshake-Protocol': 'status-handshake-v1'
			}
		});

		if (!response.ok) {
			this.setState('disconnected', {
				targetUrl: target,
				message: `Status handshake failed (${response.status}).`
			});
			throw new Error(`Status handshake failed with HTTP ${response.status}`);
		}

		const payload = (await response.json()) as StatusResponse;
		const metadata = payload.data?.handshake?.device;
		if (!payload.ok || !metadata) {
			this.setState('disconnected', {
				targetUrl: target,
				message: 'Handshake payload missing device metadata.'
			});
			throw new Error('Invalid status handshake payload: missing handshake.device metadata');
		}

		const successfulProfile: DeviceProfile = {
			base_url: target,
			metadata,
			last_seen_at: payload.timestamp
		};
		this.saveSuccessfulProfile(successfulProfile);

		const isDegraded = payload.data.health !== 'ok' || payload.data.hardware_ready?.ok === false;
		this.setState(isDegraded ? 'degraded' : 'connected', {
			targetUrl: target,
			device: metadata,
			message: isDegraded ? 'Connected with degraded hardware readiness.' : 'Connected.'
		});

		return successfulProfile;
	}

	public async reconnectLastSuccessful(): Promise<DeviceProfile | null> {
		const [latest] = this.getSavedProfiles();
		if (!latest) {
			this.setState('idle', { message: 'No successful device profile saved yet.' });
			return null;
		}
		return this.connect({ discoveredUrl: latest.base_url });
	}

	public disconnect(message = 'Disconnected by user.'): void {
		this.setState('disconnected', { message, targetUrl: null, device: null });
	}

	public getSavedProfiles(): DeviceProfile[] {
		if (!this.storage) return [];
		const raw = this.storage.getItem(PROFILE_STORAGE_KEY);
		if (!raw) return [];
		try {
			const parsed = JSON.parse(raw) as DeviceProfile[];
			return Array.isArray(parsed)
				? parsed.sort((a, b) => Date.parse(b.last_seen_at) - Date.parse(a.last_seen_at))
				: [];
		} catch {
			return [];
		}
	}

	private saveSuccessfulProfile(profile: DeviceProfile): void {
		if (!this.storage) return;

		const deduped = [profile, ...this.getSavedProfiles().filter((item) => item.base_url !== profile.base_url)];
		this.storage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(deduped.slice(0, 10)));
	}

	private setState(state: ConnectionState, updates: Partial<Omit<ConnectionSnapshot, 'state' | 'updated_at'>>): void {
		this.stateStore.set({
			...this.makeSnapshot(state),
			...updates,
			state,
			updated_at: new Date().toISOString()
		});
	}

	private makeSnapshot(state: ConnectionState): ConnectionSnapshot {
		return {
			state,
			target_url: null,
			device: null,
			message: null,
			updated_at: new Date().toISOString()
		};
	}
}

function buildStatusUrl(baseUrl: string): string {
	const normalized = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
	return `${normalized}/api/status`;
}

function normalizeBaseUrl(manualIp: string): string {
	const trimmed = manualIp.trim();
	if (!trimmed) {
		throw new Error('Manual IP cannot be empty.');
	}

	if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
		return trimmed;
	}

	return `http://${trimmed}`;
}
