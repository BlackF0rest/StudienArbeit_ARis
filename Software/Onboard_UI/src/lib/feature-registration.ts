import { featureHost } from './feature-host';

function pingHealth(details: string) {
	return {
		ok: true,
		details,
		updatedAt: new Date().toISOString()
	};
}

let bootstrapped = false;

export function bootstrapFeatureHost(): void {
	if (bootstrapped) return;
	bootstrapped = true;

	featureHost.register({
		metadata: {
			id: 'basic-hud',
			name: 'Basic HUD',
			description: 'Status, battery, climate and connectivity',
			version: '0.1.0',
			permissions: ['sensors.read', 'clock.read', 'network.read'],
			dependencies: ['backend-service'],
			enabledByDefault: true
		},
		healthCheck: async () => pingHealth('hud render loop ready')
	});

	featureHost.register({
		metadata: {
			id: 'teleprompter-runtime',
			name: 'Teleprompter Runtime',
			description: 'Polling with cache and fallback strategy',
			version: '0.1.0',
			permissions: ['network.read', 'storage.read', 'storage.write'],
			dependencies: ['backend-service'],
			enabledByDefault: true
		},
		healthCheck: async () => pingHealth('poller active')
	});

	featureHost.register({
		metadata: {
			id: 'navigation-mvp',
			name: 'Navigation MVP',
			description: 'Route text + heading indicator + next action',
			version: '0.1.0',
			permissions: ['sensors.read', 'network.read'],
			dependencies: ['telemetry-core'],
			enabledByDefault: true
		},
		healthCheck: async () => pingHealth('mock provider ready, api hook prepared')
	});

	featureHost.register({
		metadata: {
			id: 'ai-chat-scaffold',
			name: 'AI Chat Scaffold',
			description: 'UI shell + local history + provider abstraction',
			version: '0.1.0',
			permissions: ['network.read', 'network.write', 'storage.read', 'storage.write'],
			dependencies: ['backend-service'],
			enabledByDefault: false
		},
		healthCheck: async () => pingHealth('chat shell mounted')
	});
}
