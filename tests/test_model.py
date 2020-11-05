import unittest
import doctest
import os
import numpy as np
from copy import deepcopy
from glob import glob

import cm4twc
from tests.test_time import (get_dummy_timedomain,
                             get_dummy_spin_up_start_end,
                             get_dummy_dumping_frequency)
from tests.test_component import get_dummy_component
from tests.test_state import compare_states


class Simulator(object):
    def __init__(self, time_, space_, surfacelayer_kind, subsurface_kind,
                 openwater_kind, sources=None):
        self.time_ = time_
        self.model = self._initialise_model(
            time_, space_,
            surfacelayer_kind, subsurface_kind, openwater_kind,
            sources
        )

    @staticmethod
    def _initialise_model(time_, space_, surfacelayer_kind, subsurface_kind,
                          openwater_kind, sources):
        # for surfacelayer component
        category = 'surfacelayer'
        surfacelayer = get_dummy_component(
            category, surfacelayer_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )
        # for subsurface component
        category = 'subsurface'
        subsurface = get_dummy_component(
            category, subsurface_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )
        # for openwater
        category = 'openwater'
        openwater = get_dummy_component(
            category, openwater_kind, time_, space_,
            'Python' if sources is None else sources.get(category, 'Python')
        )

        # try to get an instance of model with the given combination
        model = cm4twc.Model(
            identifier='test-{}-{}-{}{}{}'.format(
                time_, space_,
                surfacelayer_kind, subsurface_kind, openwater_kind
            ),
            config_directory='outputs',
            output_directory='outputs',
            surfacelayer=surfacelayer,
            subsurface=subsurface,
            openwater=openwater
        )

        return model

    def spinup_model(self, cycles=2):
        self.model.spin_up(
            *get_dummy_spin_up_start_end(), cycles,
            dumping_frequency=get_dummy_dumping_frequency(self.time_)
        )

    def run_model(self):
        self.model.simulate(
            dumping_frequency=get_dummy_dumping_frequency(self.time_)
        )

    def resume_model(self):
        self.model.resume(
            tag='run',
            at=(get_dummy_timedomain('daily').bounds.datetime_array[-1, -1]
                - get_dummy_dumping_frequency(self.time_))
        )

    def delete_yml_and_dump(self):
        # clean up dump files potentially created
        files = []
        if self.model.surfacelayer.dump_file is not None:
            files.extend(
                glob(os.sep.join([self.model.surfacelayer.output_directory,
                                  self.model.identifier + '*_dump.nc']))
            )
        if self.model.subsurface.dump_file is not None:
            files.extend(
                glob(os.sep.join([self.model.subsurface.output_directory,
                                  self.model.identifier + '*_dump.nc']))
            )
        if self.model.openwater.dump_file is not None:
            files.extend(
                glob(os.sep.join([self.model.openwater.output_directory,
                                  self.model.identifier + '*_dump.nc']))
            )
        if self.model.interface is not None:
            if self.model.interface.dump_file is not None:
                files.extend(
                    glob(os.sep.join([self.model.interface.output_directory,
                                      self.model.identifier + '*_dump.nc']))
                )
        files.extend(
            glob(os.sep.join([self.model.config_directory,
                              self.model.identifier + '*.yml']))
        )
        # convert dumps list to set to avoid potential duplicates
        for f in set(files):
            os.remove(f)


class TestModelSameTimeSameSpace(unittest.TestCase):
    # flag to specify that components are to run at same temporal resolution
    t = 'sync'
    # flag to specify that components are to run at same spatial resolution
    s = 'match'

    # expected final values for states/transfers after main run
    # (null initial conditions, no spinup run, 12 iterations)
    exp_states = {
        'surfacelayer': {
            'state_a': 12,
            'state_b': 24
        },
        'subsurface': {
            'state_a': 12,
            'state_b': 24
        },
        'openwater': {
            'state_a': 12
        }
    }
    exp_transfers = {
        'transfer_i': 564,
        'transfer_j': 762,
        'transfer_k': 1498,
        'transfer_l': 738,
        'transfer_m': 453,
        'transfer_n': 1926,
        'transfer_o': 645
    }

    def setUp(self):
        self.simulator = None

    def tearDown(self):
        if self.simulator is not None:
            self.simulator.delete_yml_and_dump()

    def test_init_spinup_simulate_resume(self):
        # generator of all possible component combinations
        # (i.e. full factorial design of experiment) as
        # tuple(surfacelayer kind, subsurface kind, openwater kind)
        # with 'c' for Component, 'd' for DataComponent, 'n' for NullComponent
        doe = ((sl, ss, ow)
               for sl in ('c', 'd', 'n')
               for ss in ('c', 'd', 'n')
               for ow in ('c', 'd', 'n'))

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind in doe:
            with self.subTest(surfacelayer=sl_kind,
                              subsurface=ss_kind,
                              openwater=ow_kind):
                # initialise, spinup, and run model
                simulator = Simulator(self.t, self.s, sl_kind, ss_kind, ow_kind)
                simulator.spinup_model()
                simulator.run_model()

                # store the last component states
                last_states_sl = deepcopy(simulator.model.surfacelayer.states)
                last_states_ss = deepcopy(simulator.model.subsurface.states)
                last_states_ow = deepcopy(simulator.model.openwater.states)

                # resume model
                simulator.resume_model()

                # check final state values are coherent
                self.assertTrue(
                    compare_states(last_states_sl,
                                   simulator.model.surfacelayer.states)
                )
                self.assertTrue(
                    compare_states(last_states_ss,
                                   simulator.model.subsurface.states)
                )
                self.assertTrue(
                    compare_states(last_states_ow,
                                   simulator.model.openwater.states)
                )

                # clean up
                simulator.delete_yml_and_dump()

    def test_init_simulate_check_final_states_transfers(self):
        doe = ((sl, ss, ow)
               for sl in ('c', 'd')
               for ss in ('c', 'd')
               for ow in ('c', 'd'))

        # loop through all possible combinations of components
        for sl_kind, ss_kind, ow_kind in doe:
            with self.subTest(surfacelayer=sl_kind,
                              subsurface=ss_kind,
                              openwater=ow_kind):

                # initialise, and run model
                simulator = Simulator(self.t, self.s, sl_kind, ss_kind, ow_kind)
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)

                # clean up
                simulator.delete_yml_and_dump()

    def test_init_simulate_various_sources(self):
        doe = ((sl, ss, ow)
               for sl in ('Python', 'Fortran', 'C')
               for ss in ('Python', 'Fortran', 'C')
               for ow in ('Python', 'Fortran', 'C'))

        # loop through all possible combinations of component sources
        for sl_src, ss_src, ow_src in doe:
            with self.subTest(surfacelayer=sl_src,
                              subsurface=ss_src,
                              openwater=ow_src):
                # initialise, and run model
                simulator = Simulator(self.t, self.s, 'c', 'c', 'c',
                                      {'surfacelayer': sl_src,
                                       'subsurface': ss_src,
                                       'openwater': ow_src})
                simulator.run_model()

                # check final state and transfer values
                self.check_final_conditions(simulator.model)

                # clean up
                simulator.delete_yml_and_dump()

    def test_in_session_vs_through_dump(self):
        # initialise a model, and spin it up
        simulator_1 = Simulator(self.t, self.s, 'c', 'c', 'c')
        simulator_1.spinup_model(cycles=1)

        # initialise another model
        simulator_2 = Simulator(self.t, self.s, 'c', 'c', 'c')

        # use dump of first model as initial conditions for second model
        simulator_2.model.surfacelayer.initialise_states_from_dump(
            os.sep.join([simulator_1.model.surfacelayer.output_directory,
                         simulator_1.model.surfacelayer.dump_file])
        )
        simulator_2.model.subsurface.initialise_states_from_dump(
            os.sep.join([simulator_1.model.subsurface.output_directory,
                         simulator_1.model.subsurface.dump_file])
        )
        simulator_2.model.openwater.initialise_states_from_dump(
            os.sep.join([simulator_1.model.openwater.output_directory,
                         simulator_1.model.openwater.dump_file])
        )

        simulator_2.model.initialise_transfers_from_dump(
            os.sep.join([simulator_1.model.interface.output_directory,
                         simulator_1.model.interface.dump_file])
        )

        # spin second model up
        simulator_2.spinup_model(cycles=1)

        # check final state and transfer values
        # (since simulate period is of 12 days, and each spinup cycle is
        #  of 6 days, and given that the driving data is constant for
        #  the 12-day period, the final conditions with spinup+spinup
        #  will be the same as with simulate without spinup)
        self.check_final_conditions(simulator_2.model)

    def check_final_conditions(self, model):
        # check components' final state values
        for comp in [model.surfacelayer,
                     model.subsurface,
                     model.openwater]:
            self.check_component_states(comp)

        # check final transfer values
        self.check_interface_transfers(model.interface)

    def check_component_states(self, component):
        cat = component.category
        # if component is "real", otherwise no states
        if not isinstance(component, cm4twc.DataComponent):
            for state in ['state_a', 'state_b']:
                if self.exp_states[cat].get(state) is None:
                    # some components feature only one state
                    continue
                # retrieve last state values
                arr = component.states[state][-1]
                # compare both min/max, as arrays are homogeneous
                try:
                    if isinstance(component, cm4twc.DataComponent):
                        # state value should remain at zero
                        self.assertEqual(np.amin(arr), 0)
                        self.assertEqual(np.amax(arr), 0)
                    else:
                        val = self.exp_states[cat][state]
                        self.assertEqual(np.amin(arr), val)
                        self.assertEqual(np.amax(arr), val)
                except AssertionError as e:
                    raise AssertionError(
                        "error for {}, {}".format(cat, state)
                    ) from e

    def check_interface_transfers(self, interface):
        for transfer in ['transfer_i', 'transfer_j', 'transfer_k',
                         'transfer_l', 'transfer_m', 'transfer_n',
                         'transfer_o']:
            arr = interface.transfers[transfer][
                'slices'][-1]
            # compare both min/max, as array should be homogeneous
            val = self.exp_transfers[transfer]
            try:
                self.assertAlmostEqual(np.amin(arr), val)
                self.assertAlmostEqual(np.amax(arr), val)
            except AssertionError as e:
                raise AssertionError(
                    "error for {}".format(transfer)) from e


class TestModelDiffTimeSameSpace(TestModelSameTimeSameSpace):
    # flag to specify that components are to run at different temporal resolutions
    t = 'async'
    # flag to specify that components are to run at same spatial resolution
    s = 'match'

    # expected final values for states/transfers after main run
    # (null initial conditions, no spinup run, 12 iterations)
    exp_states = {
        'surfacelayer': {
            'state_a': 12,
            'state_b': 24
        },
        'subsurface': {
            'state_a': 4,
            'state_b': 8
        },
        'openwater': {
            'state_a': 6
        }
    }
    exp_transfers = {
        'transfer_i': 115,
        'transfer_j': 112.5,
        'transfer_k': 145.5,
        'transfer_l': 100,
        'transfer_m': 102,
        'transfer_n': 328.5,
        'transfer_o': 112.5
    }


class TestModelSameTimeDiffSpace(TestModelSameTimeSameSpace):
    # flag to specify that components are to run at different spatial resolutions
    s = 'remap'


class TestModelDiffTimeDiffSpace(TestModelDiffTimeSameSpace):
    # flag to specify that components are to run at different spatial resolutions
    s = 'remap'


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeSameSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeDiffSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))

    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
