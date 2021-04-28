# AC500_bl-reverse-engineering
Reverse Engineering the Soehle/Leifheit Airfresh Clean Connect 500 with Bluetooth
The reverse engineering was done by analyzing the Bluetooth Low Energy communication between PacketLogger (https://developer.apple.com/download/more/?=xcode: "Additional Tools for Xcode XX") and the AC500.

---

## What happend already:
- dumped the bluetooth traffic for each function into it's own seperate file

## Informations:
- MAC Address: `48:87:2D:1F:DB:EB
- Primary Service (Handle `0xda5c`) Device Information 
  &nbsp; UUID: `0000180a-0000-1000-8000-00805f9b34fb`

