
import flopy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LightSource

def load_head():
    # Assuming you have a head file to load
    head_file = gwf_ws / headfile
    head_obj = flopy.utils.HeadFile(head_file)
    head = head_obj.get_data()
    return head

def plot_gwf_all(gwfsim):
    # get gwf model
    gwf = gwfsim.get_model(gwf_name)
    head = load_head()

    # Load the discretization file to access model grid information
    dis = gwf.get_package("DIS")
    nlay, nrow, ncol = dis.nlay.data, dis.nrow.data, dis.ncol.data

    # Load the idomain array to identify active cells
    idomain = dis.idomain.array # No results will be visible otherwise

    # Choose the layer you want to plot, e.g., the first layer (layer 0)
    layer_to_plot = 1  # You can change this to any other layer (0-based index)

    # Extract the groundwater head for the specified layer (nrow, ncol)
    head_layer = head[layer_to_plot, :, :]

    # Mask the inactive cells in the head_layer array
    head_layer_masked = np.ma.masked_where(idomain[layer_to_plot, :, :] == 0, head_layer)

    # Plot the groundwater head for the chosen layer
    plt.figure(figsize=(10, 6))
    plt.imshow(head_layer_masked, cmap='viridis', origin='lower', extent=[0, ncol, 0, nrow])
    plt.colorbar(label='Groundwater Head (m)')
    plt.title(f'Groundwater Head at Layer {layer_to_plot + 1}')
    plt.xlabel('Column')
    plt.ylabel('Row')
    plt.show()

    # Load the surface elevation data
    surface_elevation = dis.top.array

    # Choose the layers you want to plot, e.g., the first layer (layer 0) and the last layer
    layer_to_plot_first = 0  # First layer (0-based index)
    layer_to_plot_last = nlay - 1  # Last layer (0-based index)

    # Extract the groundwater head for the specified layers (nrow, ncol)
    head_layer_first = head[layer_to_plot_first, :, :]
    head_layer_last = head[layer_to_plot_last, :, :]

    # Mask the inactive cells in the head_layer arrays
    head_layer_first_masked = np.ma.masked_where(idomain[layer_to_plot_first, :, :] == 0, head_layer_first)
    head_layer_last_masked = np.ma.masked_where(idomain[layer_to_plot_last, :, :] == 0, head_layer_last)

    # Plot the surface elevation for active cells and overlay groundwater head contours
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))

    # Plot for the first layer
    top_active_first = np.ma.masked_where(idomain[layer_to_plot_first, :, :] == 0, surface_elevation)
    im1 = axs[0].imshow(top_active_first, cmap="terrain", interpolation="nearest", origin="lower",
                        extent=[0, ncol, 0, nrow], alpha=0.7)
    plt.colorbar(im1, ax=axs[0], label='Surface Elevation (m)')

    # Check if the minimum and maximum values are different before creating contour levels
    if head_layer_first_masked.min() != head_layer_first_masked.max():
        contour_first = axs[0].contour(head_layer_first_masked, levels=np.linspace(head_layer_first_masked.min(), head_layer_first_masked.max(), 10), colors='blue', extent=[0, ncol, 0, nrow])
        axs[0].clabel(contour_first, inline=True, fontsize=8, fmt='%1.1f')
    axs[0].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer_to_plot_first + 1}')
    axs[0].set_xlabel('Column')
    axs[0].set_ylabel('Row')

    # Plot for the last layer
    top_active_last = np.ma.masked_where(idomain[layer_to_plot_last, :, :] == 0, surface_elevation)
    im2 = axs[1].imshow(top_active_last, cmap="terrain", interpolation="nearest", origin="lower",
                        extent=[0, ncol, 0, nrow], alpha=0.7)
    plt.colorbar(im2, ax=axs[1], label='Surface Elevation (m)')

    # Check if the minimum and maximum values are different before creating contour levels
    if head_layer_last_masked.min() != head_layer_last_masked.max():
        contour_last = axs[1].contour(head_layer_last_masked, levels=np.linspace(head_layer_last_masked.min(), head_layer_last_masked.max(), 10), colors='blue', extent=[0, ncol, 0, nrow])
        axs[1].clabel(contour_last, inline=True, fontsize=8, fmt='%1.1f')
    axs[1].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer_to_plot_last + 1}')
    axs[1].set_xlabel('Column')
    axs[1].set_ylabel('Row')

    plt.tight_layout()
    plt.show()

    #---------------------- Zoom In to idomain ------------------------#
    # Choose the layers you want to plot
    layers_to_plot = [1, 19, 39]  # 1st, 20th, and 40th layers (0-based index)

    # Extract the groundwater head for the specified layers (nrow, ncol)
    head_layers = [head[layer, :, :] for layer in layers_to_plot]

    # Mask the inactive cells in the head_layer arrays
    head_layers_masked = [np.ma.masked_where(idomain[layer, :, :] == 0, head_layers[i]) for i, layer in enumerate(layers_to_plot)]

    # Determine the extent of the active cells
    active_cells = np.any(idomain, axis=0)
    active_rows, active_cols = np.where(active_cells)
    row_min, row_max = active_rows.min(), active_rows.max()
    col_min, col_max = active_cols.min(), active_cols.max()

    # Define the extent for the plots
    extent = [col_min, col_max + 1, row_min, row_max + 1]

    # Plot the surface elevation for active cells and overlay groundwater head contours
    fig, axs = plt.subplots(3, 1, figsize=(10, 30))

    for i, layer in enumerate(layers_to_plot):
        # Plot for each layer
        top_active = np.ma.masked_where(idomain[layer, :, :] == 0, surface_elevation)
        im = axs[i].imshow(top_active[row_min:row_max+1, col_min:col_max+1], cmap="terrain", interpolation="nearest", origin="lower",
                           extent=extent, alpha=0.7)
        plt.colorbar(im, ax=axs[i], label='Surface Elevation (m)')
        contour = axs[i].contour(head_layers_masked[i][row_min:row_max+1, col_min:col_max+1], levels=np.linspace(head_layers_masked[i].min(), head_layers_masked[i].max(), 10), colors='blue', extent=extent)
        axs[i].clabel(contour, inline=True, fontsize=8, fmt='%1.1f')
        axs[i].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer + 1}')
        axs[i].set_xlabel('Column')
        axs[i].set_ylabel('Row')

    plt.tight_layout()
    plt.show()

    #---------------------- 3D Plot of the Model ------------------------#
    top = dis.top.array
    botm = dis.botm.array
    idomain = dis.idomain.array  # Assuming idomain is part of the dis object

    # Combine top and botm to get the elevation data for all layers
    elevation_data = np.concatenate(([top], botm), axis=0)

    # Get the number of rows and columns
    nrows, ncols = top.shape

    # Layer to plot for terrain
    terrain_layer = 0

    # Create a meshgrid for x and y coordinates
    x = np.linspace(0, ncols - 1, ncols)
    y = np.linspace(0, nrows - 1, nrows)
    x, y = np.meshgrid(x, y)

    # Mask the elevation data using the idomain array
    #z = np.ma.masked_where(idomain[terrain_layer, :, :] == 0, elevation_data[terrain_layer, :, :])

    # Set up plot
    fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

    # Light source for hillshading
    ls = LightSource(270, 45)

    # Plot the masked elevation data
    z = elevation_data[terrain_layer, :, :]
    rgb = ls.shade(z, cmap=cm.gist_earth, vert_exag=0.1, blend_mode='soft')
    surf = ax.plot_surface(x, y, z, rstride=1, cstride=1, facecolors=rgb,
                        linewidth=0, antialiased=False, shade=False)

    # Set plot labels and title
    ax.set_title('3D Terrain Elevation')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    ax.set_zlabel('Elevation (ft)')

    plt.show()

print("✅ plot_gwf_all function saved successfully.")
