"""Central hardware pin and bus mapping for the Raspberry Pi backend."""

from __future__ import annotations

from dataclasses import dataclass


BUTTON_PIN = 40  # Physical board pin number.
I2C_SDA_PIN = 3  # Physical board pin number.
I2C_SCL_PIN = 5  # Physical board pin number.
I2C_BUS_ID = 1

MPU6050_ADDRESS = 0x68
GY63_ADDRESS = 0x77


@dataclass(frozen=True)
class I2CDeviceAssignment:
    bus_id: int
    address: int


DEVICE_I2C_ASSIGNMENTS: dict[str, I2CDeviceAssignment] = {
    "mpu6050": I2CDeviceAssignment(bus_id=I2C_BUS_ID, address=MPU6050_ADDRESS),
    "gy63": I2CDeviceAssignment(bus_id=I2C_BUS_ID, address=GY63_ADDRESS),
}


PINMAP_RESPONSE = {
    "button_pin": BUTTON_PIN,
    "i2c": {
        "sda_pin": I2C_SDA_PIN,
        "scl_pin": I2C_SCL_PIN,
        "bus_id": I2C_BUS_ID,
        "devices": {
            name: {
                "bus_id": assignment.bus_id,
                "address": hex(assignment.address),
            }
            for name, assignment in DEVICE_I2C_ASSIGNMENTS.items()
        },
    },
}
