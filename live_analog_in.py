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

        # Initialize the plot
        fig, ax = plt.subplots()
        line, = ax.plot([], [], lw=2)
        ax.set_xlabel("time [ms]")
        ax.set_ylabel("voltage [V]")

        def init():
            """Initialize the plot for updating."""
            ax.set_xlim(0, 10)  # Set a range for x-axis; adjust as necessary
            ax.set_ylim(-5, 5)  # Set range based on expected voltage range
            return line,

        def update(frame):
            """Update function to fetch and display new data."""
            buffer = scope.record(device_data, channel=1)  # Get live data from scope
            length = len(buffer)
            if length > 10000:
                length = 10000
            buffer = buffer[0:length]

            # Generate time data for the x-axis
            time = [i * 1e03 / scope.data.sampling_frequency for i in range(len(buffer))]

            # Update the line data
            line.set_data(time, buffer)
            ax.set_xlim(time[0], time[-1])  # Update x-axis limits
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
