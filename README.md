# WT Aura Velox Overlay (WTAVO)

**WT Aura Velox Overlay (WTAVO)** is an advanced, fully transparent desktop assistant and overlay designed specifically for **War Thunder Air Simulator (Air SB)** players. By hooking into War Thunder's local browser map interface (`localhost:8111`), WTAVO extracts live telemetry, chat, and map data, presenting it in an immersive, customizable overlay that sits directly on top of your game window.

---

## 🌟 Key Features for Air Simulator

### 🗣️ Live Chat Translation
Communication is key in Simulator battles, but language barriers can cause critical information to be lost.
* **Auto-Translation**: Automatically translates foreign game chat messages into your preferred language using AI or Google Translate. 


### 🗺️ Interactive Tactical Map & Navigation
The in-game map is limited. WTAVO provides a fully featured tactical drawing board.
* **Draw Tools**: Draw lines, circles, paths, and place waypoints on the map.
* **Distance Measurements**: Automatically calculates and displays the distance of your drawn lines/paths in **kilometers (km)** or **nautical miles (nm)**.
* **Map Templates**: Save your tactical drawings and waypoints as templates. When you load into a specific map (e.g., "Afghanistan" or "Dover"), WTAVO can automatically load your pre-saved waypoints and strategic routes!

### 🎙️ Voice-Activated AI Co-Pilot
A hands-free, telemetry-aware AI assistant sitting in the cockpit with you.
* **Voice Recognition**: Talk directly into your microphone to ask the Co-Pilot questions without taking your hands off your HOTAS.
* **Context-Aware**: The AI knows your current altitude, speed, heading, and aircraft type. Ask it things like *"What is my optimal climb speed?"* or *"Am I stalling?"* and it will respond based on your live telemetry data!
* **Immersive TTS**: Co-pilot responds using Text-to-Speech (powered by OpenAI or Gemini).

### 🛩️ Live Telemetry HUD
Keep your eyes out of the cockpit with a customizable, external Heads Up Display.
* **Crucial Flight Data**: Real-time readouts of IAS, TAS, Mach, Altitude, Compass Heading, AoA (Angle of Attack), Engine RPM, and Throttle.


### 👻 Seamless Transparent Overlay (Compact Mode)
WTAVO is built on Tauri and SvelteKit, allowing it to become a borderless, fully transparent overlay.
---

## 🚀 Getting Started

### Prerequisites
* **War Thunder**: Must be running on your PC. The game automatically hosts a local server on port `8111`.
* **OS**: Windows 10/11 is recommended.

### Installation

If you are downloading a pre-built release:
1. Go to the [Releases](https://github.com/ivdamke/WT-Aura-Velox-Overlay/releases) page.
2. Download and run the `WTAVO_0.1.11_x64_en-US.msi`.
3. Launch the app while War Thunder is open.

### Development Setup
If you want to build the overlay from source:

1. Clone this repository.
2. Ensure you have **Node.js** and **Rust** installed on your system.
3. Install dependencies:
   ```bash
   npm install
   ```
4. Run the development server:
   ```bash
   npm run tauri dev
   ```
5. To build a production executable/installer:
   ```bash
   npm run tauri build
   ```

## ⚙️ Configuration & API Keys

To use the **AI Co-Pilot** and **AI Chat Translation** features, you will need to provide an API key in the application's Settings menu.
* **Gemini (Recommended)**: Get a free API key from Google AI Studio. Provides excellent speed and TTS capabilities.
* **OpenAI**: Get an API key from OpenAI for ChatGPT-style responses and premium TTS voices.
* **Localhost (Ollama)**: Advanced users can run local models via Ollama for zero-latency, offline AI assistance!

---

*WT Aura Velox Overlay is an open-source tool and is not officially affiliated with Gaijin Entertainment.*
