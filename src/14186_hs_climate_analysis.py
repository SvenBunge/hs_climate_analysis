# coding: utf-8

import math

##!!!!##################################################################################################
#### Own written code can be placed above this commentblock . Do not change or delete commentblock! ####
########################################################################################################
##** Code created by generator - DO NOT CHANGE! **##

class Hs_climate_analysis14186(hsl20_3.BaseModule):

    def __init__(self, homeserver_context):
        hsl20_3.BaseModule.__init__(self, homeserver_context, "hs_climate_analysis")
        self.FRAMEWORK = self._get_framework()
        self.LOGGER = self._get_logger(hsl20_3.LOGGING_NONE,())
        self.PIN_I_TEMPERATURE=1
        self.PIN_I_REL_AIR_HUMIDITY=2
        self.PIN_I_AIR_PRESSURE=3
        self.PIN_O_ABS_AIR_HUMIDITY=1
        self.PIN_O_MAX_AIR_HUMIDITY=2
        self.PIN_O_AIR_DENSITY=3
        self.PIN_O_ENTHALPY=4
        self.PIN_O_DEW_POINT=5
        self.PIN_O_SULTRY=6
        self.PIN_O_HEAT_WARNING=7
        self.FRAMEWORK._run_in_context_thread(self.on_init)

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.DEBUG = self.FRAMEWORK.create_debug_section()

        self.temperature = -999
        self.rel_humidity = -999
        self.air_pressure = 1013.25

    def on_init(self):
        pass

    def on_input_value(self, index, value):
        if index == self.PIN_I_TEMPERATURE:
            self.temperature = value
        elif index == self.PIN_I_REL_AIR_HUMIDITY:
            self.rel_humidity = value
        elif index == self.PIN_I_AIR_PRESSURE:
            self.air_pressure = value * 100

        self.DEBUG.set_value("Temp. (C)", self.temperature)
        self.DEBUG.set_value("Rel. humidity (%)", self.rel_humidity * 100)
        self.DEBUG.set_value("Air pressure (Pa)", self.air_pressure)

        if self.temperature != -999 and self.rel_humidity != -999:
            self.calculate_all_humidity_values(self.temperature, self.rel_humidity, self.air_pressure)

    def calculate_all_humidity_values(self, temp, rel_hum, air_pressure):
        temp_in_k = 273.15 + temp  # in K
        self.DEBUG.set_value("Temp. (K)", temp_in_k)

        sat_vapor_pressure = self.calc_saturation_vapor_pressure(temp)  # in Pa
        self.DEBUG.set_value("Sat. vapor pressure (Pa)", sat_vapor_pressure)
        vapor_pressure = sat_vapor_pressure * rel_hum  # in Pa
        self.DEBUG.set_value("Vapor pressure (Pa)", vapor_pressure)

        abs_air_humidity = vapor_pressure / (461.51 * temp_in_k)  # in kg/m³
        self.DEBUG.set_value("Abs. humidity (kg/cbm)", abs_air_humidity)
        max_abs_air_humidity = sat_vapor_pressure / (461.51 * temp_in_k) / 100  # in kg/m³
        self.DEBUG.set_value("Max. abs. humidity (kg/cbm)", max_abs_air_humidity)
        air_density = self.calc_air_weight(temp_in_k, rel_hum, air_pressure, sat_vapor_pressure)
        self.DEBUG.set_value("Air density (kg/cbm)", air_density)

        enthalpy = self.calc_enthalpy(temp, abs_air_humidity)  # in kJ/kg
        self.DEBUG.set_value("Enthalpy (kJ/kg)", enthalpy)
        dew_point = self.calc_dew_point(temp, vapor_pressure)
        self.DEBUG.set_value("Dew point (C)", dew_point)
        sultry = abs_air_humidity > 0.0135  # 13,5g/m³ or dew point > 16°C - https://de.wikipedia.org/wiki/Schwüle
        self.DEBUG.set_value("Sultry (yes/no)", int(sultry))
        heat_warning = dew_point > 20  # DWD raises a heat warning if the dew point gets over 20°C - https://www.dwd.de/DE/wetter/thema_des_tages/2020/6/21.html
        self.DEBUG.set_value("Heat (yes/no)", int(heat_warning))

        # Set values to outputs
        self._set_output_value(self.PIN_O_ABS_AIR_HUMIDITY, abs_air_humidity * 1000)  # convert to g/m³
        self._set_output_value(self.PIN_O_MAX_AIR_HUMIDITY, max_abs_air_humidity * 1000)  # convert to g/m³
        self._set_output_value(self.PIN_O_AIR_DENSITY, air_density)
        self._set_output_value(self.PIN_O_ENTHALPY, enthalpy)
        self._set_output_value(self.PIN_O_DEW_POINT, dew_point)
        self._set_output_value(self.PIN_O_SULTRY, int(sultry))

    @staticmethod
    def calc_air_weight(temp_in_k, rel_hum, air_pressure, sat_vapor_pressure):
        # Source https://www.chemie-schule.de/KnowHow/Universelle_Gaskonstante
        spec_dry_gas_constant = 287.058  # J / kg * K - dry air
        spec_wet_gas_constant = 462  # J / kg * K - wet air

        # See https://www.chemie.de/lexikon/Luftdichte.html
        gas_constant = spec_dry_gas_constant / 1 - (rel_hum * sat_vapor_pressure / air_pressure) \
            * (1 - spec_dry_gas_constant / spec_wet_gas_constant)

        return air_pressure / (gas_constant * temp_in_k)

    @staticmethod
    def calc_saturation_vapor_pressure(temp):

        # See https://de.wikipedia.org/wiki/Sättigungsdampfdruck#Berechnung_des_Sättigungsdampfdrucks_von_Wasser_über_die_Magnus-Formel
        return 6.112 * math.exp((17.62 * temp) / (243.12 + temp)) * 100
    
    @staticmethod
    def calc_enthalpy(temp, abs_air_humidity):
        return 1.006 * temp + abs_air_humidity * (1.86 * temp + 2500)

    @staticmethod
    def calc_dew_point(temp, vapor_pressure):

        if temp < 0:  # avoid dew point calculation below freezing point
            return -1
        a = 7.5
        b = 237.3

        try:
            inter_res = math.log10(vapor_pressure / 100 / 6.1078)
            return (b * inter_res) / (a - inter_res)
        except ValueError as err:
            return -1
