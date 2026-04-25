# OEG-Solar-Water-Heater-

Unofficial integration to connect an **OEG-KSW-E** solar water heater controller to Home Assistant using AppDaemon. The connection is made via USB. Inspired by the work of https://github.com/ced2git/oeg_kmsd and https://github.com/Yannicflight/oeg_kmsd

Manual installation:

1) Install AppDaemon. https://github.com/Poeschl/Hassio-Addons.
2) Connect the OEG-KSW-E controller to the Raspberry Pi's USB port.
3) Modify the USB serial port in "oeg.py" if it is different.
4) Go to /addon_configs/a0d7b954_appdaemon/apps and create the "oeg" folder. Copy oeg.py into the "oeg" folder.
5) Add the following to /addon_configs/a0d7b954_appdaemon/apps/apps.yaml:<br>
oeg:<br> 
module: oeg <br> 
class: OEG <br> 
6) Paste the following into AppDaemon:<br>
system_packages: []<br>
python_packages:<br>
- minimalmodbus<br>
- pyserial<br>
init_commands: []<br>
log_level: info<br>
7) Restart AppDaemon
8) Go to Developer Tools and search for oeg to view the sensors.




