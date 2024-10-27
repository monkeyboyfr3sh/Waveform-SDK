# app.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from WF_SDK import device, scope, wavegen, error
from time import sleep
from threading import Thread
import numpy as np

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable for controlling the data stream thread
data_stream_thread = None
session_count = 5  # Default value, can be updated dynamically

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('set_session_count')
def set_session_count(data):
    global session_count
    session_count = data.get('session_count', 10)
    emit('session_count_updated', {'session_count': session_count})

def stream_data():
    try:
        device_data = device.open()
        if device_data.name != "Digital Discovery":
            scope.open(device_data)
            sample_rate = scope.data.sampling_frequency
            sample_interval = 1 / sample_rate

            wavegen.generate(device_data, channel=1, function=wavegen.function.sine, offset=0, frequency=10e03, amplitude=2)
            wavegen.generate(device_data, channel=2, function=wavegen.function.square, offset=0, frequency=10e03, amplitude=2)
            sleep(1)

            buffer_accumulated_ch1 = []
            buffer_accumulated_ch2 = []
            timestamps_accumulated = []

            while True:
                for _ in range(session_count):
                    buffer_ch1 = scope.record(device_data, channel=1)
                    buffer_ch2 = scope.record(device_data, channel=2)
                    
                    num_samples = len(buffer_ch1)
                    timestamps = list(np.arange(num_samples) * sample_interval)

                    buffer_accumulated_ch1.extend(buffer_ch1)
                    buffer_accumulated_ch2.extend(buffer_ch2)
                    timestamps_accumulated.extend(timestamps)

                socketio.emit('update_data', {
                    'voltage_data_ch1': buffer_accumulated_ch1,
                    'voltage_data_ch2': buffer_accumulated_ch2,
                    'timestamps': [t * 1000 for t in timestamps_accumulated]  # Convert to milliseconds
                })

                buffer_accumulated_ch1.clear()
                buffer_accumulated_ch2.clear()
                timestamps_accumulated.clear()
                sleep(0.1)

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
    socketio.run(app, debug=True)
