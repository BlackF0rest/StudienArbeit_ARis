export interface PcLinkSession {
	session_id: string;
	pc_id: string;
	connected_at: string;
	last_seen_at: string;
}

export interface PcLinkDiagnostics {
	pc_link: {
		active: boolean;
		sessions: PcLinkSession[];
	};
	stream_metrics: {
		connected: boolean;
		reconnect_attempts: number;
		quality: 'ultra' | 'high' | 'medium' | 'low';
		avg_bandwidth_mbps: number | null;
		avg_frame_drop_ratio: number | null;
		onboard_only_mode: boolean;
		last_updated: string;
	};
	overlay_contract: {
		contract_version: string;
		coordinate_space: string;
		safe_area: Record<string, number>;
		z_order: string[];
		last_synced_at: string;
	};
}

const FALLBACK_DIAGNOSTICS: PcLinkDiagnostics = {
	pc_link: {
		active: false,
		sessions: []
	},
	stream_metrics: {
		connected: false,
		reconnect_attempts: 0,
		quality: 'medium',
		avg_bandwidth_mbps: null,
		avg_frame_drop_ratio: null,
		onboard_only_mode: false,
		last_updated: new Date(0).toISOString()
	},
	overlay_contract: {
		contract_version: '1.0',
		coordinate_space: 'normalized',
		safe_area: { x: 0, y: 0, width: 1, height: 1 },
		z_order: ['streamed-scene', 'streamed-overlay', 'onboard-hud'],
		last_synced_at: new Date(0).toISOString()
	}
};

export async function fetchPcLinkDiagnostics(): Promise<PcLinkDiagnostics> {
	try {
		const response = await fetch('http://localhost:5000/api/debug/diagnostics');
		if (!response.ok) throw new Error(`diagnostics returned ${response.status}`);
		const payload = (await response.json()) as {
			panels?: { pc_link?: PcLinkDiagnostics };
		};
		if (payload.panels?.pc_link) {
			return payload.panels.pc_link;
		}
	} catch {
		// Use fallback when debug endpoint is unavailable.
	}

	return {
		...FALLBACK_DIAGNOSTICS,
		stream_metrics: {
			...FALLBACK_DIAGNOSTICS.stream_metrics,
			last_updated: new Date().toISOString()
		}
	};
}
