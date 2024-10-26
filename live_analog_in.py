from WF_SDK import device, scope, wavegen, tools, error  # import instruments
import matplotlib.pyplot as plt  # needed for plotting
from matplotlib.animation import FuncAnimation
from time import sleep  # needed for delays
from collections import deque

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

        # Duration of the rolling window in seconds
        PLOT_DURATION_WINDOW_SECONDS = 3
        sampling_frequency = scope.data.sampling_frequency

        # Set an upper limit on max_points to prevent excessively large deques
        max_points = min(int(PLOT_DURATION_WINDOW_SECONDS * sampling_frequency), 60000)

        # Initialize the plot
        fig, ax = plt.subplots()
        line, = ax.plot([], [], lw=2)
        ax.set_xlabel("time [ms]")
        ax.set_ylabel("voltage [V]")

        # Initialize deques for time and voltage data with a fixed length
        time_data = deque(maxlen=max_points)
        voltage_data = deque(maxlen=max_points)

        print(f"Calculated maxlen for deques: {max_points}")

        def init():
            """Initialize the plot for updating."""
            ax.set_xlim(0, PLOT_DURATION_WINDOW_SECONDS * 1000)  # 3 seconds in ms
            ax.set_ylim(-5, 5)  # Set range based on expected voltage range
            line.set_data([], [])  # Initialize empty data
            return line,

        def update(frame):
            """Update function to fetch and display new data."""
            # Record new data from scope
            buffer = scope.record(device_data, channel=1)
            num_samples = len(buffer)

            # Generate time data for new samples in ms
            new_time_data = [i * 1e03 / sampling_frequency for i in range(num_samples)]
            if time_data:
                # Offset the time data by the last time value in the deque
                new_time_data = [t + time_data[-1] + 1e03 / sampling_frequency for t in new_time_data]

            # Extend the deques with new data
            time_data.extend(new_time_data)
            voltage_data.extend(buffer)

            # Check and print deque lengths to confirm max_points is maintained
            print(f"Deque lengths (Time: {len(time_data)}, Voltage: {len(voltage_data)})")

            # Update the line data with the current deque contents
            line.set_data(list(time_data), list(voltage_data))

            # Ensure x-axis limits reflect the rolling 3-second window
            ax.set_xlim(time_data[0], time_data[-1])  # Rolling window based on deque length
            return line,

        # Create the animation object
        ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=100)  # interval in ms

        plt.show()

        # Reset the scope and wavegen
        scope.close(device_data)
        wavegen.close(device_data)

    # Close the connection
    device.close(device_data)

except error as e:
    print(e)
    # Close the connection if an error occurs
    device.close(device_data)
