"""
TODO: add tests using cm4twc.LatLonGrid
"""
import unittest
import doctest

import cm4twc


def get_dummy_spacedomain():
    return cm4twc.LatLonGrid(
        latitude=[51.5, 52.5, 53.5, 54.5],
        latitude_bounds=[[51, 52], [52, 53], [53, 54], [54, 55]],
        longitude=[-1.5, -0.5, 0.5],
        longitude_bounds=[[-2, -1], [-1, 0], [0, 1]],
        altitude=[2],
        altitude_bounds=[[0, 4]]
    )


def get_sciencish_spacedomain():
    return cm4twc.RotatedLatLonGrid(
        grid_latitude=[2.2, 1.76, 1.32, 0.88, 0.44, 0., -0.44, -0.88, -1.32, -1.76],
        grid_longitude=[-4.7, -4.26, -3.82, -3.38, -2.94, -2.5, -2.06, -1.62, -1.18],
        grid_latitude_bounds=[[2.42, 1.98], [1.98, 1.54], [1.54, 1.1], [1.1, 0.66],
                              [0.66, 0.22], [0.22, -0.22], [-0.22, -0.66],
                              [-0.66, -1.1], [-1.1, -1.54], [-1.54, -1.98]],
        grid_longitude_bounds=[[-4.92, -4.48], [-4.48, -4.04], [-4.04, -3.6],
                               [-3.6,  -3.16], [-3.16, -2.72], [-2.72, -2.28],
                               [-2.28, -1.84], [-1.84, -1.4], [-1.4, -0.96]],
        earth_radius=6371007., grid_north_pole_latitude=38.0,
        grid_north_pole_longitude=190.0,
        altitude=1.5,
        altitude_bounds=[1.0, 2.0]
    )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc.space))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
