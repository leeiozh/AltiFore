import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from suncalc import get_position
from numpy import pi
import datetime


def update_elevation(event):
    selected_hour = int(slider.get() / 60)  # Get the selected hour from the slider
    selected_min = int(slider.get() - 60 * selected_hour)

    if selected_hour == 24:
        selected_hour = 23
        selected_min = 59
    selected_time = datetime.datetime(2023, 9, 18, int(selected_hour), int(selected_min))  # Create a datetime object
    sun_position = get_position(selected_time, latitude, longitude)
    elevation = sun_position['altitude'] * 180 / pi
    elevation_label.config(text=f"Sun Elevation: {elevation:.2f} degrees")
    slider_label.config(text=f"Selected time: {selected_hour:2d}:{selected_min:2d}")
    sun_label.place(x=slider.get() / 24 / 60 * 270, y=30)


def slide_left(event):
    current_value = slider.get()
    if current_value > 0:
        slider.set(current_value - 5)
        update_elevation(event)


def slide_right(event):
    current_value = slider.get()
    if current_value < 24 * 60:
        slider.set(current_value + 5)
        update_elevation(event)


# Create the main window
window = tk.Tk()
window.title("Sun Elevation Calculator")

# Latitude and longitude for your location (update with your coordinates)
latitude = 55  # Example: New York City
longitude = 37  # Example: New York City

# Create a label for the slider
slider_label = ttk.Label(window, text="Select Time (0 AM to 12 PM):")
slider_label.pack(padx=10, pady=10)

# Create a slider widget
slider = ttk.Scale(window, from_=0, to=24 * 60, length=300, orient="horizontal")
slider.pack(padx=10, pady=10)
slider_width = slider.winfo_width()

# Create a label to display the sun elevation
elevation_label = ttk.Label(window, text="Sun Elevation: 0.00 degrees")
elevation_label.pack(padx=10, pady=10)

sun_image = ImageTk.PhotoImage(Image.open("/home/leeiozh/ocean/AltiFore/sun.png").resize((50, 50)))
sun_label = ttk.Label(window, image=sun_image, background="")
sun_label.pack()

# Bind the slider to the update function
slider.bind("<Motion>", update_elevation)
window.bind("<Left>", slide_left)
window.bind("<Right>", slide_right)

# Start the Tkinter main loop
window.mainloop()
