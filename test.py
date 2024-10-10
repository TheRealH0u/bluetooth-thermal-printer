from ImageUtils import ImageUtils
from BLESPPUtils import BLESPPUtils
import asyncio

WRITE_CHARACTERISTIC_UUID = "00000000-0000-0000-0000-000000000000"
NOTIFY_CHARACTERISTIC_UUID = "00000000-0000-0000-0000-000000000000"
READ_CHARACTERISTIC_UUID = "00000000-0000-0000-0000-000000000000"
BLE_DEVICE_ADDRESS = "00:00:00:00:00:00"

def notification_handler(sender, data):
    """Simple notification handler that prints the data received."""
    print(f"Notification from {sender}: {data}")

async def main():
    image = ImageUtils()
    data = image.generate_image("test.png")

    printer = BLESPPUtils(BLE_DEVICE_ADDRESS, WRITE_CHARACTERISTIC_UUID, NOTIFY_CHARACTERISTIC_UUID, READ_CHARACTERISTIC_UUID)
    
    print("Connecting to printer")
    if await printer.connect():
        print("Starting notifications")
        await printer.start_notify(notification_handler)

        print("SENDING DATA")
        await printer.send(data)
        print("DATA SENT")

        await asyncio.sleep(10)
        await printer.disconnect()


asyncio.run(main())

# Qx\xa3\x01\x03\x00\x00\x0e&$\xff
# Qx\xa8\x01\n\x00y\x00\x033.0.48\x002\xff

# Qx\xbb\x01\x06\x00\x00@\x17\x00\x00\x96&\xff
# Qx\xa3\x01\x03\x00\x00\x0e&$\xff