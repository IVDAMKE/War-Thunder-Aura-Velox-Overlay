import urllib.request
import json
import os
import sys

ENDPOINTS = {
    "gamechat": "http://localhost:8111/gamechat?lastId=0",
    "state": "http://localhost:8111/state",
    "indicators": "http://localhost:8111/indicators"
}

FALLBACKS = {
    "gamechat": [
        {"id": 1, "msg": "[Squad] Attack the A point!", "sender": "Viper_1", "enemy": False, "mode": "squad", "time": 10},
        {"id": 2, "msg": "Внимание на карту! [G-4]", "sender": "TankerRU", "enemy": True, "mode": "all", "time": 18},
        {"id": 3, "msg": "Bravo! Excellent work!", "sender": "AcePilot_99", "enemy": False, "mode": "team", "time": 25},
        {"id": 4, "msg": "Viper_1 (F-16C) has destroyed TankerRU (T-80BVM)", "sender": "system", "enemy": False, "mode": "system", "time": 42}
    ],
    "state": {
        "valid": True,
        "army": "aviation",
        "type": "plane",
        "H, m": 1450,
        "TAS, km/h": 680,
        "IAS, km/h": 620,
        "M": 0.58,
        "AoA, deg": 3.2,
        "AoS, deg": 0.1,
        "Ny": 1.2,
        "Vy, m/s": 15.5,
        "Wx, deg/s": 0.0,
        "Mfuel, kg": 1200,
        "Mfuel0, kg": 2000,
        "RPM 1": 95,
        "manifold pressure 1, atm": 1.2,
        "oil temp 1, C": 85,
        "pitch 1, deg": 12,
        "throttle 1, %": 100,
        "water temp 1, C": 90,
        "gear, %": 0,
        "flaps, %": 0,
        "airbrake, %": 0
    },
    "indicators": {
        "valid": True,
        "type": "plane",
        "speed": 172.22,
        "pedals": 0,
        "stick_elevator": -0.05,
        "stick_ailerons": 0.0,
        "compass": 245.5,
        "altitude_hour": 1450.0,
        "speed_hour": 620.0,
        "oil_pressure": 4.5,
        "oil_temperature": 85.0,
        "water_temperature": 90.0,
        "mixture": 100.0,
        "g_meter": 1.2,
        "horizon_roll": -2.5,
        "horizon_pitch": 4.0
    }
}

def sample():
    os.makedirs("sample_data", exist_ok=True)
    print("=== Sampling Telemetry from http://localhost:8111 ===")
    
    for key, url in ENDPOINTS.items():
        output_file = os.path.join("sample_data", f"{key}.json")
        try:
            print(f"Fetching {url}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'WT-Desktop-Assistant'})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  [SUCCESS] Saved live response to {output_file}")
                else:
                    print(f"  [WARNING] Received status code {response.status}. Using fallback.")
                    save_fallback(key, output_file)
        except Exception as e:
            print(f"  [INFO] Could not connect to {url} ({e}). Saving fallback schema to {output_file}")
            save_fallback(key, output_file)

def save_fallback(key, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(FALLBACKS[key], f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    sample()
