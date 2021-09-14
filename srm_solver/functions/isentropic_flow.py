# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores the functions that solve isentropic flow equations.
"""

import numpy as np


def get_critical_pressure(k_mix_ch):
    """
    Returns value of the critical pressure ratio.
    """
    return (2 / (k_mix_ch + 1)) ** (k_mix_ch / (k_mix_ch - 1))


def get_opt_expansion_ratio(k, P0, P_ext):
    """
    Returns the optimal expansion ratio based on the current chamber pressure,
    specific heat ratio and external pressure.
    """
    Exp_opt = ((((k + 1) / 2) ** (1 / (k - 1))) * ((P_ext / P0) ** (1 / k)) *
               np.sqrt(((k + 1) / (k - 1)) * (1 - (P_ext / P0) ** ((k - 1) / k)))) ** - 1
    return Exp_opt


def get_exit_mach(k: float, E: float):
    """
    Gets the exit Mach number of the nozzle flow.
    """
    M_exit = scipy.optimize.fsolve(
        lambda x: (((1 + 0.5 * (k - 1) * x ** 2) / (1 + 0.5 * (k - 1))) ** ((k + 1) / (2 * (k - 1)))) / x - E,
        [10]
    )
    return M_exit[0]


def get_exit_pressure(k_2ph_ex, E, P0):
    """
    Returns the exit pressure of the nozzle flow.
    """
    Mach_exit = get_exit_mach(k_2ph_ex, E)
    P_exit = P0 * (1 + 0.5 * (k_2ph_ex - 1) * Mach_exit ** 2) ** (- k_2ph_ex / (k_2ph_ex - 1))
    return P_exit


def get_thrust_coeff(P0, P_exit, P_external, E, k, n_cf):
    """
    Returns value for thrust coefficient based on the chamber pressure and
    correction factor.
    """
    P_r = P_exit / P0
    Cf_ideal = np.sqrt((2 * (k ** 2) / (k - 1)) * ((2 / (k + 1)) ** ((k + 1) / (k - 1))) * (1 - (P_r ** ((k - 1) / k))))
    Cf = (Cf_ideal + E * (P_exit - P_external) / P0) * n_cf
    if Cf <= 0:
        Cf = 0
    if Cf_ideal <= 0:
        Cf_ideal = 0
    return Cf, Cf_ideal


def get_impulses(F_avg, t, t_burnout, m_prop):
    """
    Returns total and specific impulse, given the average thrust, time
    nparray and propellant mass nparray.
    """
    t = t[t <= t_burnout]
    index = np.where(t == t_burnout)
    m_prop = m_prop[: index[0][0]]
    I_total = F_avg * t[-1]
    I_sp = I_total / (m_prop[0] * 9.81)
    return I_total, I_sp


def get_operational_correction_factors(
    P0,
    P_external,
    P0_psi,
    propellant,
    structure,
    critical_pressure_ratio,
    V0,
    t
):
    """
    Returns kinetic, two-phase and boundary layer correction factors based
    on a015140.
    """

    # Kinetic losses
    if P0_psi >= 200:
        n_kin = 33.3 * 200 * (propellant.Isp_frozen / propellant.Isp_shifting) / P0_psi
    else:
        n_kin = 0

    # Boundary layer and two phase flow losses
    if P_external / P0 <= critical_pressure_ratio:

        termC2 = 1 + 2 * np.exp(- structure.C2 * P0_psi ** 0.8 * t / ((structure.D_throat / 0.0254) ** 0.2))
        E_cf = 1 + 0.016 * structure.Exp_ratio ** - 9
        n_bl = structure.C1 * ((P0_psi ** 0.8) / ((structure.D_throat / 0.0254) ** 0.2)) * termC2 * E_cf

        C7 = 0.454 * (P0_psi ** 0.33) * (propellant.qsi_ch ** 0.33) * (1 - np.exp(- 0.004 * (V0 / get_circle_area(
            structure.D_throat)) / 0.0254) * (1 + 0.045 * structure.D_throat / 0.0254))
        if 1 / propellant.M_ch >= 0.9:
            C4 = 0.5
            if structure.D_throat / 0.0254 < 1:
                C3, C5, C6 = 9, 1, 1
            elif 1 <= structure.D_throat / 0.0254 < 2:
                C3, C5, C6 = 9, 1, 0.8
            elif structure.D_throat / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 13.4, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 10.2, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 7.58, 0.8, 0.33
        elif 1 / propellant.M_ch < 0.9:
            C4 = 1
            if structure.D_throat / 0.0245 < 1:
                C3, C5, C6 = 44.5, 0.8, 0.8
            elif 1 <= structure.D_throat / 0.0254 < 2:
                C3, C5, C6 = 30.4, 0.8, 0.4
            elif structure.D_throat / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 44.5, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 30.4, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 25.2, 0.8, 0.33
        n_tp = C3 * ((propellant.qsi_ch * C4 * C7 ** C5) / (P0_psi ** 0.15 * structure.Exp_ratio ** 0.08 *
                                                            (structure.D_throat / 0.0254) ** C6))
    else:
        n_tp = 0
        n_bl = 0

    return n_kin, n_tp, n_bl


def get_expansion_ratio(
    Pe: float,
    P0: list,
    k: float,
    critical_pressure_ratio: float
):
    """
    Returns array of the optimal expansion ratio for each pressure ratio.
    """
    E = np.zeros(np.size(P0))

    for i in range(np.size(P0)):
        if Pe / P0[i] <= critical_pressure_ratio:
            pressure_ratio = Pe / P0[i]
            E[i] = (((k + 1) / 2) ** (1 / (k - 1)) * pressure_ratio ** (1 / k) * (
                    (k + 1) / (k - 1) * (1 - pressure_ratio ** ((k - 1) / k))) ** 0.5) ** -1
        else:
            E[i] = 1
    return np.mean(E)