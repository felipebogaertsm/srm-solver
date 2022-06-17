# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import time

import numpy as np
import plotly.express as px

from models.propulsion.grain import Grain
from models.propulsion.grain.bates import BatesSegment
from models.propulsion.structure import (
    BoltedCombustionChamber,
    MotorStructure,
    Nozzle,
)
from models.propellants.solid import get_solid_propellant_from_name
from models.recovery import Recovery
from models.rocket import Rocket
from models.materials.metals import Steel, Al6063T5
from models.materials.elastics import EPDM
from models.propulsion.thermals import ThermalLiner
from models.recovery.events import (
    AltitudeBasedEvent,
    ApogeeBasedEvent,
)
from models.recovery.parachutes import HemisphericalParachute
from models.rocket.fuselage import Fuselage
from models.rocket.structure import RocketStructure
from models.atmosphere import Atmosphere1976
from models.propulsion import SolidMotor

from montecarlo import MonteCarloParameter, MonteCarloSimulation

from simulations.internal_balistics_coupled import InternalBallisticsCoupled


def main():
    # /////////////////////////////////////////////////////////////////////////
    # TIME FUNCTION START
    # Starts the timer.

    start = time.time()

    # /////////////////////////////////////////////////////////////////////////
    # PRE CALCULATIONS AND DEFINITIONS
    # This section is responsible for creating all of the instances of classes that
    # can be obtained from the input data.
    # It includes instanced of the classes: PropellantSelected, BATES,
    # MotorStructure, Rocket, Rocket and Recovery.
    # It also does some small calculations of the chamber length and chamber
    # diameter.

    # Motor:
    propellant = get_solid_propellant_from_name(prop_name="KNSB-NAKKA")

    grain = Grain()

    bates_segment_45 = BatesSegment(
        outer_diameter=MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=MonteCarloParameter(value=45e-3, tolerance=1e-3),
        length=MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )
    bates_segment_60 = BatesSegment(
        outer_diameter=MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=MonteCarloParameter(value=60e-3, tolerance=1e-3),
        length=MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    nozzle = Nozzle(
        throat_diameter=MonteCarloParameter(value=37e-3, tolerance=0.5e-3),
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=Steel(),
    )

    liner = ThermalLiner(thickness=2e-3, material=EPDM())

    chamber = BoltedCombustionChamber(
        casing_inner_diameter=128.2e-3,
        outer_diameter=141.3e-3,
        liner=liner,
        length=grain.total_length + 10e-3,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=9e-3,
        screw_diameter=6.75e-3,
    )

    structure = MotorStructure(
        safety_factor=4,
        dry_mass=21.013,
        nozzle=nozzle,
        chamber=chamber,
    )

    motor = SolidMotor(grain=grain, propellant=propellant, structure=structure)

    # Recovery:
    recovery = Recovery()
    recovery.add_event(
        ApogeeBasedEvent(
            trigger_value=1,
            parachute=HemisphericalParachute(diameter=1.25),
        )
    )
    recovery.add_event(
        AltitudeBasedEvent(
            trigger_value=450,
            parachute=HemisphericalParachute(diameter=2.66),
        )
    )

    # Rocket:
    fuselage = Fuselage(
        length=4e3,
        drag_coefficient=0.5,
        outer_diameter=0.17,
    )

    rocket_structure = RocketStructure(mass_without_motor=25)

    rocket = Rocket(
        fuselage=fuselage,
        structure=rocket_structure,
    )

    # /////////////////////////////////////////////////////////////////////////
    # INTERNAL BALLISTICS AND TRAJECTORY
    # This section runs the main simulation of the program, returning the results
    # of all the internal ballistics and trajectory calculations.
    # The 'run_ballistics' function runs, in a single loop, the chamber pressure
    # PDE as well as the rocket flight mechanics ODE.
    # The exit pressure of the motor is automatically subtracted from the external
    # (or ambient) pressure of the rocket during flight, yielding more precise
    # motor thrust estimation.
    # 'run_ballistics' returns instances of the classes Ballistics and
    # InternalBallistics.

    montecarlo_sim = MonteCarloSimulation(
        [
            motor,
            rocket,
            recovery,
            Atmosphere1976(),
            0.01,
            10,
            600,
            1.5e6,
            5,
        ],
        100,
        InternalBallisticsCoupled,
    )

    results = montecarlo_sim.run()

    apogees = np.array([result[2].apogee for result in results])

    fig = px.scatter(y=apogees)
    fig.show()


if __name__ == "__main__":
    main()