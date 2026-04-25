# OEG-Solar-Water-Heater-

Unofficial integration to connect an **OEG-KSW-E** solar water heater controller to Home Assistant using AppDaemon. The connection is made via USB. Inspired by the work of https://github.com/ced2git/oeg_kmsd and https://github.com/Yannicflight/oeg_kmsd

Manual installation:

- Install AppDaemon. https://github.com/Poeschl/Hassio-Addons.
- Connect the OEG-KSW-E controller to the Raspberry Pi's USB port.
- Modify the USB serial port in "oeg.py" if it is different.
- Go to /addon_configs/a0d7b954_appdaemon/apps and create the "oeg" folder. Copy oeg.py into the "oeg" folder.
- Add the following to /addon_configs/a0d7b954_appdaemon/apps/apps.yaml:
oeg:
module: oeg
class: OEG
- Paste the following into AppDaemon:
system_packages: []
python_packages:
- minimalmodbus
- pyserial
init_commands: []
log_level: info
- Restart AppDaemon
- Go to Developer Tools and search for oeg to view the sensors.



