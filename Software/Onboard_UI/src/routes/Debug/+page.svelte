<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '../header.svelte';
	import { bootstrapFeatureHost } from '$lib/feature-registration';
	import { featureHost, type FeatureRuntimeSnapshot } from '$lib/feature-host';
	import { fetchPcLinkDiagnostics, type PcLinkDiagnostics } from '$lib/services/pc-link-diagnostics';
	import { fetchSensorDiagnostics, type SensorDiagnostics } from '$lib/services/sensor-diagnostics';
	import { getHintForContext, registerAppActions, setInputContext, type InputHint } from '$lib/input-controller';
	import InputHintOverlay from '$lib/components/InputHintOverlay.svelte';
	import HudCard from '$lib/components/hud/HudCard.svelte';
	import HudScaffold from '$lib/components/hud/HudScaffold.svelte';
	import StatusPill from '$lib/components/hud/StatusPill.svelte';

	let hint: InputHint = getHintForContext('debug');
	let snapshot: FeatureRuntimeSnapshot = {
		registered: [],
		health: {},
		telemetry: []
	};

	let pcDiagnostics: PcLinkDiagnostics = {
		pc_link: { active: false, sessions: [] },
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
	let sensorDiagnostics: SensorDiagnostics = {
		connection: 'offline',
		button: { pin: 40, state: 'unknown', lastEventAt: null },
		mpu6050: {
			sdaPin: 3,
			sclPin: 5,
			gyro: { x: null, y: null, z: null },
			accel: { x: null, y: null, z: null }
		},
		gy63: {
			sdaPin: 3,
			sclPin: 5,
			pressureHpa: null,
			altitudeM: null
		},
		lastUpdated: new Date(0).toISOString()
	};

	function hasNumericSensorValues(data: SensorDiagnostics): boolean {
		return (
			data.mpu6050.gyro.x !== null ||
			data.mpu6050.gyro.y !== null ||
			data.mpu6050.gyro.z !== null ||
			data.mpu6050.accel.x !== null ||
			data.mpu6050.accel.y !== null ||
			data.mpu6050.accel.z !== null ||
			data.gy63.pressureHpa !== null ||
			data.gy63.altitudeM !== null
		);
	}

	async function refreshSnapshot(): Promise<void> {
		snapshot = await featureHost.snapshot();
		pcDiagnostics = await fetchPcLinkDiagnostics();
		sensorDiagnostics = await fetchSensorDiagnostics();
	}

	onMount(() => {
		bootstrapFeatureHost();
		setInputContext('debug');
		const unregister = registerAppActions({
			onSingle: () => {
				void refreshSnapshot();
			},
			onDouble: () => {
				featureHost.emit('basic-hud', 'debug.return_home', { reason: 'double-tap' });
			}
		});
		void refreshSnapshot();
		const timer = setInterval(() => void refreshSnapshot(), 3000);
		return () => {
			unregister();
			clearInterval(timer);
		};
	});
</script>

<Header />

<HudScaffold title="Debug Diagnostics" subtitle="Telemetry and integration diagnostics">
	<svelte:fragment slot="header">
		<StatusPill text={pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'} tone={pcDiagnostics.pc_link.active ? 'ok' : 'warn'} />
	</svelte:fragment>

	<HudCard title="Telemetry (latest)">
		{#if snapshot.telemetry.length === 0}
			<p>No telemetry yet.</p>
		{:else}
			{#each snapshot.telemetry.slice(0, 12) as event}
				<p>{event.createdAt} · {event.featureId} · {event.type}</p>
			{/each}
		{/if}
	</HudCard>

	<HudCard title="PC Link Diagnostics">
		<p class="hud-primary-point">{pcDiagnostics.pc_link.active ? 'PC Link Connected' : 'PC Link Offline'}</p>
		<p class="hud-secondary-line">Stream {pcDiagnostics.stream_metrics.connected ? 'connected' : 'disconnected'} ({pcDiagnostics.stream_metrics.quality})</p>
		<p><strong>Reconnects:</strong> {pcDiagnostics.stream_metrics.reconnect_attempts} · <strong>Bandwidth:</strong> {pcDiagnostics.stream_metrics.avg_bandwidth_mbps ?? 'n/a'} Mbps · <strong>Frame Drop:</strong> {pcDiagnostics.stream_metrics.avg_frame_drop_ratio ?? 'n/a'}</p>
		<p><strong>Display Mode:</strong> {pcDiagnostics.stream_metrics.onboard_only_mode ? 'Onboard-only fallback' : 'Hybrid streaming'}</p>
		<p><strong>Overlay Contract:</strong> v{pcDiagnostics.overlay_contract.contract_version} · {pcDiagnostics.overlay_contract.coordinate_space} · {pcDiagnostics.overlay_contract.z_order.join(' → ')}</p>
	</HudCard>

	<HudCard title="Onboard Sensors">
		<p class="hud-primary-point">{sensorDiagnostics.connection === 'connected' ? 'Sensors online' : 'Sensor data offline (fallback)'}</p>
		<p class="hud-secondary-line">{hasNumericSensorValues(sensorDiagnostics) ? 'Live numeric values received' : 'No live numeric values yet'}</p>
		<p class="hud-muted"><strong>Updated:</strong> {sensorDiagnostics.lastUpdated}</p>
		<p>
			<strong>Button (Pin {sensorDiagnostics.button.pin}):</strong>
			{sensorDiagnostics.button.state}
			· <strong>Last event:</strong> {sensorDiagnostics.button.lastEventAt ?? 'n/a'}
		</p>
		<p>
			<strong>MPU-6050 (SDA {sensorDiagnostics.mpu6050.sdaPin}, SCL {sensorDiagnostics.mpu6050.sclPin}):</strong>
			Gyro (dps) x/y/z {sensorDiagnostics.mpu6050.gyro.x ?? 'n/a'} / {sensorDiagnostics.mpu6050.gyro.y ?? 'n/a'} / {sensorDiagnostics.mpu6050.gyro.z ?? 'n/a'}
			· Accel (g) x/y/z {sensorDiagnostics.mpu6050.accel.x ?? 'n/a'} / {sensorDiagnostics.mpu6050.accel.y ?? 'n/a'} / {sensorDiagnostics.mpu6050.accel.z ?? 'n/a'}
		</p>
		<p>
			<strong>GY-63 (SDA {sensorDiagnostics.gy63.sdaPin}, SCL {sensorDiagnostics.gy63.sclPin}):</strong>
			Druck {sensorDiagnostics.gy63.pressureHpa ?? 'n/a'} hPa
			· Höhe {sensorDiagnostics.gy63.altitudeM ?? 'n/a'} m
		</p>
	</HudCard>

	<svelte:fragment slot="hint">
		<InputHintOverlay {hint} />
	</svelte:fragment>
</HudScaffold>
