# app.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from WF_SDK import device, scope, wavegen, error
from time import sleep
from threading import Thread
import numpy as np

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for testing

# Global variable for controlling the data stream thread
data_stream_thread = None
session_count = 4  # Default value, can be updated dynamically

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('set_session_count')
def set_session_count(data):
    """Set the number of sessions to accumulate before emitting data."""
    global session_count
    session_count = data.get('session_count', 10)  # Default to 2 if not specified
    emit('session_count_updated', {'session_count': session_count})


def stream_data():
    """Thread function to continuously stream data from the device."""
    try:
        device_data = device.open()
        if device_data.name != "Digital Discovery":
            # Set up the scope and retrieve sample rate
            scope.open(device_data)
            sample_rate = scope.data.sampling_frequency  # 20 MHz by default
            sample_interval = 1 / sample_rate  # Interval in seconds per sample

            wavegen.generate(device_data, channel=1, function=wavegen.function.sine, offset=0, frequency=10e03, amplitude=2)
            sleep(1)

            buffer_accumulated = []
            timestamps_accumulated = []

            while True:
                for _ in range(session_count):
                    buffer = scope.record(device_data, channel=1)
                    
                    # Generate timestamps for each sample in the buffer
                    num_samples = len(buffer)
                    timestamps = list(np.arange(num_samples) * sample_interval)  # Generate timestamps in seconds

                    # Accumulate data
                    buffer_accumulated.extend(buffer)
                    timestamps_accumulated.extend(timestamps)

                    sleep(0.001)  # Adjust delay as needed

                # Emit accumulated data after `session_count` recordings
                socketio.emit('update_data', {
                    'voltage_data': buffer_accumulated,
                    'timestamps': timestamps_accumulated
                })

                # Clear the accumulated data
                buffer_accumulated.clear()
                timestamps_accumulated.clear()

    except error as e:
        print(e)
    finally:
        device.close(device_data)


@socketio.on('connect')
def handle_connect():
    global data_stream_thread
    if data_stream_thread is None:
        data_stream_thread = Thread(target=stream_data)
        data_stream_thread.start()


if __name__ == '__main__':
    socketio.run(app, debug=True)  # Use SocketIO's `run` method
