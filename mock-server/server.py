import http.server
import socketserver
import json
import math
import time
import random

PORT = 8111

start_time = time.time()
chat_counter = 1

chat_pool = [
    {"msg": "Внимание на карту! [G-4]", "sender": "Tanker_RU", "enemy": True, "mode": "all"},
    {"msg": "Attack the A point!", "sender": "Viper_1", "enemy": False, "mode": "squad"},
    {"msg": "Need air support over C point!", "sender": "Panzer_Commander", "enemy": False, "mode": "team"},
    {"msg": "Спасибо!", "sender": "AcePilot_99", "enemy": False, "mode": "team"},
    {"msg": "Viper_1 (F-16C) has destroyed RedBaron (MiG-29)", "sender": "system", "enemy": False, "mode": "system"},
    {"msg": "Внимание на указанный квадрат!", "sender": "Comrade_77", "enemy": True, "mode": "all"},
    {"msg": "Enemy SPAA spotted near north airfield", "sender": "Falcon_5", "enemy": False, "mode": "team"}
]

chats_history = [
    {"id": 1, "msg": "Battle started!", "sender": "system", "enemy": False, "mode": "system", "time": 0}
]

class MockTelemetryHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress verbose HTTP log output
        return

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        global chat_counter, chats_history
        elapsed = time.time() - start_time

        # Periodically add a new chat message every 8 seconds
        if elapsed > chat_counter * 8:
            chat_counter += 1
            sample_chat = random.choice(chat_pool)
            chats_history.append({
                "id": chat_counter,
                "msg": sample_chat["msg"],
                "sender": sample_chat["sender"],
                "enemy": sample_chat["enemy"],
                "mode": sample_chat["mode"],
                "time": int(elapsed)
            })
            if len(chats_history) > 20:
                chats_history.pop(0)

        if self.path.startswith('/gamechat'):
            last_id = 0
            if '?lastId=' in self.path:
                try:
                    last_id = int(self.path.split('?lastId=')[1].split('&')[0])
                except (ValueError, IndexError):
                    last_id = 0
            
            filtered_chats = [c for c in chats_history if c["id"] > last_id] if last_id > 0 else chats_history
            self.send_json(filtered_chats)

        elif self.path == '/state':
            alt = 3500 + int(math.sin(elapsed * 0.1) * 300)
            tas = 600 + int(math.sin(elapsed * 0.2) * 80)
            ias = 500 + int(math.sin(elapsed * 0.2) * 70)
            g_force = round(1.2 + math.sin(elapsed * 0.5) * 0.8, 2)
            rpm = 13500 + int(math.sin(elapsed * 0.3) * 300)
            
            payload = {
                "valid": True,
                "army": "aviation",
                "type": "su_30sm2",
                "H, m": alt,
                "TAS, km/h": tas,
                "IAS, km/h": ias,
                "M": round(tas / 1225.0, 2),
                "AoA, deg": round(5.0 + math.sin(elapsed * 0.4) * 3.0, 1),
                "AoS, deg": round(math.sin(elapsed * 0.2) * 0.5, 1),
                "Ny": g_force,
                "Vy, m/s": round(math.cos(elapsed * 0.1) * 15.0, 1),
                "Mfuel, kg": max(100, int(9000 - elapsed * 2)),
                "Mfuel0, kg": 9400,
                "RPM 1": rpm,
                "throttle 1, %": 100,
                "thrust 1, kgs": 4900 + int(math.sin(elapsed * 0.3) * 200),
                "oil temp 1, C": 88
            }
            self.send_json(payload)

        elif self.path == '/indicators':
            compass = round((elapsed * 5.0) % 360, 1)
            alt = 3500.0 + math.sin(elapsed * 0.1) * 300.0
            g_force = round(1.2 + math.sin(elapsed * 0.5) * 0.8, 2)

            payload = {
                "valid": True,
                "army": "air",
                "type": "su_30sm2",
                "speed": round(165.0 + math.sin(elapsed * 0.2) * 20.0, 2),
                "altitude_hour": round(alt, 1),
                "compass": compass,
                "g_meter": g_force,
                "g_meter_max": 9.5,
                "g_meter_min": -1.2,
                "aoa": round(5.0 + math.sin(elapsed * 0.4) * 3.0, 1),
                "aviahorizon_roll": round(math.sin(elapsed * 0.3) * 15.0, 1),
                "aviahorizon_pitch": round(math.cos(elapsed * 0.2) * 8.0, 1),
                "rpm": 13500.0 + math.sin(elapsed * 0.3) * 300.0,
                "throttle": 1.0
            }
            self.send_json(payload)

        elif self.path == '/map_info.json':
            payload = {
                "map_generation": [[0.0, 0.0], [65536.0, 65536.0]],
                "map_min": [-32768.0, -32768.0],
                "map_max": [32768.0, 32768.0],
                "grid_steps": [8192.0, 8192.0],
                "grid_zero": [-32768.0, 32768.0]
            }
            self.send_json(payload)

        elif self.path == '/map_obj.json':
            # Generate moving objects for mock testing
            p_x = 0.5 + math.sin(elapsed * 0.05) * 0.2
            p_y = 0.5 + math.cos(elapsed * 0.05) * 0.2
            e_x = 0.5 - math.sin(elapsed * 0.03) * 0.3
            e_y = 0.5 + math.cos(elapsed * 0.03) * 0.3
            
            payload = [
                {"type": "airfield", "color": "#112233", "color[]": [17, 34, 51], "x": 0.2, "y": 0.8},
                {"type": "airfield", "color": "#990000", "color[]": [153, 0, 0], "x": 0.8, "y": 0.2},
                {"type": "player", "color": "#FFFFFF", "color[]": [255,255,255], "x": p_x, "y": p_y, "dx": math.cos(elapsed * 0.05), "dy": -math.sin(elapsed * 0.05), "icon": "Fighter"},
                {"type": "enemy", "color": "#FF0000", "color[]": [255,0,0], "x": e_x, "y": e_y, "icon": "Fighter"}
            ]
            self.send_json(payload)

        elif self.path == '/mission.json':
            payload = {
                "objectives" : [
                    {
                        "primary" : true,
                        "status" : "in_progress",
                        "text" : "<color=#00BFFF>V1.2.31</color>: Protect Airfield"
                    },
                    {
                        "primary" : false,
                        "status" : "succeed",
                        "text" : "Destroy enemy convoy"
                    }
                ],
                "status" : "running"
            }
            self.send_json(payload)

        elif self.path.startswith('/map.img'):
            try:
                with open("map.png", "rb") as f:
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/png')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    print(f"==================================================")
    print(f"   War Thunder Mock Telemetry Server Running      ")
    print(f"   Hosting endpoints at http://localhost:{PORT}   ")
    print(f"   - http://localhost:{PORT}/gamechat            ")
    print(f"   - http://localhost:{PORT}/state               ")
    print(f"   - http://localhost:{PORT}/indicators          ")
    print(f"   - http://localhost:{PORT}/map.png             ")
    print(f"   - http://localhost:{PORT}/map_info.json       ")
    print(f"   - http://localhost:{PORT}/map_obj.json        ")
    print(f"==================================================")
    with socketserver.TCPServer(("", PORT), MockTelemetryHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping Mock Telemetry Server...")

if __name__ == '__main__':
    run_server()
