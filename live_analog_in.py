from WF_SDK import device, scope, wavegen, tools, error  # import instruments
import matplotlib.pyplot as plt  # needed for plotting
from matplotlib.animation import FuncAnimation
from time import sleep  # needed for delays

try:
    # connect to the device
    device_data = device.open()

    # handle devices without analog I/O channels
    if device_data.name != "Digital Discovery":

        # initialize the scope with default settings
        scope.open(device_data)

        # set up triggering on scope channel 1
        scope.trigger(device_data, enable=False, source=scope.trigger_source.analog, channel=1, level=0)

        # generate a 10KHz sine signal with 2V amplitude on channel 1
        wavegen.generate(device_data, channel=1, function=wavegen.function.sine, offset=0, frequency=10e03, amplitude=2)

        # wait 1 second to allow signal generation to stabilize
        sleep(1)

        # Calculate the maximum number of points to store for 3 seconds of data
        max_points = int(3 * scope.data.sampling_frequency)  # adjust for sampling frequency

        # Initialize the plot
        fig, ax = plt.subplots()
        line, = ax.plot([], [], lw=2)
        ax.set_xlabel("time [ms]")
        ax.set_ylabel("voltage [V]")

        # Initialize data lists for time and voltage with dummy starting data
        time_data = [0]
        voltage_data = [0]

        def init():
            """Initialize the plot for updating."""
            ax.set_xlim(0, 3000)  # 3 seconds in ms
            ax.set_ylim(-5, 5)  # Set range based on expected voltage range
            line.set_data(time_data, voltage_data)  # Set initial data
            return line,

        def update(frame):
            """Update function to fetch and display new data."""
            global time_data, voltage_data  # declare as global to modify outside variables

            buffer = scope.record(device_data, channel=1)  # Get live data from scope
            num_samples = len(buffer)

            # Generate time data for new samples in ms
            new_time_data = [i * 1e03 / scope.data.sampling_frequency for i in range(num_samples)]
            if time_data:
                new_time_data = [t + time_data[-1] + 1e03 / scope.data.sampling_frequency for t in new_time_data]

            # Append new data
            time_data.extend(new_time_data)
            voltage_data.extend(buffer)

            # Trim data to maintain only the last 3 seconds
            if len(time_data) > max_points:
                time_data = time_data[-max_points:]
                voltage_data = voltage_data[-max_points:]

            # Update the line data
            line.set_data(time_data, voltage_data)
            ax.set_xlim(time_data[0], time_data[-1])  # Update x-axis limits to show rolling window
            return line,

        # Create the animation object
        ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=100)  # interval in ms

        plt.show()

        # reset the scope and wavegen
        scope.close(device_data)
        wavegen.close(device_data)

    # close the connection
    device.close(device_data)

except error as e:
    print(e)
    # close the connection if error occurs
    device.close(device_data)
