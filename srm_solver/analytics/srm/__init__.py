# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass
from typing import Optional

import numpy as np
import plotly.graph_objects as go

from .. import Analyze
from models.atmosphere import Atmosphere
from models.propulsion import SolidMotor
from models.recovery import Recovery
from models.rocket import Rocket
from operations.ballistics import Ballistic1DOperation
from simulations.ballistics import BallisticSimulation
from simulations.internal_ballistics import InternalBallistics
from utils.isentropic_flow import get_total_impulse, get_specific_impulse
from utils.units import convert_mpa_to_pa, convert_pa_to_mpa


@dataclass
class AnalyzeSRMOperation(Analyze):
    initial_propellant_mass: float
    theoretical_motor: SolidMotor
    external_pressure: float

    thrust_header_name: Optional[str] = "Force (N)"
    time_header_name: Optional[str] = "Time (s)"
    pressure_header_name: Optional[str] = "Pressure (MPa)"

    igniter_pressure: Optional[float] = 1.5e6  # in Pa
    external_pressure: Optional[float] = 1e5  # in Pa
    simulation_resolution: Optional[float] = 0.01

    def __post_init__(self):
        self.ib_simulation = InternalBallistics(
            motor=self.theoretical_motor,
            d_t=self.simulation_resolution,
            igniter_pressure=self.igniter_pressure,
            external_pressure=self.external_pressure,
        )

        (
            self.theoretical_motor_time,
            self.theoretical_motor_operation,
        ) = self.ib_simulation.run()

    def get_thrust(self) -> np.ndarray:
        return self.get_from_df(self.thrust_header_name)

    def get_time(self) -> np.ndarray:
        return self.get_from_df(self.time_header_name)

    def get_pressure(self) -> np.ndarray:
        return convert_mpa_to_pa(self.get_from_df(self.pressure_header_name))

    def get_temperatures(
        self, col_name_startswith="Temperature"
    ) -> np.ndarray:
        """
        :param str col_name_startswith: The name that the column starts with
        :return: An array of temperatures captured by each thermopar.
        :rtype: np.ndarray
        """
        col_names = self.data.columns.values().tolist()
        temperature_col_names = [
            col_name
            for col_name in col_names
            if col_name.startswith(col_name_startswith)
        ]

        temperatures = np.array([])

        for name in temperature_col_names:
            temperatures = np.append(temperatures, self.get_from_df(name))

        return temperatures

    def get_total_impulse(self) -> float:
        return get_total_impulse(
            np.average(self.get_thrust()), self.get_time()[-1]
        )

    def get_specific_impulse(self) -> float:
        return get_specific_impulse(
            self.get_total_impulse(), self.initial_propellant_mass
        )

    def get_instantaneous_propellant_mass(self, t: float) -> float:
        """
        IMPORTANT NOTE: this method is only an estimation of the propellant
        mass during the operation of the motor. It assumes a constant nozzle
        efficiency throughout the operation and perfect correlation between
        thrust and pressure data.

        :param float t: The time at which the propellant mass is desired
        :return: The propellant mass at time t
        :rtype: np.ndarray
        """
        t_index = np.where(self.get_time() == t)[0][0]

        time = self.get_time()[t_index:-1]
        thrust = self.get_thrust()[t_index:-1]

        return (
            np.trapz(y=thrust, x=time) / self.get_total_impulse()
        ) * self.initial_propellant_mass

    def get_propellant_mass(self) -> np.ndarray:
        """
        Calculates propellant mass for each instant and appends in an array.

        :return: The propellant mass at each time step
        :rtype: np.ndarray
        """
        return np.array(
            list(
                map(
                    lambda time: self.get_instantaneous_propellant_mass(time),
                    self.get_time(),
                )
            )
        )

    def run_ballistic_simulation(
        self,
        rocket: Rocket,
        recovery: Recovery,
        atmosphere: Atmosphere,
        d_t: float = 0.1,
        initial_elevation: float = 0.0,
        rail_length: float = 5.0,
    ) -> tuple[np.ndarray, Ballistic1DOperation]:
        self.ballistic_simulation = BallisticSimulation(
            thrust=self.get_thrust(),
            initial_propellant_mass=self.initial_propellant_mass,
            motor_dry_mass=self.theoretical_motor.structure.dry_mass,
            time=self.get_time(),
            rocket=rocket,
            recovery=recovery,
            atmosphere=atmosphere,
            d_t=d_t,
            initial_elevation_amsl=initial_elevation,
            rail_length=rail_length,
        )

        (
            t,
            ballistic_operation,
        ) = self.ballistic_simulation.run()

        return (t, ballistic_operation)

    def plot_thrust_propellant_mass(
        self,
        title: str = "SRM Hot-Fire Analysis",
        thrust_color: str = "#d62728",
        propellant_mass_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.get_time(),
                y=self.get_thrust(),
                name="Thrust (N)",
                yaxis="y",
                line=dict(color=thrust_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.get_time(),
                y=self.get_propellant_mass(),
                name="Est. propellant mass (kg)",
                yaxis="y2",
                line=dict(color=propellant_mass_color),
            ),
        )

        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(
            title_text=title,
            yaxis=dict(
                title="<b>Thrust</b> (N)",
                titlefont=dict(color=thrust_color),
                tickfont=dict(color=thrust_color),
            ),
            yaxis2=dict(
                title="<b>Propellant mass</b> (kg)",
                titlefont=dict(color=propellant_mass_color),
                tickfont=dict(color=propellant_mass_color),
                side="right",
                overlaying="y",
            ),
        )

        return figure

    def plot_pressure(
        self,
        title: str = "SRM Hot-Fire Analysis - Chamber Pressure",
        test_pressure_color: str = "#d62728",
        theoretical_pressure_color: str = "#1f77b4",
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=self.get_time(),
                y=convert_pa_to_mpa(self.get_pressure()),
                name="Experimental data",
                line=dict(color=test_pressure_color),
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=self.theoretical_motor_time,
                y=convert_pa_to_mpa(self.theoretical_motor_operation.P_0),
                name="Theoretical data",
                line=dict(color=theoretical_pressure_color),
            ),
        )

        figure.update_xaxes(title_text="Time (s)")
        figure.update_layout(
            title_text=title,
            yaxis=dict(title="<b>Chamber pressure</b> (MPa)"),
        )

        return figure
