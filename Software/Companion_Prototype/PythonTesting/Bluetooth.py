# scan_ble.py
import asyncio
from bleak import BleakScanner, BleakClient

TEXT_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TEXT_RX_UUID      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
TEXT_TX_UUID      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

async def simple_scan():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=8.0)
    for d in devices:
        print(repr(d))

async def blescan():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        print(f"Name: {d.name!r}, Address: {d.address}")

async def find_device_by_name(name: str):
    print(f"Scanning for device with name {name!r}...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, adv: (adv.local_name == name)
    )
    return device

async def connect_on_name(target_name: str):
    device = await find_device_by_name(target_name)
    if device is None:
        print("Device not found. Make sure the Pi is advertising.")
        return

    print(f"Found device: {device.name!r} at {device.address}")
    async with BleakClient(device) as client:
        if not client.is_connected:
            print("Failed to connect")
            return
        print("Connected!")

        # Optional: list services/characteristics
        services = await client.get_services()
        print("Services and characteristics:")
        for service in services:
            print(f"[Service] {service.uuid}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                print(f"  [Char] {char.uuid} ({props})")

        # Here you would do read/write/notify on your custom UUIDs

async def connect_on_adress(adress: str):
    async with BleakClient(adress) as client:
        print("Connected:", client.is_connected)
        # Neu: services über Property holen, kein await
        services = client.services
        print("Services and characteristics:")
        for s in services:
            print("Service:", s.uuid)
            for c in s.characteristics:
                print("  Char:", c.uuid, c.properties)

async def connect_on_adress_txrx(adress: str):
    async with BleakClient(adress) as client:
        print("Connected:", client.is_connected)

        while True:
            print("\nOptions:"
                  "\n1. Send message"
                  "\n2. List services/characteristics"
                  "\n0. Exit")
            inp = input("What would you like to do?\n")      
            if inp == "1":
                msg = input("Enter message to send: ")
                await client.write_gatt_char(TEXT_RX_UUID, msg.encode())
                print("Message sent!")
            elif inp == "2":  
                services = client.services
                for s in services:
                    print("Service:", s.uuid)
                    for c in s.characteristics:
                        print("  Char:", c.uuid, c.properties)
            elif inp == "3":
                print("Subscribing to notifications...")
                def notification_handler(sender, data):
                    print(f"Notification from {sender}: {data.decode()}")

                await client.start_notify(TEXT_TX_UUID, notification_handler)
                print("Subscribed to notifications. Waiting for messages...")
                input("Press Enter to stop notifications and exit...\n")
                await client.stop_notify(TEXT_TX_UUID)
            elif inp == "0":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")

def bluetooth_manu():
    while True:
        print("This is the start of the Bluetooth testing menu.")
        print("1. Scan for BLE devices")
        print("2. Connect to target device by name and list services")
        print("3. Connect to target device by address and list services")
        print("4. Connect to target device and test TX/RX")
        choice = input("Enter your choice: ")
        if choice == '1':
            asyncio.run(blescan())
        elif choice == '2':
            target = input("Enter the target device name (default 'AR-Glasses'): ")
            asyncio.run(connect_on_name(target))
        elif choice == '3':
            #target = input("Enter the target device address (e.g., 'XX:XX:XX:XX:XX:XX'): ")
            asyncio.run(connect_on_adress("B8:27:EB:03:BD:E9"))
        elif choice == '4':
            #target = input("Enter the target device address (e.g., 'XX:XX:XX:XX:XX:XX'): ")
            asyncio.run(connect_on_adress_txrx("B8:27:EB:03:BD:E9"))
        elif choice == '0':
            print("Exiting Bluetooth testing menu.")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    bluetooth_manu()