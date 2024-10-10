import asyncio
from bleak import BleakClient
from decimal import Decimal
import binascii
import re

class BLESPPUtils:
    def __init__(self, address, uuid, notify_uuid, read_uuid, slow_interval=0.05, interval=0.01, one_length=100):
        self.device_address = address
        self.slow_interval = slow_interval
        self.interval = interval 
        self.one_length = one_length

        self._is_full = False
        self._uuid = uuid
        self._notify_uuid = notify_uuid
        self._read_uuid = read_uuid
        self._connected = False

    @staticmethod
    def is_valid_mac(mac):
        """Validates MAC address format."""
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return re.match(mac_pattern, mac) is not None

    @property
    def device_address(self):
        return self._device_address
    @device_address.setter
    def device_address(self, value):
        if not self.is_valid_mac(value):
            raise ValueError("Invalid MAC address format.")
        self._device_address = value


     # Property for one_length
    @property
    def one_length(self):
        return self._one_length
    @one_length.setter
    def one_length(self, value):
        if value <= 0:
            raise ValueError("one_length must be a positive integer.")
        self._one_length = value

    # Property for interval
    @property
    def interval(self):
        return self._interval
    @interval.setter
    def interval(self, value):
        if value < 0:
            raise ValueError("interval must be a non-negative number.")
        self._interval = value

    # Property for slow_interval
    @property
    def slow_interval(self):
        return self._slow_interval
    @slow_interval.setter
    def slow_interval(self, value):
        if value < 0:
            raise ValueError("slow_interval must be a non-negative number.")
        self._slow_interval = value

    # Read-only property for is_full
    @property
    def is_full(self):
        return self._is_full

    # Read-only property for uuid
    @property
    def uuid(self):
        return self._uuid

    # Read-only property for notify_uuid
    @property
    def notify_uuid(self):
        return self._notify_uuid

    # Read-only property for read_uuid
    @property
    def read_uuid(self):
        return self._read_uuid

    # Read-only property for connected
    @property
    def connected(self):
        return self._connected
    @connected.setter
    def connected(self, value):
        self._connected = value

    async def is_connected(self):
        try:
            value = await self._client.read_gatt_char(self.read_uuid)
            if value:
                return True
        except:
            return False
        
    async def start_notify(self, function):
        if await self.is_connected():
            try:
                await self._client.start_notify(self.notify_uuid, function)
            except Exception as e:
                print(f"Notification start error: {e}")
    
    async def stop_notify(self):
        if await self.is_connected():
            try:
                await self._client.stop_notify(self.notify_uuid)
            except Exception as e:
                print(f"Notification stop error: {e}")
    
    async def connect(self):
        try:
            self._client = BleakClient(self.device_address)
            await self._client.connect()
            self.connected = True
            #print(f"Connected to {self.device_address}")
            return True
        except Exception as e:
           print(f"Failed to connect: {e}")
           return False

    async def disconnect(self):
        if self._client:
            await self._client.disconnect()
            self.connected = False
            print(f"Disconnected from {self.device_address}")
    
    async def read_characteristic(self):
        try:
            value = await self._client.read_gatt_char(self.read_uuid)
            print(f"READING {self.read_uuid}: {value}")
        except Exception as e:
            print(f"Error reading characteristic: {e}")

    async def write_characteristic(self, data):
        if not self.connected:
            return False
        # If the data is a list, convert it to a hex string first
        if isinstance(data, list):
            hex_string = ""
            for value in data:
                # Convert negative values to their unsigned 8-bit representation
                if value < 0:
                    value = (value + 256) % 256
                hex_string += f"{value:02X}"

            data = binascii.unhexlify(hex_string)  # Convert hex string to binary data

            length = len(data)
            i2 = 0
            i3 = 0

            while i2 < length:
                try:
                    # Determine chunk size
                    chunk_size = min(self.one_length, length - i2)

                    # Write the chunk to the GATT characteristic
                    await self._client.write_gatt_char(self.uuid, data[i2:i2 + chunk_size])

                    i2 += chunk_size
                    i3 = 0  # Reset the error counter

                    # Determine sleep time based on full/slow status
                    await asyncio.sleep(self.interval if not self.is_full else self.slow_interval)

                except Exception as e:
                    if "Access Denied" in str(e):
                        print(f"Cant send data to uuid {self.uuid}")
                    print(f"Error during sending: {str(e)}")
                    i3 += 1

                    # Retry logic (similar to Java retries with sleeps)
                    if i3 >= 50:
                        #print("Failed to send data after multiple retries")
                        return False
                        #raise Exception("Failed to send data")

                    await asyncio.sleep(0.004)  # Retry delay

            if length > 50:
                return True
                #print("Write successful!")
        
    async def send(self, data):
        try:
            #print("Sending initialization data")
            await self.write_characteristic([18,81,120,-93,0,1,0,0,0,-1])
            await self.write_characteristic([18,81,120,-88,0,1,0,0,0,-1])
            await self.write_characteristic([18,81,120,-69,0,1,0,1,7,-1])
            await self.write_characteristic([18,81,120,-93,0,1,0,0,0,-1])

            #print("Writing data...")
            await self.write_characteristic(data)
            return True
        except:
            return False
