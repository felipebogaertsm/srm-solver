# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


from abc import ABC
from dataclasses import dataclass


@dataclass
class Propellant(ABC):
    """
    Base class for any propellant.
    """

    pass