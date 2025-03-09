
import flopy
import numpy as np

def build_gwf_model(
        example_name, 
        gwf_name, gwf_ws, 
        md6_exe_path, 
        nrow, 
        ncol, 
        cell_size_x, 
        cell_size_y, 
        tops, 
        botm, 
        xorigin, 
        yorigin, 
        idomain, 
        nper,
        perlen,
        nstp,
        tsmult,
        kh, 
        kv, 
        bed_elevation, 
        chd_data_converted, 
        head_filerecord, 
        budget_filerecord):
    
    print(f"Building GWF model for {example_name}")

    # Instantiate the MODFLOW 6 GWF simulation object
    gwfsim = flopy.mf6.MFSimulation(
        sim_name=gwf_name, exe_name=md6_exe_path, sim_ws=gwf_ws
    )

    # Instantiate the MODFLOW 6 temporal discretization package
    flopy.mf6.modflow.mftdis.ModflowTdis(
        gwfsim,
        pname="tdis",
        time_units="DAYS",
        nper=nper,
        perioddata=[(perlen, nstp, tsmult)],
    )

    # Instantiate the MODFLOW 6 gwf (groundwater-flow) model
    gwf = flopy.mf6.ModflowGwf(
        gwfsim, modelname=gwf_name, model_nam_file=f"{gwf_name}.nam", save_flows=True
    )

    # Instantiate the MODFLOW 6 gwf discretization package
    flopy.mf6.modflow.mfgwfdis.ModflowGwfdis(
        gwf,
        nlay=len(botm),  # Number of layers (based on `botm` list length)
        nrow=nrow,       # Number of rows in the grid
        ncol=ncol,       # Number of columns in the grid
        delr=cell_size_x,  # Cell width
        delc=cell_size_y,  # Cell height
        top=tops[0],       # List of dynamically calculated top elevation of the first layer
        botm=botm,          # List of bottom elevations for all layers
        idomain=idomain,    # List of dynamically calculated active and inactive cells in the model domain
        xorigin=xorigin,  # Assign dynamically calculated xorigin
        yorigin=yorigin   # Assign dynamically calculated yorigin
    )
    
    # Add initial conditions (IC package)
    strt_array = np.full((len(botm), nrow, ncol), bed_elevation)

    # Instantiate the MODFLOW 6 gwf initial conditions package
    flopy.mf6.modflow.mfgwfic.ModflowGwfic(gwf, pname="ic", strt= strt_array)
    
    # Instantiate the MODFLOW 6 gwf node property flow package
    flopy.mf6.modflow.mfgwfnpf.ModflowGwfnpf(
        gwf,
        pname="npf",
        icelltype= 2,
        k=kh,
        k33=kv,
        save_flows=True,
        save_saturation=True,
        save_specific_discharge=True,
    )

    # Create an iterative model solution (IMS) for the MODFLOW 6 gwf model
    flopy.mf6.ModflowIms(
        gwfsim,
        print_option="SUMMARY",
        outer_dvclose=1e-4,  # Increase convergence criteria for outer iterations
        outer_maximum=200,  # Increase maximum number of outer iterations
        under_relaxation="NONE",
        inner_maximum=500,  # Increase maximum number of inner iterations
        inner_dvclose=1e-4,  # Increase convergence criteria for inner iterations
        rcloserecord=1e-4,  # Increase residual convergence criteria
        linear_acceleration="BICGSTAB",  # Switch to Bi-Conjugate Gradient Stabilized method
        scaling_method="NONE",
        reordering_method="NONE",
        relaxation_factor=0.97,  # Adjust relaxation factor
    )

    # Assign CHD Package to the model if there are valid unique boundary cells
    if not chd_data_converted:
        print("❌ No CHD boundary cells assigned. Please check the input data and conditions.")
    else:
        # Format the CHD values to ensure they are not in scientific notation
        formatted_chd_data = [
            [item[0], item[1], item[2], float(f"{item[3]:.2f}")]
            for item in chd_data_converted
        ]
    
        # Assuming 'gwf' is your groundwater flow model instance
        flopy.mf6.ModflowGwfchd(
            gwf,
            maxbound=len(formatted_chd_data),  # Set to actual assigned CHD cells
            stress_period_data={0: formatted_chd_data},  # Apply the boundary conditions in stress period 0
            pname="CHD",
            save_flows=True,
            filename=f"{gwf_name}.chd"
        )

        print(f"✅ Assigned {len(formatted_chd_data)} unique CHD boundary cells.")

    # Instantiate the MODFLOW 6 prt output control package
    saverecord = [("HEAD", "ALL"), ("BUDGET", "ALL")]
    printrecord = [("HEAD", "LAST")]
    flopy.mf6.ModflowGwfoc(
        gwf,
        saverecord=saverecord,
        head_filerecord=head_filerecord,
        budget_filerecord=budget_filerecord,
        printrecord=printrecord,
    )
    return gwfsim, gwf

print("✅ build_gwf_model function saved successfully.")
