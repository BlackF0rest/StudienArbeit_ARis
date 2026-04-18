export interface ButtonDiagnostics {
	pin: number;
	state: 'pressed' | 'released' | 'unknown';
	lastEventAt: string | null;
}

export interface Mpu6050Diagnostics {
	sdaPin: number;
	sclPin: number;
	gyro: {
		x: number | null;
		y: number | null;
		z: number | null;
	};
	accel: {
		x: number | null;
		y: number | null;
		z: number | null;
	};
}

export interface Gy63Diagnostics {
	sdaPin: number;
	sclPin: number;
	pressureHpa: number | null;
	altitudeM: number | null;
}

export interface SensorDiagnostics {
	connection: 'connected' | 'offline';
	button: ButtonDiagnostics;
	mpu6050: Mpu6050Diagnostics;
	gy63: Gy63Diagnostics;
	lastUpdated: string;
}

const FALLBACK_SENSOR_DIAGNOSTICS: SensorDiagnostics = {
	connection: 'offline',
	button: {
		pin: 40,
		state: 'unknown',
		lastEventAt: null
	},
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

function pickNumber(value: unknown): number | null {
	if (typeof value === 'number' && Number.isFinite(value)) return value;
	if (typeof value === 'string') {
		const parsed = Number(value);
		if (Number.isFinite(parsed)) return parsed;
	}
	return null;
}

function pickRecord(value: unknown): Record<string, unknown> {
	if (value && typeof value === 'object') return value as Record<string, unknown>;
	return {};
}

function pickState(value: unknown): ButtonDiagnostics['state'] {
	if (value === 'pressed' || value === 'released') return value;
	if (typeof value === 'boolean') return value ? 'pressed' : 'released';
	return 'unknown';
}

export async function fetchSensorDiagnostics(): Promise<SensorDiagnostics> {
	try {
		const response = await fetch('http://localhost:5000/api/sensors');
		if (!response.ok) throw new Error(`sensor diagnostics returned ${response.status}`);
		const responseBody = (await response.json()) as Record<string, unknown>;

		const data = pickRecord(responseBody.data ?? responseBody.sensors ?? responseBody);
		const button = pickRecord(data.button);
		const mpu6050 = pickRecord(data.mpu6050 ?? data.mpu_6050 ?? data.imu);
		const gy63 = pickRecord(data.gy63 ?? data.gy_63 ?? data.barometer);
		const gyro = pickRecord(mpu6050.gyro);
		const accel = pickRecord(mpu6050.accel ?? mpu6050.accelerometer);

		return {
			connection: 'connected',
			button: {
				pin: pickNumber(button.pin) ?? 40,
				state: pickState(button.state ?? button.pressed),
				lastEventAt: typeof button.lastEventAt === 'string' ? button.lastEventAt : typeof button.last_event_at === 'string' ? button.last_event_at : null
			},
			mpu6050: {
				sdaPin: pickNumber(mpu6050.sdaPin ?? mpu6050.sda_pin) ?? 3,
				sclPin: pickNumber(mpu6050.sclPin ?? mpu6050.scl_pin) ?? 5,
				gyro: {
					x: pickNumber(gyro.x),
					y: pickNumber(gyro.y),
					z: pickNumber(gyro.z)
				},
				accel: {
					x: pickNumber(accel.x),
					y: pickNumber(accel.y),
					z: pickNumber(accel.z)
				}
			},
			gy63: {
				sdaPin: pickNumber(gy63.sdaPin ?? gy63.sda_pin) ?? 3,
				sclPin: pickNumber(gy63.sclPin ?? gy63.scl_pin) ?? 5,
				pressureHpa: pickNumber(gy63.pressureHpa ?? gy63.pressure_hpa ?? gy63.pressure),
				altitudeM: pickNumber(gy63.altitudeM ?? gy63.altitude_m ?? gy63.altitude)
			},
			lastUpdated: new Date().toISOString()
		};
	} catch {
		return {
			...FALLBACK_SENSOR_DIAGNOSTICS,
			lastUpdated: new Date().toISOString()
		};
	}
}
