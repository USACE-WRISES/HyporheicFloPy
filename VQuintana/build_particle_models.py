
import flopy
import numpy as np
import pathlib as pl

def build_particle_models(example_name, gwf):
    print(f"Building PRT model for {example_name}")

    # Instantiate the MODFLOW 6 PRT simulation object
    prtsim = flopy.mf6.MFSimulation(
        sim_name=prt_name, exe_name=md6_exe_path, version="mf6", sim_ws=prt_ws
    )

    # Instantiate the MODFLOW 6 temporal discretization package
    flopy.mf6.modflow.mftdis.ModflowTdis(
        prtsim,
        pname="tdis",
        time_units="DAYS",
        nper=nper,
        perioddata=[(perlen, nstp, tsmult)],
    )

    # Instantiate the MODFLOW 6 prt model
    prt = flopy.mf6.ModflowPrt(
        prtsim, modelname=prt_name, model_nam_file=f"{prt_name}.nam", save_flows=True
    )

    # Instantiate the MODFLOW 6 prt discretization package
    flopy.mf6.modflow.mfgwfdis.ModflowGwfdis(
        prt,
        pname="dis",
        nlay=len(botm),
        nrow=nrow,
        ncol=ncol,
        length_units="FEET",
        delr=cell_size_x,  # Cell width
        delc=cell_size_y,  # Cell height
        top=tops[0],
        botm=botm,
        idomain=idomain,    # List of dynamically calculated active and inactive cells in the model domain
        xorigin=xorigin,  # Assign dynamically calculated xorigin
        yorigin=yorigin   # Assign dynamically calculated yorigin
    )

    # Instantiate the MODFLOW 6 prt model input package.
    # Assign a different zone number to active cells, well cells, and river cells.
    # # This makes it easier to determine where particles terminate.
    # izone = np.zeros((len(botm), nrow, ncol), dtype=int)
    # for l, r, c in gwf.modelgrid.get_lrc(nodes["well"]):
    #     izone[l, r, c] = 1
    # for l, r, c in gwf.modelgrid.get_lrc(nodes["river"]):
    #     izone[l, r, c] = 2
    flopy.mf6.ModflowPrtmip(prt, pname="mip", porosity= porosity) #izone=izone)

    # Instantiate the MODFLOW 6 prt particle release point (prp) package for example 1A,
    # first converting MP7 particle release configurations to PRT format.
    releasepts_1a = list(mp7_particle_data_1a.to_prp(prt.modelgrid))
    flopy.mf6.ModflowPrtprp(
        prt,
        pname="prp1a",
        filename=f"{prt_name}_1a.prp",
        nreleasepts=len(releasepts_1a),
        packagedata=releasepts_1a,
        perioddata={0: ["FIRST"]},
        exit_solve_tolerance=1e-5,
    )

    # # Instantiate the MODFLOW 6 prt particle release point (prp) package for example 1B,
    # # first converting MP7 particle release configurations to PRT format.
    # releasepts_1b = list(mp7_particle_data_1b.to_prp(prt.modelgrid))
    # flopy.mf6.ModflowPrtprp(
    #     prt,
    #     pname="prp1b",
    #     filename=f"{prt_name}_1b.prp",
    #     nreleasepts=len(releasepts_1b),
    #     packagedata=releasepts_1b,
    #     perioddata={0: ["FIRST"]},
    #     exit_solve_tolerance=1e-10,
    # )

    # Instantiate the MODFLOW 6 prt output control package
    budget_record = [budgetfile_prt]
    track_record = [trackfile_prt]
    trackcsv_record = [trackcsvfile_prt]
    
    #tracktimes = [round(float(i), 2) for i in range(0, 72000, 1000)]  # Convert to non-integer floats and round
    tracktimes = [float(i) for i in range(0, 72000, 1000)]
    ntracktimes = len(tracktimes) 
    
    # Debug print to check tracktimes and ntracktimes
    print("Track times:", tracktimes)
    print("Data type of track times:", type(tracktimes))
    print("Number of track times:", ntracktimes)
    print("Data type of Number of track times:", type(ntracktimes))

    # Dynamically generate file names
    budget_filerecord_prt = [budgetfile_prt]
    track_filerecord_prt = [trackfile_prt]

    # flopy.mf6.ModflowPrtoc(
    #     prt,
    #     pname="oc",
    #     budget_filerecord=budget_record,
    #     track_filerecord=track_record,
    #     trackcsv_filerecord=trackcsv_record,
    #     ntracktimes= float(ntracktimes),
    #     tracktimes=[(t,) for t in tracktimes],
    #     saverecord = [("HEAD", "ALL"), ("BUDGET", "ALL")],
    #     printrecord = [("HEAD", "LAST")]
    # )

    # Debug prints to check if the paths exist
    head_path = gwf_ws / headfile
    budget_path = gwf_ws / budgetfile
    print("Head file path:", head_path)
    print("Budget file path:", budget_path)
    print("Head file exists:", head_path.exists())  
    print("Budget file exists:", budget_path.exists())

    # Instantiate the MODFLOW 6 prt flow model interface
    pd = [
        ("GWFHEAD", pl.Path(f"../{gwf_ws.name}/{headfile}")),
        ("GWFBUDGET", pl.Path(f"../{gwf_ws.name}/{budgetfile}")),
    ]
    
    flopy.mf6.ModflowPrtfmi(prt, packagedata=pd)

    # Create an explicit model solution (EMS) for the MODFLOW 6 prt model
    ems = flopy.mf6.ModflowEms(
        prtsim,
        pname="ems",
        filename=f"{prt_name}.ems",
    )
    prtsim.register_solution_package(ems, [prt.name])

    print(f"Building PRT model for {example_name}")
    
    # Instantiate the MODPATH 7 object
    mp7 = flopy.modpath.Modpath7(
        modelname=mp7_name,
        flowmodel=gwf,
        exe_name=md7_exe_path,
        model_ws=mp7_ws,
        budgetfilename=budget_path,
        headfilename=head_path,
    )

    # Instantiate the MODPATH 7 basic data
    flopy.modpath.Modpath7Bas(mp7, porosity=porosity, defaultiface={"RCH": 6, "EVT": 6})

    # Instantiate the MODPATH 7 particle groups
    pg1a = flopy.modpath.ParticleGroup(
        particlegroupname="PG1A",
        particledata=mp7_particle_data_1a,
        filename=sim_name + "a.sloc",
    )
    # pg1b = flopy.modpath.ParticleGroupLRCTemplate(
    #     particlegroupname="PG1B",
    #     particledata=mp7_particle_data_1b,
    #     filename=sim_name + "b.sloc",
    # )

    # Instantiate the MODPATH 7 simulation
    mpsim = flopy.modpath.Modpath7Sim(
        mp7,
        simulationtype="combined",
        trackingdirection="forward",
        weaksinkoption="pass_through",
        weaksourceoption="pass_through",
        budgetoutputoption="summary",
        referencetime=[0, 0, 0.0],
        stoptimeoption="extend",
        timepointdata=[500, 1000.0],
        zonedataoption="on",
        zones=izone,
        particlegroups=[pg1a],
    )
    return prtsim, prt, mpsim, mp7

print("✅ build_particle_models function saved successfully.")
