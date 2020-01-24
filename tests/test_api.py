import unittest
import traceback
import sys

import cm4twc


def set_up_model_from_3_components(surface, subsurface, openwater):

    try:
        cm4twc.Model(surface=surface,
                     subsurface=subsurface,
                     openwater=openwater)
    except (TypeError, UserWarning) as e:
        # check in traceback if the TypeError originates from the right
        # method of |Model|
        tb = traceback.extract_tb(sys.exc_info()[2])
        if tb[-1].filename.split('/')[-1] == 'model.py' and \
                (tb[-1].name == '__init__' or
                 tb[-1].name == '_instantiate_component_with_depend_checks'):
            return False
        else:
            return e
    else:
        return True


class TestAPI(unittest.TestCase):

    def test_allowed_component_combinations(self):

        # full factorial design of experiment
        # (i.e. all possible combinations of components)
        doe = {
            # keys: tuple(surface_component, subsurface_component, openwater_component)
            #       with 'c' for _Component, 'd' for DataBase, 'n' for None
            # values: 's' for supported, 'i' for impossible, 'p' for possible but not supported
            ('c', 'c', 'c'): 's',
            ('d', 'c', 'c'): 's',
            ('n', 'c', 'c'): 'i',  # surface outwards required
            ('c', 'd', 'c'): 's',
            ('d', 'd', 'c'): 's',
            ('n', 'd', 'c'): 'i',  # surface outwards required
            ('c', 'n', 'c'): 'i',  # subsurface outwards required
            ('d', 'n', 'c'): 'i',  # subsurface outwards required
            ('n', 'n', 'c'): 'i',  # surface+subsurface outwards required
            ('c', 'c', 'd'): 'p',  # openwater data unnecessary
            ('d', 'c', 'd'): 'p',  # openwater data unnecessary
            ('n', 'c', 'd'): 'i',  # surface outwards required & openwater data unnecessary
            ('c', 'd', 'd'): 'p',  # subsurface+openwater data unnecessary
            ('d', 'd', 'd'): 'p',  # no modelling component at all
            ('n', 'd', 'd'): 'p',  # no modelling component at all
            ('c', 'n', 'd'): 'p',  # openwater data unnecessary
            ('d', 'n', 'd'): 'p',  # no modelling component at all
            ('n', 'n', 'd'): 'p',  # no modelling component at all
            ('c', 'c', 'n'): 's',
            ('d', 'c', 'n'): 's',
            ('n', 'c', 'n'): 'i',  # surface outwards required
            ('c', 'd', 'n'): 'p',  # subsurface data unnecessary
            ('d', 'd', 'n'): 'p',  # no modelling component at all
            ('n', 'd', 'n'): 'p',  # no modelling component at all
            ('c', 'n', 'n'): 's',
            ('d', 'n', 'n'): 'p',  # no modelling component at all
            ('n', 'n', 'n'): 'p'  # no modelling component at all
        }

        for combination, outcome in doe.items():
            # for surface component
            if combination[0] == 'c':
                surface = cm4twc.surface.Dummy
            elif combination[0] == 'd':
                surface = cm4twc.DataBase(
                    throughfall=cm4twc.Variable('throughfall'),
                    snowmelt=cm4twc.Variable('snowmelt'),
                    transpiration=cm4twc.Variable('transpiration'),
                    evaporation_soil_surface=cm4twc.Variable('evaporation_soil_surface'),
                    evaporation_ponded_water=cm4twc.Variable('evaporation_ponded_water'),
                    evaporation_openwater=cm4twc.Variable('evaporation_openwater')
                )
            else:  # i.e. 'n'
                surface = None

            # for subsurface component
            if combination[1] == 'c':
                subsurface = cm4twc.subsurface.Dummy
            elif combination[1] == 'd':
                subsurface = cm4twc.DataBase(
                    surface_runoff=cm4twc.Variable('surface_runoff'),
                    subsurface_runoff=cm4twc.Variable('subsurface_runoff')
                )
            else:  # i.e. 'n'
                subsurface = None

            # for openwater
            if combination[2] == 'c':
                openwater = cm4twc.openwater.Dummy
            elif combination[2] == 'd':
                openwater = cm4twc.DataBase(
                    discharge=cm4twc.Variable('discharge')
                )
            else:  # i.e. 'n'
                openwater = None

            try:
                self.assertEqual(set_up_model_from_3_components(surface,
                                                                subsurface,
                                                                openwater),
                                 True if outcome == 's' else False)
            except AssertionError as e:
                raise AssertionError("The combination of 3 components returning the unexpected "
                                     "outcome is {}.".format(combination)) from e


if __name__ == '__main__':
    unittest.main()