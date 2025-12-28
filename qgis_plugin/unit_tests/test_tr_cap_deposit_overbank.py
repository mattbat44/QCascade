import os
import sys

import numpy as np

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sedimentary_system import SedimentarySystem


class ReachDataStub:
    def __init__(self, n_reaches):
        self.n_reaches = n_reaches
        self.slope = np.zeros(n_reaches)
        self.wac = np.ones(n_reaches)
        self.wac_bf = None
        self.el_fn = np.zeros(n_reaches)
        self.el_tn = np.zeros(n_reaches)


def test_tr_cap_deposit_overbank_respects_capacity_and_stratigraphy():
    psi = np.array([-1.0, 0.0])
    reach_data = ReachDataStub(n_reaches=1)
    system = SedimentarySystem(reach_data, {"outlet": 0}, timescale=1, ts_length=1, save_dep_layer="never", psi=psi)
    system.initialize_storing_matrices()

    V_dep2act = np.array([
        [1.0, 0.6, 0.2],
        [1.0, 0.4, 0.6],
    ])
    V_dep = np.array([[1.0, 0.1, 0.1]])
    tr_cap_overbank = np.array([0.7, 0.5])

    V_dep2act_new, V_dep_out, V_overbank_dep = system.tr_cap_deposit_overbank(
        V_dep2act, V_dep, tr_cap_overbank, roundpar=np.nan
    )

    mobilized = system.sediments(V_dep2act_new).sum(axis=0)
    np.testing.assert_allclose(mobilized, tr_cap_overbank)

    before_total = system.sediments(V_dep2act).sum() + system.sediments(V_dep).sum()
    after_total = system.sediments(V_dep2act_new).sum() + system.sediments(V_dep_out).sum()
    np.testing.assert_allclose(after_total, before_total)

    assert np.all(system.provenance(V_dep_out) == 1)
    np.testing.assert_allclose(system.sediments(V_overbank_dep).sum(axis=0), np.array([0.3, 0.3]))


def test_compute_mobilised_volumes_applies_overbank_capacity():
    psi = np.array([-1.0, 0.0])
    reach_data = ReachDataStub(n_reaches=1)
    system = SedimentarySystem(reach_data, {"outlet": 0}, timescale=1, ts_length=1, save_dep_layer="never", psi=psi)
    system.initialize_storing_matrices()

    system.eros_max_vol = np.array([[10.0]])

    V_dep = np.array([[0.0, 1.0, 1.0]])
    tr_cap_per_s = np.array([2.0, 2.0])  # large capacity without overbank
    tr_cap_overbank = np.array([0.3, 0.4])

    V_mob, _, V_dep_new = system.compute_mobilised_volumes(
        V_dep, tr_cap_per_s, n=0, t=0, roundpar=np.nan, passing_cascades=None, tr_cap_overbank=tr_cap_overbank
    )

    mobilized = system.sediments(V_mob).sum(axis=0)
    np.testing.assert_allclose(mobilized, tr_cap_overbank)

    before_total = system.sediments(V_dep).sum()
    after_total = system.sediments(V_dep_new).sum() + system.sediments(V_mob).sum()
    np.testing.assert_allclose(after_total, before_total)

    np.testing.assert_allclose(system.overbank_dep[0, 0, :], np.array([0.7, 0.6]))
