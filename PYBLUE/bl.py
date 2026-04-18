import asyncio
import bleak
import BleakClient
from crccheck.crc import Crc8Maxim

address = "48:87:2d:1f:db:eb"

async def main(address):
    async with BreakClient(address) as client:
        header = bytes.fromhex("")
        command = bytes.fromhex("")
        params = bytes.fromhex("")

        crcinst = Crc8Maxim()
        crcinst.process(header)
        crcinst.process(command)
        crcinst.process(params)
        model_number = await client.write_gatt_char("UUID HIER", header + command + params + crcinst.finalbytes())

asyncio.run(main(address))
