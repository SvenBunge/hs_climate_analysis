# coding: utf-8

import math

##!!!!##################################################################################################
#### Own written code can be placed above this commentblock . Do not change or delete commentblock! ####
########################################################################################################
##** Code created by generator - DO NOT CHANGE! **##

class Hs_humidity14186(hsl20_3.BaseModule):

    def __init__(self, homeserver_context):
        hsl20_3.BaseModule.__init__(self, homeserver_context, "hs_humidity")
        self.FRAMEWORK = self._get_framework()
        self.LOGGER = self._get_logger(hsl20_3.LOGGING_NONE,())
        self.PIN_I_TEMPERATURE=1
        self.PIN_I_REL_AIR_HUMIDITY=2
        self.PIN_O_ABS_AIR_HUMIDITY=1
        self.PIN_O_MAX_AIR_HUMIDITY=2
        self.PIN_O_ENTHALPY=3
        self.PIN_O_DEW_POINT=4
        self.FRAMEWORK._run_in_context_thread(self.on_init)

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.DEBUG = self.FRAMEWORK.create_debug_section()

        self.temperature = -999
        self.rel_humidity = -999

    def on_init(self):
        pass

    def on_input_value(self, index, value):
        if index == self.PIN_I_TEMPERATURE:
            self.temperature = value
        elif index == self.PIN_I_REL_AIR_HUMIDITY:
            self.rel_humidity = value

        self.DEBUG.set_value("Temp. (C)", self.temperature)
        self.DEBUG.set_value("Rel. humidity (%)", self.rel_humidity * 100)

        if self.temperature != -999 and self.rel_humidity != -999:
            self.calculate_all_humidity_values(self.temperature, self.rel_humidity)

    def calculate_all_humidity_values(self, temp, rel_hum):
        temp_in_k = 273.15 + temp  # in K
        self.DEBUG.set_value("Temp. (K)", temp_in_k)
        sat_vapor_pressure = self.calc_saturation_vapor_pressure(temp)  # in Pa
        self.DEBUG.set_value("Sat. vapor pressure (Pa)", sat_vapor_pressure)
        vapor_pressure = sat_vapor_pressure * rel_hum  # in Pa
        self.DEBUG.set_value("Vapor pressure (Pa)", vapor_pressure)

        abs_air_humidity = vapor_pressure / (461.51 * temp_in_k)  # in kg/m³
        self.DEBUG.set_value("Abs. humidity (kg/m^3)", abs_air_humidity)
        max_abs_air_humidity = sat_vapor_pressure / (461.51 * temp_in_k)  # in kg/m³
        self.DEBUG.set_value("Max. abs. humidity (kg/m^3)", max_abs_air_humidity)
        enthalpy = self.calc_enthalpy(temp, abs_air_humidity)  # in kJ/kg
        self.DEBUG.set_value("Enthalpy (kJ/kg)", enthalpy)
        dew_point = self.calc_dew_point(temp, vapor_pressure)
        self.DEBUG.set_value("Dew point (C)", dew_point)

        self._set_output_value(self.PIN_O_ABS_AIR_HUMIDITY, abs_air_humidity * 1000)  # convert to g/m³
        self._set_output_value(self.PIN_O_MAX_AIR_HUMIDITY, max_abs_air_humidity * 1000)  # convert to g/m³
        self._set_output_value(self.PIN_O_ENTHALPY, enthalpy)
        self._set_output_value(self.PIN_O_DEW_POINT, dew_point)

    @staticmethod
    def calc_saturation_vapor_pressure(temp):
        ## Gemäß https://www.uni-due.de/ibpm/BauPhy/Feuchte/Formelsammlung/Formels.unterteilt/7Feuchtetechnische_Grundbegriffe.htm

        ## official: -20 < temp < 0 and 0 < temp < 30!!
        if temp < 0:
            a = 4.689  # Pa
            b = 1.486
            n = 12.3
        elif 0 <= temp:
            a = 288.68
            b = 1.098
            n = 8.02

        return a * ((b + temp / 100) ** n)
        # return 6.112 * math.exp((17.62 * temp) / (243.12 + temp)) # Alternative version

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
