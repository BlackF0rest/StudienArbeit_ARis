export type FeaturePermission =
	| 'sensors.read'
	| 'network.read'
	| 'network.write'
	| 'storage.read'
	| 'storage.write'
	| 'clock.read';

export interface FeatureMetadata {
	id: string;
	name: string;
	description: string;
	version: string;
	permissions: FeaturePermission[];
	dependencies: string[];
	enabledByDefault?: boolean;
}

export interface HealthReport {
	ok: boolean;
	details: string;
	updatedAt: string;
}

export interface TelemetryEvent {
	featureId: string;
	type: string;
	payload: Record<string, unknown>;
	createdAt: string;
}

export interface FeatureModule {
	metadata: FeatureMetadata;
	healthCheck: () => Promise<HealthReport>;
	onTelemetry?: (event: TelemetryEvent) => void;
}

export interface FeatureRuntimeSnapshot {
	registered: FeatureMetadata[];
	health: Record<string, HealthReport>;
	telemetry: TelemetryEvent[];
}

export class FeatureHost {
	private readonly modules = new Map<string, FeatureModule>();
	private readonly telemetryBuffer: TelemetryEvent[] = [];

	register(module: FeatureModule): void {
		if (this.modules.has(module.metadata.id)) {
			throw new Error(`Feature \"${module.metadata.id}\" is already registered.`);
		}

		this.modules.set(module.metadata.id, module);
	}

	list(): FeatureMetadata[] {
		return [...this.modules.values()].map((module) => module.metadata);
	}

	async runHealthChecks(): Promise<Record<string, HealthReport>> {
		const health: Record<string, HealthReport> = {};

		for (const module of this.modules.values()) {
			try {
				health[module.metadata.id] = await module.healthCheck();
			} catch (error) {
				health[module.metadata.id] = {
					ok: false,
					details: error instanceof Error ? error.message : 'health check failed',
					updatedAt: new Date().toISOString()
				};
			}
		}

		return health;
	}

	emit(featureId: string, type: string, payload: Record<string, unknown>): void {
		const event: TelemetryEvent = {
			featureId,
			type,
			payload,
			createdAt: new Date().toISOString()
		};

		this.telemetryBuffer.unshift(event);
		this.telemetryBuffer.splice(40);

		const module = this.modules.get(featureId);
		module?.onTelemetry?.(event);
	}

	async snapshot(): Promise<FeatureRuntimeSnapshot> {
		return {
			registered: this.list(),
			health: await this.runHealthChecks(),
			telemetry: [...this.telemetryBuffer]
		};
	}
}

export const featureHost = new FeatureHost();
