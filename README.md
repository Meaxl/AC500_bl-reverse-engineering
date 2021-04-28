# AC500_bl-reverse-engineering
Reverse Engineering the Soehle/Leifheit Airfresh Clean Connect 500 with Bluetooth
The reverse engineering was done by analyzing the Bluetooth Low Energy communication between PacketLogger (https://developer.apple.com/download/more/?=xcode: "Additional Tools for Xcode XX") and the AC500.

### What happend already:
- dumped the bluetooth traffic for each function into it's own seperate file
- MAC: `48:87:2D:1F:DB:EB`

---

## Bluetooth

> **Primary Service**: Device Information
> - Handle: `0xda5c`
> - UUID: `0000180a-0000-1000-8000-00805f9b34fb`
> > **Characteristic**: Serial Number String
> > - Handle: `0x006c`
> > - UUID: `00002a25-0000-1000-8000-00805f9b34fb`  

> > **Characteristic**: Firmware Revision String
> > - Handle: `0x006c`
> > - UUID: `00002a26-0000-1000-8000-00805f9b34fb`

> **Primary Service**: Unkown
> - Handle: `0xda5c`
> - UUID: `0000ffa0-0000-1000-8000-00805f9b34fb`
> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `000ef01-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ef02-0000-1000-8000-00805f9b34fb`
> > > **Descriptor**: Client Characteristic Configuration
> > > - Handle: `0x55b9`
> > > - UUID: `00002902-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle:`0x006c`
> > - UUID: `0000ef03-0000-1000-8000-00805f9b34fb`
> > > **Descriptor**: Client Characteristic Configuration
> > > - Handle: `0x55b9`
> > > - UUID: `00002902-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ef04-0000-1000-8000-00805f9b34fb`
> > > **Descriptor**: Client Characteristic Configuration
> > > - Handle: `0x55b9`
> > > - UUID: `00002902-0000-1000-8000-00805f9b34fb`

> **Primary Service**: Vendor specific
> - Handle: `0xda5c`
> - UUID: `0000d0ff-3c17-d293-8e48-14fe2e4da212`
> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ffd1-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ffd2-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ffd3-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ffd4-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000ffd5-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000fff1-0000-1000-8000-00805f9b34fb`

> > **Characteristic**: Unknown
> > - Handle: `0x006c`
> > - UUID: `0000fff2-0000-1000-8000-00805f9b34fb`
