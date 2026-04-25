import appdaemon.plugins.hass.hassapi as hass
import minimalmodbus
import serial

class OEG(hass.Hass):

    def initialize(self):
        self.log("OEG AppDaemon started")

        # Configuration Modbus
        self.instrument = minimalmodbus.Instrument('/dev/ttyACM0', 128, mode=minimalmodbus.MODE_ASCII)
        self.instrument.serial.baudrate = 9600
        self.instrument.serial.parity = serial.PARITY_EVEN
        self.instrument.serial.bytesize = 7
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 0.3
        self.instrument.clear_buffers_before_each_transaction = True

        # Hystérésis pompe calculée
        self.delta_on = 6.0
        self.delta_off = 4.0
        self.pump_state = False

        # Lecture toutes les 5 minutes
        self.run_every(self.read_oeg, "now", 300)

    # ---------------------------------------------------------
    # Décodages
    # ---------------------------------------------------------

    def decode_circulator_status(self, val):
        table = {
            0: "stopped",
            1: "running",
            2: "fault",
            3: "starting",
            4: "stopping",
            5: "unknown"
        }
        return table.get(val, f"code_{val}")

    def decode_onoff_bits(self, val):
        r1 = bool(val & 1)
        r2 = bool(val & 2)
        r3 = bool(val & 4)
        return {
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "text": f"R1:{'ON' if r1 else 'OFF'}, R2:{'ON' if r2 else 'OFF'}, R3:{'ON' if r3 else 'OFF'}"
        }

    def decode_modulation(self, val):
        if 0 <= val <= 100:
            return float(val)
        if 100 < val <= 1000:
            return val / 10.0
        return float(val)

    # ---------------------------------------------------------
    # Lecture Modbus
    # ---------------------------------------------------------

    def read_reg(self, reg, decimals=0):
        try:
            return self.instrument.read_register(reg, decimals, 3)
        except Exception as e:
            self.log(f"Erreur lecture registre {reg}: {e}")
            return None

    # Filtre pour T3/T4/T5 (valeurs absurdes > 200°C)
    def filter_temp(self, value):
        if value is None:
            return None
        if value > 200:  # valeur impossible → sonde absente
            return None
        return value

    # ---------------------------------------------------------
    # Boucle principale
    # ---------------------------------------------------------

    def read_oeg(self, kwargs):

        # --- Températures ---
        t1 = self.read_reg(38, 1)
        t2 = self.read_reg(39, 1)
        t3 = self.filter_temp(self.read_reg(40, 1))
        t4 = self.filter_temp(self.read_reg(41, 1))
        t5 = self.filter_temp(self.read_reg(42, 1))
        t_retour = self.read_reg(59, 1)

        if t1 is not None and t2 is not None:
            delta = round(t1 - t2, 1)
        else:
            delta = None

        # Hystérésis calculée
        if delta is not None:
            if not self.pump_state and delta > self.delta_on:
                self.pump_state = True
            elif self.pump_state and delta < self.delta_off:
                self.pump_state = False

        # --- Registres pompe ---
        status_raw = self.read_reg(31, 0)
        onoff_raw = self.read_reg(35, 0)
        modulation_raw = self.read_reg(58, 0)

        # Décodages
        status_text = self.decode_circulator_status(status_raw) if status_raw is not None else None
        onoff = self.decode_onoff_bits(onoff_raw) if onoff_raw is not None else None
        modulation = self.decode_modulation(modulation_raw) if modulation_raw is not None else None

        # ---------------------------------------------------------
        # Publication Home Assistant
        # ---------------------------------------------------------

        # Températures
        if t1 is not None: self.set_state("sensor.oeg_t1", state=t1, attributes={"unit_of_measurement": "°C"})
        if t2 is not None: self.set_state("sensor.oeg_t2", state=t2, attributes={"unit_of_measurement": "°C"})
        if t3 is not None: self.set_state("sensor.oeg_t3", state=t3, attributes={"unit_of_measurement": "°C"})
        if t4 is not None: self.set_state("sensor.oeg_t4", state=t4, attributes={"unit_of_measurement": "°C"})
        if t5 is not None: self.set_state("sensor.oeg_t5", state=t5, attributes={"unit_of_measurement": "°C"})
        if t_retour is not None: self.set_state("sensor.oeg_retour", state=t_retour, attributes={"unit_of_measurement": "°C"})

        if delta is not None:
            self.set_state("sensor.oeg_delta", state=delta, attributes={"unit_of_measurement": "°C"})

        # Pompe calculée
        self.set_state("sensor.oeg_pump_calc", state="ON" if self.pump_state else "OFF")

        # Pompe réelle : status
        if status_raw is not None:
            self.set_state("sensor.oeg_pump_status",
                state=status_raw,
                attributes={"text": status_text}
            )

        # Pompe réelle : R1/R2/R3
        if onoff_raw is not None:
            self.set_state("sensor.oeg_pump_onoff",
                state=onoff_raw,
                attributes=onoff
            )

        # Pompe réelle : modulation %
        if modulation_raw is not None:
            self.set_state("sensor.oeg_pump_modulation",
                state=round(modulation, 1),
                attributes={"raw": modulation_raw, "unit_of_measurement": "%"}
            )

        # ---------------------------------------------------------
        # 💡 Nouveau : puissance réelle en watts
        # ---------------------------------------------------------
        if modulation is not None:
            power = round(30 * (modulation / 100.0), 1)
            self.set_state(
                "sensor.oeg_pump_power",
                state=power,
                attributes={
                    "unit_of_measurement": "W",
                    "modulation": modulation
                }
            )

        self.log("Lecture OEG terminée")
