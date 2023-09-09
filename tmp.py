import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import math


# Create a custom function for displaying information based on coordinates
def custom_display_coords(x, y):
    message = None

    if x is not None and y is not None:
        for lon, lat in coordinates:
            # Calculate the distance between the cursor and the dot
            distance = math.sqrt((x - lon) ** 2 + (y - lat) ** 2)
            if distance < 10:
                message = f"Close to dot: Lon={lon:.2f}, Lat={lat:.2f}"
                break

    if message is None:
        return f"Lon: {x:.2f}, Lat: {y:.2f}"
    else:
        return message


# Create a Tkinter window
root = tk.Tk()
root.title("World Map")

# Create a frame to hold the map
map_frame = tk.Frame(root)
map_frame.pack()


# Create a function to update the map with given coordinates and display function
def update_map(coordinates, display_func):
    # Create a Cartopy map
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Plot the world map
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, edgecolor='black')
    ax.add_feature(cfeature.OCEAN, color='lightblue')
    ax.add_feature(cfeature.LAKES, edgecolor='black')
    ax.add_feature(cfeature.RIVERS)

    # Plot dots on the map using input coordinates
    for lon, lat in coordinates:
        ax.plot(lon, lat, 'ro', markersize=6, transform=ccrs.PlateCarree())

    # Create a Tkinter canvas for embedding the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master=map_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)

    # Create a label to display coordinates or messages at the bottom of the window
    coord_label = tk.Label(root, text="", padx=10, pady=5)
    coord_label.pack(side=tk.BOTTOM)

    # Create a function to update the coordinates label
    def display_coords(event):
        x, y = event.xdata, event.ydata
        coord_label.config(text=display_func(x, y))

    # Connect the hover event to display_coords function
    canvas.mpl_connect('motion_notify_event', display_coords)


# Example input array of coordinates
coordinates = [(0, 0), (40, 30), (-60, -20), (120, 45)]

# Call the update_map function with coordinates and custom display function
update_map(coordinates, custom_display_coords)

# Run the Tkinter main loop
root.mainloop()