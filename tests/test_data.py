import unittest
import doctest

import cm4twc


def get_sciencish_dataset():
    return cm4twc.DataSet(
        ['data/dummy_driving_data.nc',
         'data/dummy_ancillary_data.nc'],
        name_mapping={'rainfall_flux': 'rainfall',
                      'snowfall_flux': 'snowfall',
                      'air_temperature': 'air_temperature',
                      'soil_temperature': 'soil_temperature'}
    )


def get_dummy_dataset(component_category):
    return cm4twc.DataSet(
        'data/dummy_{}_data_daily.nc'.format(component_category)
    )


def get_dummy_component_substitute_dataset(component_category):
    return cm4twc.DataSet(
        'data/dummy_{}_substitute_data_daily.nc'.format(component_category)
    )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc.data))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
