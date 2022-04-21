# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores BATES class and methods.
"""

import numpy as np

from utils.geometric import get_circle_area


class Bates:
    def __init__(
        self,
        segment_count: int,
        segment_spacing: float,
        outer_diameter: float,
        core_diameter: np.array,
        segment_length: np.array,
    ):
        self.segment_count = segment_count
        self.segment_spacing = segment_spacing
        self.outer_diameter = outer_diameter
        self.core_diameter = core_diameter
        self.segment_length = segment_length

    @property
    def total_length(self):
        return (
            np.sum(self.segment_length)
            + (self.segment_count - 1) * self.segment_spacing
        )

    def get_optimal_segment_length(self):
        """
        Returns the optimal length for each of the input grains.
        """
        optimal_grain_length = (
            1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)
        )
        return optimal_grain_length

    def get_mass_flux_per_segment(self, burn_rate, propellant_density, x):
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
        """
        segment_mass_flux = np.zeros((self.segment_count, np.size(x)))
        segment_mass_flux = np.zeros((self.segment_count, np.size(x)))
        total_grain_Ab = np.zeros((self.segment_count, np.size(x)))
        for j in range(self.segment_count):
            for i in range(np.size(burn_rate)):
                for k in range(j + 1):
                    total_grain_Ab[j, i] = total_grain_Ab[
                        j, i
                    ] + self.get_burn_area(x[i], k)
                segment_mass_flux[j, i] = (
                    total_grain_Ab[j, i] * propellant_density * burn_rate[i]
                )
                segment_mass_flux[j, i] = segment_mass_flux[j, i] / (
                    get_circle_area(self.core_diameter[j] + x[i])
                )
        return segment_mass_flux

    def get_burn_area_per_segment(
        self, segment_index: int, web_thickness: float
    ):
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.segment_length

        if 0.5 * (D_grain - D_core[segment_index]) >= web_thickness:
            return np.pi * (
                (
                    (D_grain ** 2)
                    - (D_core[segment_index] + 2 * web_thickness) ** 2
                )
                / 2
                + (
                    (L_grain[segment_index] - 2 * web_thickness)
                    * (D_core[segment_index] + 2 * web_thickness)
                )
            )
        else:
            return 0

    def get_burn_area(self, x: float):
        """
        Calculates the BATES burn area given the web distance.
        """
        burn_areas = np.array([])

        for i in range(self.segment_count):
            burn_areas = np.append(
                burn_areas, self.get_burn_area_per_segment(i, x)
            )

        return np.sum(burn_areas)

    def get_propellant_volume_per_segment(self, x: float, j: int):
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.segment_length

        if 0.5 * (D_grain - D_core[j]) >= x:
            return (np.pi / 4) * (
                ((D_grain ** 2) - ((D_core[j] + 2 * x) ** 2))
                * (L_grain[j] - 2 * x)
            )
        else:
            return 0

    def get_propellant_volume(self, x: float):
        """
        Calculates the BATES grain volume given the web distance.
        """
        prop_volume = np.array([])

        for i in range(self.segment_count):
            prop_volume = np.append(
                prop_volume, self.get_propellant_volume_per_segment(x, i)
            )

        return np.sum(prop_volume)

    def get_burn_profile(self, A_burn: list):
        """
        Returns string with burn profile.
        """
        if A_burn[0] / A_burn[-1] > 1.02:
            burn_profile = "regressive"
        elif A_burn[0] / A_burn[-1] < 0.98:
            burn_profile = "progressive"
        else:
            burn_profile = "neutral"
        return burn_profile
