# AC500_bl-reverse-engineering
Reverse Engineering the Soehle/Leifheit Airfresh Clean Connect 500 with Bluetooth
The reverse engineering was done by analyzing the Bluetooth Low Energy communication between PacketLogger (https://developer.apple.com/download/more/?=xcode: "Additional Tools for Xcode XX") and the AC500.

### What happend already:
- dumped the bluetooth traffic for each function into it's own seperate file

---

### Informations:
MAC: `48:87:2D:1F:DB:EB`


## Bluetooth Services/Characteristics

- Primary Service (`0xda5c`): Device Information - UUID: `0000180a-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Serial Number String - UUID: `00002a25-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Firmware Revision String - UUID: `00002a26-0000-1000-8000-00805f9b34fb`


- Primary Service (`0xda5c`): Unknown - UUID: `0000ffa0-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Unknown - UUID: `000ef01-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Unknown - UUID: `0000ef02-0000-1000-8000-00805f9b34fb`
    * Descriptor (`0x55b9`): Client Characteristic Configuration - UUID: `00002902-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Unknown - UUID: `0000ef03-0000-1000-8000-00805f9b34fb`
    * Descriptor (`0x55b9`): Client Characteristic Configuration - UUID: `00002902-0000-1000-8000-00805f9b34fb`
  - Characteristic (`0x006c`): Unknown - UUID: `0000ef04-0000-1000-8000-00805f9b34fb`
    * Descriptor (`0x55b9`): Client Characteristic Configuration - UUID: `00002902-0000-1000-8000-00805f9b34fb`


- Primary Service (Handle `0xda5c`): Vendor specific - UUID: `0000d0ff-3c17-d293-8e48-14fe2e4da212`

