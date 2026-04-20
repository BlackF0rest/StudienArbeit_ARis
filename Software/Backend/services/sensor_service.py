from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hardware.pinmap import (
    BUTTON_PIN,
    DEVICE_I2C_ASSIGNMENTS,
    GY63_ADDRESS,
    I2C_BUS_ID,
    I2C_SCL_PIN,
    I2C_SDA_PIN,
    MPU6050_ADDRESS,
    PINMAP_RESPONSE,
)

try:
    import RPi.GPIO as GPIO
except Exception:  # noqa: BLE001
    GPIO = None

try:
    from smbus2 import SMBus
except Exception:  # noqa: BLE001
    SMBus = None


SEA_LEVEL_PRESSURE_PA = 101325.0


@dataclass
class _ButtonState:
    stable_value: int
    raw_value: int
    last_raw_change: float
    last_stable_change: float


class SensorService:
    def __init__(self, debounce_ms: int = 50):
        self.source = "raspi-gpio-i2c"
        self._debounce_s = debounce_ms / 1000.0

        self._gpio_ready = False
        self._gpio_error: str | None = None

        self._i2c_lock = threading.Lock()
        self._i2c_bus: SMBus | None = None
        self._i2c_error: str | None = None

        self._button_state: _ButtonState | None = None
        self._button_transitions = 0
        self._last_button_event: dict[str, Any] | None = None

        self._gy63_calibration: dict[str, int] | None = None

        self._init_gpio()
        self._init_i2c()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_gpio(self) -> None:
        if GPIO is None:
            self._gpio_error = "RPi.GPIO is not installed"
            return

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            initial = int(GPIO.input(BUTTON_PIN))
            now = time.monotonic()
            self._button_state = _ButtonState(
                stable_value=initial,
                raw_value=initial,
                last_raw_change=now,
                last_stable_change=now,
            )
            self._gpio_ready = True
        except Exception as exc:  # noqa: BLE001
            self._gpio_error = f"GPIO init failed: {exc}"

    def _init_i2c(self) -> None:
        if SMBus is None:
            self._i2c_error = "smbus2 is not installed"
            return

        try:
            self._i2c_bus = SMBus(I2C_BUS_ID)
            self._wake_mpu6050()
            self._load_gy63_calibration()
        except Exception as exc:  # noqa: BLE001
            self._i2c_error = f"I2C init failed: {exc}"

    def _wake_mpu6050(self) -> None:
        if self._i2c_bus is None:
            return
        with self._i2c_lock:
            self._i2c_bus.write_byte_data(MPU6050_ADDRESS, 0x6B, 0x00)

    def _read_u16(self, address: int, register: int) -> int:
        if self._i2c_bus is None:
            raise RuntimeError("I2C bus not ready")
        msb = self._i2c_bus.read_byte_data(address, register)
        lsb = self._i2c_bus.read_byte_data(address, register + 1)
        return (msb << 8) | lsb

    def _read_s16(self, address: int, register: int) -> int:
        value = self._read_u16(address, register)
        return value - 65536 if value > 32767 else value

    def _load_gy63_calibration(self) -> None:
        if self._i2c_bus is None:
            return

        with self._i2c_lock:
            calib = {
                "ac1": self._read_s16(GY63_ADDRESS, 0xAA),
                "ac2": self._read_s16(GY63_ADDRESS, 0xAC),
                "ac3": self._read_s16(GY63_ADDRESS, 0xAE),
                "ac4": self._read_u16(GY63_ADDRESS, 0xB0),
                "ac5": self._read_u16(GY63_ADDRESS, 0xB2),
                "ac6": self._read_u16(GY63_ADDRESS, 0xB4),
                "b1": self._read_s16(GY63_ADDRESS, 0xB6),
                "b2": self._read_s16(GY63_ADDRESS, 0xB8),
                "mb": self._read_s16(GY63_ADDRESS, 0xBA),
                "mc": self._read_s16(GY63_ADDRESS, 0xBC),
                "md": self._read_s16(GY63_ADDRESS, 0xBE),
            }
            self._gy63_calibration = calib

    def _read_button(self) -> dict[str, Any]:
        now_iso = self._utc_now()
        if not self._gpio_ready or self._button_state is None:
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": self._gpio_error or "GPIO unavailable",
                "pin": BUTTON_PIN,
            }

        try:
            raw = int(GPIO.input(BUTTON_PIN))
        except Exception as exc:  # noqa: BLE001
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": f"GPIO read failed: {exc}",
                "pin": BUTTON_PIN,
            }

        now_mono = time.monotonic()
        state = self._button_state

        if raw != state.raw_value:
            state.raw_value = raw
            state.last_raw_change = now_mono

        if raw != state.stable_value and (now_mono - state.last_raw_change) >= self._debounce_s:
            previous = state.stable_value
            state.stable_value = raw
            state.last_stable_change = now_mono
            self._button_transitions += 1
            self._last_button_event = {
                "from": previous,
                "to": raw,
                "edge": "falling" if raw == 0 else "rising",
                "timestamp": now_iso,
            }

        return {
            "source": self.source,
            "updated_at": now_iso,
            "ok": True,
            "pin": BUTTON_PIN,
            "state": state.stable_value,
            "state_label": "pressed" if state.stable_value == 0 else "released",
            "raw_state": state.raw_value,
            "debounce_ms": int(self._debounce_s * 1000),
            "transition_count": self._button_transitions,
            "last_event": self._last_button_event,
            "last_event_at": self._last_button_event["timestamp"] if self._last_button_event else None,
        }

    def _read_mpu6050(self) -> dict[str, Any]:
        now_iso = self._utc_now()
        if self._i2c_bus is None:
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": self._i2c_error or "I2C unavailable",
                "address": MPU6050_ADDRESS,
            }

        try:
            with self._i2c_lock:
                accel_x = self._read_s16(MPU6050_ADDRESS, 0x3B)
                accel_y = self._read_s16(MPU6050_ADDRESS, 0x3D)
                accel_z = self._read_s16(MPU6050_ADDRESS, 0x3F)

                gyro_x = self._read_s16(MPU6050_ADDRESS, 0x43)
                gyro_y = self._read_s16(MPU6050_ADDRESS, 0x45)
                gyro_z = self._read_s16(MPU6050_ADDRESS, 0x47)
        except Exception as exc:  # noqa: BLE001
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": f"MPU6050 read failed: {exc}",
                "address": MPU6050_ADDRESS,
            }

        return {
            "source": self.source,
            "updated_at": now_iso,
            "ok": True,
            "address": MPU6050_ADDRESS,
            "accelerometer_g": {
                "x": round(accel_x / 16384.0, 5),
                "y": round(accel_y / 16384.0, 5),
                "z": round(accel_z / 16384.0, 5),
            },
            "gyroscope_dps": {
                "x": round(gyro_x / 131.0, 5),
                "y": round(gyro_y / 131.0, 5),
                "z": round(gyro_z / 131.0, 5),
            },
            "accel": {
                "x": round(accel_x / 16384.0, 5),
                "y": round(accel_y / 16384.0, 5),
                "z": round(accel_z / 16384.0, 5),
            },
            "gyro": {
                "x": round(gyro_x / 131.0, 5),
                "y": round(gyro_y / 131.0, 5),
                "z": round(gyro_z / 131.0, 5),
            },
        }

    def _read_gy63(self) -> dict[str, Any]:
        now_iso = self._utc_now()
        if self._i2c_bus is None:
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": self._i2c_error or "I2C unavailable",
                "address": GY63_ADDRESS,
            }

        if self._gy63_calibration is None:
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": "GY-63 calibration unavailable",
                "address": GY63_ADDRESS,
            }

        calib = self._gy63_calibration

        try:
            with self._i2c_lock:
                self._i2c_bus.write_byte_data(GY63_ADDRESS, 0xF4, 0x2E)
                time.sleep(0.005)
                ut = self._read_u16(GY63_ADDRESS, 0xF6)

                self._i2c_bus.write_byte_data(GY63_ADDRESS, 0xF4, 0x34)
                time.sleep(0.008)
                msb = self._i2c_bus.read_byte_data(GY63_ADDRESS, 0xF6)
                lsb = self._i2c_bus.read_byte_data(GY63_ADDRESS, 0xF7)
                xlsb = self._i2c_bus.read_byte_data(GY63_ADDRESS, 0xF8)
                up = ((msb << 16) + (lsb << 8) + xlsb) >> 8

            x1 = ((ut - calib["ac6"]) * calib["ac5"]) >> 15
            x2 = (calib["mc"] << 11) // (x1 + calib["md"])
            b5 = x1 + x2
            temp_c = ((b5 + 8) >> 4) / 10.0

            b6 = b5 - 4000
            x1 = (calib["b2"] * ((b6 * b6) >> 12)) >> 11
            x2 = (calib["ac2"] * b6) >> 11
            x3 = x1 + x2
            b3 = ((calib["ac1"] * 4 + x3) + 2) >> 2

            x1 = (calib["ac3"] * b6) >> 13
            x2 = (calib["b1"] * ((b6 * b6) >> 12)) >> 16
            x3 = (x1 + x2 + 2) >> 2
            b4 = (calib["ac4"] * (x3 + 32768)) >> 15
            b7 = (up - b3) * 50000
            pressure = (b7 * 2) // b4

            x1 = (pressure >> 8) * (pressure >> 8)
            x1 = (x1 * 3038) >> 16
            x2 = (-7357 * pressure) >> 16
            pressure = pressure + ((x1 + x2 + 3791) >> 4)

            altitude_m = 44330.0 * (1.0 - (pressure / SEA_LEVEL_PRESSURE_PA) ** 0.1903)
        except Exception as exc:  # noqa: BLE001
            return {
                "source": self.source,
                "updated_at": now_iso,
                "ok": False,
                "error": f"GY-63 read failed: {exc}",
                "address": GY63_ADDRESS,
            }

        return {
            "source": self.source,
            "updated_at": now_iso,
            "ok": True,
            "address": GY63_ADDRESS,
            "pressure_pa": float(pressure),
            "pressure_hpa": round(float(pressure) / 100.0, 2),
            "altitude_m": round(float(altitude_m), 3),
            "temperature_c": round(float(temp_c), 2),
        }

    def get_hardware_readiness(self) -> dict[str, Any]:
        i2c_device_path = f"/dev/i2c-{I2C_BUS_ID}"
        i2c_device_exists = Path(i2c_device_path).exists()
        gpio_ok = self._gpio_ready
        i2c_ok = self._i2c_bus is not None

        return {
            "ok": gpio_ok and i2c_ok and i2c_device_exists,
            "gpio": {
                "initialized": gpio_ok,
                "error": self._gpio_error,
                "provider": "RPi.GPIO",
            },
            "i2c": {
                "initialized": i2c_ok,
                "error": self._i2c_error,
                "provider": "smbus2",
                "bus_id": I2C_BUS_ID,
                "device_path": i2c_device_path,
                "device_path_exists": i2c_device_exists,
            },
        }

    def get_snapshot(self) -> dict[str, Any]:
        button = self._read_button()
        mpu6050 = self._read_mpu6050()
        gy63 = self._read_gy63()

        return {
            "source": self.source,
            "updated_at": self._utc_now(),
            "bus": {
                "ok": self._i2c_bus is not None,
                "name": f"i2c-{I2C_BUS_ID}",
                "pins": {"sda": I2C_SDA_PIN, "scl": I2C_SCL_PIN},
                "devices": {
                    name: {
                        "bus_id": assignment.bus_id,
                        "address": hex(assignment.address),
                    }
                    for name, assignment in DEVICE_I2C_ASSIGNMENTS.items()
                },
                "error": self._i2c_error,
            },
            "button": button,
            "mpu6050": mpu6050,
            "gy63": gy63,
            "pinmap": PINMAP_RESPONSE,
        }
