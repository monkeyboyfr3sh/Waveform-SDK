# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from WF_SDK import device, scope, wavegen, error
from time import sleep
from threading import Thread

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for testing

# Global variable for controlling the data stream thread
data_stream_thread = None

@app.route('/')
def index():
    return render_template('index.html')

def stream_data():
    """Thread function to continuously stream data from the device."""
    try:
        device_data = device.open()
        if device_data.name != "Digital Discovery":
            scope.open(device_data)
            wavegen.generate(device_data, channel=1, function=wavegen.function.sine, offset=0, frequency=10e03, amplitude=2)
            sleep(1)

            while True:
                buffer = scope.record(device_data, channel=1)
                socketio.emit('update_data', {'voltage_data': buffer})
                sleep(0.1)  # Adjust delay as needed

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
