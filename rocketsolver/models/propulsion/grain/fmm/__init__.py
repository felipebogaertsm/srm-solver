# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import skfmm
from skimage import measure

from .. import GrainGeometryError, GrainSegment
from rocketsolver.utils.decorators import validate_assertions


class FMMGrainSegment(GrainSegment, ABC):
    """
    Fast Marching Method (FMM) implementation of a grain segment.

    This class was inspired by the Andrew Reilley's software openMotor, in
    particular the fmm module.
    openMotor's repository can be accessed at:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        map_dim: int,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: Optional[int] = 0,
    ) -> None:
        self.map_dim = map_dim

        # "Cache" variables:
        self.maps = None
        self.mask = None
        self.masked_face = None
        self.regression_map = None
        self.face_area_interp_func = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
        )

    @abstractmethod
    def get_initial_face_map(self) -> np.ndarray:
        """
        Method needs to be implemented for each and every geometry.
        """
        pass

    @abstractmethod
    def get_maps(self) -> tuple[np.ndarray]:
        """
        Implementation varies depending if the geometry is 2D or 3D.
        """
        pass

    @validate_assertions(exception=GrainGeometryError)
    def validate(self) -> None:
        super().validate()

        assert self.map_dim >= 100
        self.map_dim = 10

    def normalize(self, value: int | float) -> float:
        return value / (0.5 * self.outer_diameter)

    def denormalize(self, value: int | float) -> float:
        return (value / 2) * (self.outer_diameter)

    def map_to_area(self, value: float):
        """
        Used to convert sq pixels to sqm.
        For extracting real areas from the regression map.
        """
        return (self.outer_diameter**2) * (value / (self.map_dim**2))

    def map_to_length(self, value: float) -> float:
        """
        Converts pixels to meters. Used to extract real distances from pixel
        distances such as contour lengths
        """
        return self.outer_diameter * (value / self.map_dim)

    def get_mask(self) -> np.ndarray:
        if self.mask is None:
            map_x, map_y = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1

        return self.mask

    def get_empty_face_map(self) -> np.ndarray:
        """
        Returns the empty geometry map/mesh of the grain.

        https://pythonhosted.org/scikit-fmm/
        """
        return np.ones_like(self.get_maps()[0])

    def get_masked_face(self) -> np.ndarray:
        """
        Masks the face map.
        The mask is circular shaped and normalized to the shape of the matrix.
        """
        if self.masked_face is None:
            self.masked_face = np.ma.MaskedArray(
                self.get_initial_face_map(), self.get_mask()
            )

        return self.masked_face

    def get_cell_size(self) -> float:
        return 1 / self.map_dim

    def get_regression_map(self):
        """
        Uses the fast marching method to generate an image of how the grain
        regresses from the core map.
        """
        if self.regression_map is None:
            self.regression_map = (
                skfmm.distance(self.get_masked_face(), dx=self.get_cell_size())
                * 2
            )

        return self.regression_map

    def get_web_thickness(self) -> float:
        """
        The distance between the closest and furthest point to the center of
        the grain segment.
        """
        return self.denormalize(np.amax(self.get_regression_map()))

    def get_contours(self, web_distance: float) -> np.ndarray:
        """
        Returns the contours of the regression map in function of the web
        thickness traveled.
        """
        map_dist = self.normalize(web_distance)
        return measure.find_contours(
            self.get_regression_map(), map_dist, fully_connected="low"
        )
