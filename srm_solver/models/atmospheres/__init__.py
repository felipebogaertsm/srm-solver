# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from fluids.atmosphere import ATMOSPHERE_1976


class Atmosphere1976:
    def __init__(self) -> None:
        pass

    def get_air_density_by_altitude(y_amsl):
        """
        Gets the air density using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976(y_amsl).rho

    def get_gravity_by_altitude(y_amsl):
        """
        Gets the gravity using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976.gravity(y_amsl)

    def get_air_pressure_by_altitude(y_amsl):
        """
        Gets the air density using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976(y_amsl).P
