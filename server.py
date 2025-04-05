from flask import Flask, render_template_string, Response, request
from picamera2 import Picamera2
import cv2
from libcamera import controls

# Setup Flask
app = Flask(__name__)

# Initialize Picamera2
picam2 = Picamera2()
# video_config = picam2.create_video_configuration(main={"size": (640, 480)})
video_config = picam2.create_video_configuration(main={"size": (1280, 800), "format": "BGR888"})
picam2.configure(video_config)
picam2.start()
picam2.set_controls({"AwbMode": 1})

# Apply Auto White Balance
picam2.set_controls({"AwbMode": 1})

def generate_frames():
    while True:
        frame = picam2.capture_array()
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Fix weird colors
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string('''
        <html>
        <head>
            <title>Camera Stream</title>
            <script>
                function triggerAutofocus() {
                    fetch("/autofocus", { method: "POST" })
                        .then(response => {
                            if (!response.ok) throw new Error("Autofocus failed");
                            alert("Autofocus triggered!");
                        })
                        .catch(err => alert("Error: " + err));
                }
            </script>
        </head>
        <body>
            <h1>Live Camera Stream</h1>
            <img src="{{ url_for('video_feed') }}" width="640" height="480"><br><br>
            <button onclick="triggerAutofocus()">Trigger Autofocus</button>
        </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/autofocus', methods=['POST'])
def autofocus():
    try:
        # picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})  # 1 = Auto
        picam2.set_controls({"AfMode": 0})
        picam2.set_controls({"AfMode": 1})
        picam2.set_controls({"AfTrigger": 0})
        print("Autofoucs Triggered")
        return "OK", 200
    except Exception as e:
        print(e)
        return str(e), 500

@app.route('/capture', methods=['GET'])
def capture():
    try:
        frame = picam2.capture_array()
        
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Fix weird colors
        _, img_encoded = cv2.imencode('.jpg', frame)
        return Response(
            img_encoded.tobytes(),
            mimetype='image/jpeg'
        )
    except Exception as e:
        print(f"Capture error: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)