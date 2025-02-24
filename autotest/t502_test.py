import os
import shutil

import flopy
from flopy.mf6.modflow import mfgwfriv, mfgwfsto, mfgwfoc, mfgwfwel, mfgwfdrn
from flopy.mf6.modflow import mfims, mftdis, mfgwfic, mfgwfnpf, mfgwfdis, mfgwf
from flopy.mf6.modflow.mfsimulation import MFSimulation

out_dir = os.path.join("temp", "t502")
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.mkdir(out_dir)


def test_create_and_run_model():

    # names
    sim_name = "testsim"
    model_name = "testmodel"
    exe_name = "mf6"

    # set up simulation
    tdis_name = f"{sim_name}.tdis"
    sim = MFSimulation(
        sim_name=sim_name, version="mf6", exe_name=exe_name, sim_ws=out_dir
    )
    tdis_rc = [(6.0, 2, 1.0), (6.0, 3, 1.0)]
    tdis = mftdis.ModflowTdis(
        sim, time_units="DAYS", nper=2, perioddata=tdis_rc
    )

    # create model instance
    model = mfgwf.ModflowGwf(
        sim, modelname=model_name, model_nam_file=f"{model_name}.nam"
    )

    # create solution and add the model
    ims_package = mfims.ModflowIms(
        sim,
        print_option="ALL",
        complexity="SIMPLE",
        outer_hclose=0.00001,
        outer_maximum=50,
        under_relaxation="NONE",
        inner_maximum=30,
        inner_hclose=0.00001,
        linear_acceleration="CG",
        preconditioner_levels=7,
        preconditioner_drop_tolerance=0.01,
        number_orthogonalizations=2,
    )
    sim.register_ims_package(ims_package, [model_name])

    # add packages to model
    dis_package = mfgwfdis.ModflowGwfdis(
        model,
        length_units="FEET",
        nlay=1,
        nrow=1,
        ncol=10,
        delr=500.0,
        delc=500.0,
        top=100.0,
        botm=50.0,
        filename=f"{model_name}.dis",
    )
    ic_package = mfgwfic.ModflowGwfic(
        model,
        strt=[
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
        ],
        filename=f"{model_name}.ic",
    )
    npf_package = mfgwfnpf.ModflowGwfnpf(
        model, save_flows=True, icelltype=1, k=100.0
    )

    sto_package = mfgwfsto.ModflowGwfsto(
        model, save_flows=True, iconvert=1, ss=0.000001, sy=0.15
    )

    wel_package = mfgwfwel.ModflowGwfwel(
        model,
        print_input=True,
        print_flows=True,
        save_flows=True,
        maxbound=2,
        stress_period_data=[((0, 0, 4), -2000.0), ((0, 0, 7), -2.0)],
    )
    wel_package.stress_period_data.add_transient_key(1)
    wel_package.stress_period_data.set_data([((0, 0, 4), -200.0)], 1)

    drn_package = mfgwfdrn.ModflowGwfdrn(
        model,
        print_input=True,
        print_flows=True,
        save_flows=True,
        maxbound=1,
        stress_period_data=[((0, 0, 0), 80, 60.0)],
    )

    riv_package = mfgwfriv.ModflowGwfriv(
        model,
        print_input=True,
        print_flows=True,
        save_flows=True,
        maxbound=1,
        stress_period_data=[((0, 0, 9), 110, 90.0, 100.0)],
    )
    oc_package = mfgwfoc.ModflowGwfoc(
        model,
        budget_filerecord=[f"{model_name}.cbc"],
        head_filerecord=[f"{model_name}.hds"],
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )
    oc_package.saverecord.add_transient_key(1)
    oc_package.saverecord.set_data([("HEAD", "ALL"), ("BUDGET", "ALL")], 1)
    oc_package.printrecord.add_transient_key(1)
    oc_package.printrecord.set_data([("HEAD", "ALL"), ("BUDGET", "ALL")], 1)

    # write the simulation input files
    sim.write_simulation()

    # determine whether or not to run
    v = flopy.which(exe_name)
    run = True
    if v is None:
        run = False

    # run the simulation and look for output
    if run:
        sim.run_simulation()
        # head = sim.simulation_data.mfdata[(model_name, 'HDS', 'HEAD')]
        # print('HEAD: ', head)

    return


if __name__ == "__main__":
    test_create_and_run_model()
