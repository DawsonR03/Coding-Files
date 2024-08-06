import time
from unittest.mock import Mock
from tkinter import Tk, Label, Entry, Button, StringVar, Toplevel, messagebox, Listbox, Scrollbar, Frame, filedialog
from threading import Thread, Event
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import csv
import logging
import sys
from queue import Queue
from datetime import datetime

# Mock libraries for testing on Windows or non-Raspberry Pi environments
if sys.platform == "win32" or sys.platform.startswith('linux'):
    from unittest.mock import Mock

    class MockGPIO:
        BCM = Mock()
        OUT = Mock()
        HIGH = Mock()
        LOW = Mock()

        def setmode(self, mode):
            pass

        def setup(self, pin, mode):
            pass

        def output(self, pin, state):
            pass

        def cleanup(self):
            pass

    GPIO = MockGPIO()

    class MockSPI:
        def __init__(self):
            pass

        def open(self, bus, device):
            pass

        def xfer2(self, data):
            return [0, 0]

    spidev = Mock()
    spidev.SpiDev = MockSPI

    class MockSMBus:
        def __init__(self, bus):
            pass

        def write_byte_data(self, addr, reg, value):
            pass

        def read_i2c_block_data(self, addr, reg, length):
            return [0] * length

    smbus2 = Mock()
    smbus2.SMBus = MockSMBus

    HX711 = Mock()
    ADXL345 = Mock()
else:
    import RPi.GPIO as GPIO
    import spidev
    import smbus2
    from hx711 import HX711
    from adafruit_adxl34x import ADXL345

# Initialize logging
logging.basicConfig(filename='system_log.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Initialize I2C bus for ADXL345 accelerometer
bus = smbus2.SMBus(1)
ADXL345_ADDRESS = 0x53
ADXL345_POWER_CTL = 0x2D
ADXL345_DATA_FORMAT = 0x31
ADXL345_DATAX0 = 0x32

# Initialize SPI for MAX6675 thermocouple
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 5000

# Initialize HX711 for strain gauge
hx711 = HX711(dout_pin=5, pd_sck_pin=6)

# GPIO setup for motor controllers (example)
MOTOR_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_PIN, GPIO.OUT)

# Event to control the stop of data collection and plotting
stop_event = Event()

# Queue for communication between threads
data_queue = Queue()

# Calibration values
hx711_calibration = 1.0
adxl345_calibration = 1.0
max6675_calibration = 1.0

# User authentication credentials (hardcoded for simplicity)
USERNAME = "admin"
PASSWORD = "1234"

# Data storage for plotting
plot_data_storage = []

def init_adxl345():
    try:
        bus.write_byte_data(ADXL345_ADDRESS, ADXL345_POWER_CTL, 0x08)
        bus.write_byte_data(ADXL345_ADDRESS, ADXL345_DATA_FORMAT, 0x0B)
        logging.info("ADXL345 initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing ADXL345: {e}")

def read_adxl345():
    try:
        data = [0, 128, 0, 128, 0, 128]  # Mock data to provide more realistic values
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        z = data[4] | (data[5] << 8)
        x = (x - 32768) * adxl345_calibration  # Adjust using calibration
        y = (y - 32768) * adxl345_calibration  # Adjust using calibration
        z = (z - 32768) * adxl345_calibration  # Adjust using calibration
        logging.info(f"ADXL345 read: x={x}, y={y}, z={z}")
        return x, y, z
    except Exception as e:
        logging.error(f"Error reading ADXL345: {e}")
        return None, None, None

def read_max6675():
    try:
        raw = [0x00, 0x40]  # Mock data to provide more realistic values
        value = (raw[0] << 8) | raw[1]
        temperature = ((value >> 3) * 0.25) * max6675_calibration  # Adjust using calibration
        logging.info(f"MAX6675 read: temperature={temperature}")
        return temperature
    except Exception as e:
        logging.error(f"Error reading MAX6675: {e}")
        return None

def read_hx711():
    try:
        weight = 1000 * hx711_calibration  # Mock data to provide more realistic values
        logging.info(f"HX711 read: weight={weight}")
        return weight
    except Exception as e:
        logging.error(f"Error reading HX711: {e}")
        return None

def data_collection_thread(sensor_name, airspeed, acceleration, g_force, data_queue, stop_event, gui_elements, output_listbox):
    init_adxl345()

    while not stop_event.is_set():
        x_accel, y_accel, z_accel = read_adxl345()
        temperature = read_max6675()
        force = read_hx711()
        timestamp = datetime.now()

        if x_accel is not None and y_accel is not None and z_accel is not None:
            data = {
                "sensor_name": sensor_name,
                "x_accel": x_accel,
                "y_accel": y_accel,
                "z_accel": z_accel,
                "temperature": temperature,
                "force": force,
                "timestamp": timestamp
            }
            plot_data_storage.append(data)
            data_queue.put(data)
            logging.info(f"Logged data: {data}")

            try:
                gui_elements[f'x_accel_{sensor_name}'].set(f"X-Accel: {x_accel}")
                gui_elements[f'y_accel_{sensor_name}'].set(f"Y-Accel: {y_accel}")
                gui_elements[f'z_accel_{sensor_name}'].set(f"Z-Accel: {z_accel}")
                gui_elements[f'temperature_{sensor_name}'].set(f"Temperature: {temperature}")
                gui_elements[f'force_{sensor_name}'].set(f"Force: {force}")

                output_listbox.insert('end', f"{sensor_name} - X-Accel: {x_accel}, Y-Accel: {y_accel}, Z-Accel: {z_accel}, "
                                            f"Temp: {temperature}, Force: {force}, Timestamp: {timestamp.strftime('%H:%M:%S')}")
                output_listbox.yview('end')
            except:
                pass  # Handle any exceptions that occur during Listbox updates

        time.sleep(1)

def animate(i, fig, ax, x_data, y_data, z_data, temp_data, force_data, gui_elements, acceleration, output_listbox):
    if stop_event.is_set():
        plt.close(fig)
        return

    while not data_queue.empty():
        data = data_queue.get()
        x_data.append(data["x_accel"])
        y_data.append(data["y_accel"])
        z_data.append(data["z_accel"])
        temp_data.append(data["temperature"])
        force_data.append(data["force"])

        ax[0].clear()
        ax[1].clear()
        ax[0].plot(x_data, label='X-Accel')
        ax[0].plot(y_data, label='Y-Accel')
        ax[0].plot(z_data, label='Z-Accel')
        ax[0].set_title('Accelerometer Data')
        ax[0].legend()

        ax[1].plot(temp_data, label='Temperature')
        ax[1].plot(force_data, label='Force')
        ax[1].set_title('Temperature and Force Data')
        ax[1].legend()

        plt.tight_layout()

def start_data_collection(airspeed, acceleration, g_force, gui_elements, output_listbox):
    global stop_event, plot_data_storage
    stop_event.clear()  # Clear the stop_event to allow data collection to start
    plot_data_storage = []  # Clear previous data
    airspeed = float(airspeed)
    acceleration = float(acceleration)
    g_force = float(g_force)

    sensor_names = ["HX711-Guage Sensor", "ADXL345-Accelerometer Sensor", "MAX6675-Thermocouple Sensor"]

    for sensor_name in sensor_names:
        Thread(target=data_collection_thread, args=(sensor_name, airspeed, acceleration, g_force, data_queue, stop_event, gui_elements, output_listbox)).start()

def plot_data(gui_elements, output_listbox):
    fig, ax = plt.subplots(2, 1)
    x_data, y_data, z_data, temp_data, force_data = [], [], [], [], []

    ani = animation.FuncAnimation(fig, animate, fargs=(fig, ax, x_data, y_data, z_data, temp_data, force_data, gui_elements, float(gui_elements['acceleration'].get()), output_listbox), interval=1000, save_count=100)
    plt.show()

def create_bar_graph():
    avg_data = {sensor_name: {'x_accel': 0, 'y_accel': 0, 'z_accel': 0, 'temperature': 0, 'force': 0, 'count': 0} for sensor_name in ["HX711-Guage Sensor", "ADXL345-Accelerometer Sensor", "MAX6675-Thermocouple Sensor"]}

    for data in plot_data_storage:
        sensor_name = data['sensor_name']
        avg_data[sensor_name]['x_accel'] += data['x_accel']
        avg_data[sensor_name]['y_accel'] += data['y_accel']
        avg_data[sensor_name]['z_accel'] += data['z_accel']
        avg_data[sensor_name]['temperature'] += data['temperature']
        avg_data[sensor_name]['force'] += data['force']
        avg_data[sensor_name]['count'] += 1

    labels = ['x_accel', 'y_accel', 'z_accel', 'temperature', 'force']
    sensor_labels = ['HX711-Guage Sensor', 'ADXL345-Accelerometer Sensor', 'MAX6675-Thermocouple Sensor']

    avg_values = []
    for sensor_name in sensor_labels:
        count = avg_data[sensor_name]['count']
        if count > 0:
            avg_values.append([avg_data[sensor_name][metric] / count for metric in labels])

    avg_values = np.array(avg_values).T

    fig, ax = plt.subplots()
    bar_width = 0.2
    index = np.arange(len(labels))

    for i, sensor in enumerate(sensor_labels):
        ax.bar(index + i * bar_width, avg_values[:, i], bar_width, label=sensor)

    ax.set_xlabel('Metrics')
    ax.set_ylabel('Average Values')
    ax.set_title('Average Sensor Readings')
    ax.set_xticks(index + bar_width)
    ax.set_xticklabels(['X-Accel', 'Y-Accel', 'Z-Accel', 'Temperature', 'Force'])
    ax.legend()

    plt.tight_layout()
    plt.show()

def create_heat_map():
    timestamps = [data['timestamp'] for data in plot_data_storage]
    sensors_data = {sensor_name: {'x_accel': [], 'y_accel': [], 'z_accel': [], 'temperature': [], 'force': []} for sensor_name in ["HX711-Guage Sensor", "ADXL345-Accelerometer Sensor", "MAX6675-Thermocouple Sensor"]}

    for data in plot_data_storage:
        sensor_name = data['sensor_name']
        sensors_data[sensor_name]['x_accel'].append(data['x_accel'])
        sensors_data[sensor_name]['y_accel'].append(data['y_accel'])
        sensors_data[sensor_name]['z_accel'].append(data['z_accel'])
        sensors_data[sensor_name]['temperature'].append(data['temperature'])
        sensors_data[sensor_name]['force'].append(data['force'])

    min_length = min(len(timestamps), len(sensors_data['HX711-Guage Sensor']['x_accel']), len(sensors_data['ADXL345-Accelerometer Sensor']['x_accel']), len(sensors_data['MAX6675-Thermocouple Sensor']['x_accel']))

    timestamps = timestamps[:min_length]
    for sensor_name in sensors_data.keys():
        sensors_data[sensor_name]['x_accel'] = sensors_data[sensor_name]['x_accel'][:min_length]
        sensors_data[sensor_name]['y_accel'] = sensors_data[sensor_name]['y_accel'][:min_length]
        sensors_data[sensor_name]['z_accel'] = sensors_data[sensor_name]['z_accel'][:min_length]
        sensors_data[sensor_name]['temperature'] = sensors_data[sensor_name]['temperature'][:min_length]
        sensors_data[sensor_name]['force'] = sensors_data[sensor_name]['force'][:min_length]

    fig, ax = plt.subplots(5, 1, sharex=True, figsize=(10, 10))

    for sensor_name in ["HX711-Guage Sensor", "ADXL345-Accelerometer Sensor", "MAX6675-Thermocouple Sensor"]:
        ax[0].plot(timestamps, sensors_data[sensor_name]['x_accel'], label=f'{sensor_name} X-Accel')
        ax[1].plot(timestamps, sensors_data[sensor_name]['y_accel'], label=f'{sensor_name} Y-Accel')
        ax[2].plot(timestamps, sensors_data[sensor_name]['z_accel'], label=f'{sensor_name} Z-Accel')
        ax[3].plot(timestamps, sensors_data[sensor_name]['temperature'], label=f'{sensor_name} Temperature')
        ax[4].plot(timestamps, sensors_data[sensor_name]['force'], label=f'{sensor_name} Force')

    for i in range(5):
        ax[i].legend()

    fig.autofmt_xdate()
    ax[4].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    plt.tight_layout()
    plt.show()

def show_data_summary():
    sensor_labels = ['HX711-Guage Sensor', 'ADXL345-Accelerometer Sensor', 'MAX6675-Thermocouple Sensor']
    stats = {sensor_name: {'x_accel': [], 'y_accel': [], 'z_accel': [], 'temperature': [], 'force': []} for sensor_name in sensor_labels}

    for data in plot_data_storage:
        sensor_name = data['sensor_name']
        stats[sensor_name]['x_accel'].append(data['x_accel'])
        stats[sensor_name]['y_accel'].append(data['y_accel'])
        stats[sensor_name]['z_accel'].append(data['z_accel'])
        stats[sensor_name]['temperature'].append(data['temperature'])
        stats[sensor_name]['force'].append(data['force'])

    summary_text = ""
    for sensor_name in sensor_labels:
        summary_text += f"{sensor_name}:\n"
        for metric in stats[sensor_name]:
            values = np.array(stats[sensor_name][metric])
            summary_text += f"{metric}: Count={len(values)}, Mean={np.mean(values):.2f}, Std={np.std(values):.2f}, Min={np.min(values):.2f}, Max={np.max(values):.2f}\n"
        summary_text += "\n"

    messagebox.showinfo("Data Summary", summary_text)

def stop_data_collection():
    global stop_event
    stop_event.set()
    logging.info("Data collection stopped.")

def reset_data():
    global hx711_calibration, adxl345_calibration, max6675_calibration
    airspeed.set("0")
    acceleration.set("0")
    g_force.set("0")
    hx711_calibration = 0.0
    adxl345_calibration = 0.0
    max6675_calibration = 0.0
    logging.info("All values reset.")

def download_data():
    filetypes = [('Excel files', '*.xlsx'), ('Text files', '*.txt')]
    filepath = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=filetypes)
    if filepath:
        if filepath.endswith('.xlsx'):
            df = pd.DataFrame(plot_data_storage)
            df.to_excel(filepath, index=False)
            messagebox.showinfo("Download Complete", f"Data saved as Excel file at {filepath}")
        elif filepath.endswith('.txt'):
            with open(filepath, 'w') as file:
                writer = csv.DictWriter(file, fieldnames=plot_data_storage[0].keys(), delimiter='\t')
                writer.writeheader()
                writer.writerows(plot_data_storage)
            messagebox.showinfo("Download Complete", f"Data saved as text file at {filepath}")

def show_calibration_window():
    calib_win = Toplevel()
    calib_win.title("Calibration and Configuration")

    Label(calib_win, text="HX711 Calibration:").grid(row=0, column=0)
    hx711_calib = StringVar(value=str(hx711_calibration))
    Entry(calib_win, textvariable=hx711_calib).grid(row=0, column=1)

    Label(calib_win, text="ADXL345 Calibration:").grid(row=1, column=0)
    adxl345_calib = StringVar(value=str(adxl345_calibration))
    Entry(calib_win, textvariable=adxl345_calib).grid(row=1, column=1)

    Label(calib_win, text="MAX6675 Calibration:").grid(row=2, column=0)
    max6675_calib = StringVar(value=str(max6675_calibration))
    Entry(calib_win, textvariable=max6675_calib).grid(row=2, column=1)

    def save_calibration():
        global hx711_calibration, adxl345_calibration, max6675_calibration
        try:
            hx711_calibration = float(hx711_calib.get())
            adxl345_calibration = float(adxl345_calib.get())
            max6675_calibration = float(max6675_calib.get())
            logging.info(f"Saved HX711 Calibration: {hx711_calibration}")
            logging.info(f"Saved ADXL345 Calibration: {adxl345_calibration}")
            logging.info(f"Saved MAX6675 Calibration: {max6675_calibration}")
            calib_win.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for calibration.")
            logging.error(f"Invalid calibration input: {e}")

    Button(calib_win, text="Save", command=save_calibration).grid(row=3, columnspan=2)

def authenticate_user(username, password, root, login_win):
    if username == USERNAME and password == PASSWORD:
        logging.info("User authenticated successfully.")
        login_win.destroy()
        show_main_window(root)
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")
        logging.warning("Failed login attempt.")

def show_login_window(root):
    login_win = Toplevel(root)
    login_win.title("User Login")

    Label(login_win, text="Username:").grid(row=0, column=0)
    username = StringVar()
    Entry(login_win, textvariable=username).grid(row=0, column=1)

    Label(login_win, text="Password:").grid(row=1, column=0)
    password = StringVar()
    Entry(login_win, textvariable=password, show='*').grid(row=1, column=1)

    Button(login_win, text="Login", command=lambda: authenticate_user(username.get(), password.get(), root, login_win)).grid(row=2, columnspan=2)

def show_main_window(root):
    global airspeed, acceleration, g_force

    Label(root, text="Airspeed:").grid(row=0, column=0)
    Label(root, text="Acceleration:").grid(row=1, column=0)
    Label(root, text="G-Force:").grid(row=2, column=0)

    airspeed = StringVar()
    acceleration = StringVar()
    g_force = StringVar()

    Entry(root, textvariable=airspeed).grid(row=0, column=1)
    Entry(root, textvariable=acceleration).grid(row=1, column=1)
    Entry(root, textvariable=g_force).grid(row=2, column=1)

    sensor_names = ["HX711-Guage Sensor", "ADXL345-Accelerometer Sensor", "MAX6675-Thermocouple Sensor"]
    gui_elements = {f'{metric}_{sensor_name}': StringVar() for sensor_name in sensor_names for metric in ['x_accel', 'y_accel', 'z_accel', 'temperature', 'force']}
    gui_elements['acceleration'] = acceleration

    Label(root, text="Sensor Name").grid(row=3, column=0)
    Label(root, text="X-Accel").grid(row=3, column=1)
    Label(root, text="Y-Accel").grid(row=3, column=2)
    Label(root, text="Z-Accel").grid(row=3, column=3)
    Label(root, text="Temperature").grid(row=3, column=4)
    Label(root, text="Force").grid(row=3, column=5)

    for i, sensor_name in enumerate(sensor_names):
        Label(root, text=sensor_name).grid(row=4+i, column=0)
        Label(root, textvariable=gui_elements[f'x_accel_{sensor_name}']).grid(row=4+i, column=1)
        Label(root, textvariable=gui_elements[f'y_accel_{sensor_name}']).grid(row=4+i, column=2)
        Label(root, textvariable=gui_elements[f'z_accel_{sensor_name}']).grid(row=4+i, column=3)
        Label(root, textvariable=gui_elements[f'temperature_{sensor_name}']).grid(row=4+i, column=4)
        Label(root, textvariable=gui_elements[f'force_{sensor_name}']).grid(row=4+i, column=5)

    # Adding Listbox to show real-time output
    output_listbox = Listbox(root, width=80, height=10)
    output_listbox.grid(row=7, columnspan=6)
    scrollbar = Scrollbar(root)
    scrollbar.grid(row=7, column=6, sticky='ns')
    output_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=output_listbox.yview)

    button_frame = Frame(root)
    button_frame.grid(row=8, columnspan=6, pady=10)

    def start_thread():
        start_data_collection(airspeed.get(), acceleration.get(), g_force.get(), gui_elements, output_listbox)

    def create_plot():
        plot_data(gui_elements, output_listbox)

    def create_bar():
        create_bar_graph()

    def create_heat():
        create_heat_map()

    def show_summary():
        show_data_summary()

    Button(button_frame, text="Start/Resume", command=start_thread).grid(row=0, column=0, padx=5, pady=5)
    Button(button_frame, text="Stop/Pause", command=stop_data_collection).grid(row=1, column=0, padx=5, pady=5)
    Button(button_frame, text="Calibrate", command=show_calibration_window).grid(row=0, column=1, padx=5, pady=5)
    Button(button_frame, text="Reset", command=reset_data).grid(row=1, column=1, padx=5, pady=5)
    Button(button_frame, text="Plot Data", command=create_plot).grid(row=0, column=2, padx=5, pady=5)
    Button(button_frame, text="Bar Graph", command=create_bar).grid(row=1, column=2, padx=5, pady=5)
    Button(button_frame, text="Heat Map", command=create_heat).grid(row=0, column=3, padx=5, pady=5)
    Button(button_frame, text="Data Summary", command=show_summary).grid(row=1, column=3, padx=5, pady=5)
    Button(button_frame, text="Download Data", command=download_data).grid(row=2, column=1, padx=5, pady=5)

def main():
    root = Tk()
    root.title("Control System")

    show_login_window(root)

    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        logging.info("Program terminated by user.")
