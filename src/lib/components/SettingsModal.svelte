<script lang="ts">
  import { DEFAULT_SETTINGS, SUPPORTED_LANGUAGES, type InterfaceSettings } from '../types/settings';
  import { onMount } from 'svelte';

  let availableVoices = $state<SpeechSynthesisVoice[]>([]);

  onMount(() => {
    const loadVoices = () => {
      if ('speechSynthesis' in window) {
        availableVoices = window.speechSynthesis.getVoices();
      }
    };
    loadVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  });

  let {
    isOpen = false,
    settings = $bindable(DEFAULT_SETTINGS),
    onClose = () => {}
  }: {
    isOpen?: boolean;
    settings: InterfaceSettings;
    onClose?: () => void;
  } = $props();

  function resetToDefaults() {
    settings = { ...DEFAULT_SETTINGS };
  }

  function handleBackdropKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  function recordKeybind(e: KeyboardEvent, settingKey: 'shortcutToggleClickThrough' | 'shortcutToggleSettings') {
    e.preventDefault();
    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return;

    const parts: string[] = [];
    if (e.ctrlKey) parts.push('Ctrl');
    if (e.altKey) parts.push('Alt');
    if (e.shiftKey) parts.push('Shift');
    if (e.metaKey) parts.push('Win');

    let key = e.key;
    if (key === ' ') key = 'Space';
    else if (key.length === 1) key = key.toUpperCase();

    parts.push(key);
    settings[settingKey] = parts.join('+');
  }
</script>

{#if isOpen}
  <div
    class="modal-backdrop"
    onclick={onClose}
    onkeydown={handleBackdropKeyDown}
    role="presentation"
  >
    <div
      class="modal-content overlay-card"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      tabindex="-1"
    >
      <div class="modal-header">
        <div class="title-group">
          <span class="gear-icon">⚙️</span>
          <span class="modal-title">INTERFACE DISPLAY SETTINGS</span>
        </div>
        <button class="close-btn" onclick={onClose} title="Close Settings">✕</button>
      </div>

      <div class="settings-body">
        <!-- Section 0: Player Identity & Radar -->
        <div class="setting-section">
          <span class="section-title">PILOT IDENTITY & RADAR TRACKING</span>
          <div class="input-group">
            <label for="username-input" class="input-label">
              <span class="label-title">In-Game Username / Pilot Handle</span>
              <span class="label-desc">Used to auto-detect your Kills, Deaths & Assists from game HUD events</span>
            </label>
            <input
              id="username-input"
              type="text"
              bind:value={settings.playerUsername}
              placeholder="e.g. Player1"
              class="text-input"
            />
          </div>
        </div>

        <!-- Section 1: Global UI Preferences -->
        <div class="setting-section">
          <span class="section-title">GLOBAL UI PREFERENCES</span>
          <div class="input-group">
            <label for="idle-time" class="input-label">
              <span class="label-title">Idle Fade-out Time (Seconds)</span>
              <span class="label-desc">Time before inactive widgets fade out</span>
            </label>
            <input
              id="idle-time"
              type="number"
              bind:value={settings.idleFadeTime}
              min="1"
              max="300"
              class="text-input"
              style="width: 100px"
            />
          </div>
          <div class="input-group">
            <label for="idle-opacity" class="input-label">
              <span class="label-title">Idle Fade-out Opacity (0.0 to 1.0)</span>
              <span class="label-desc">Transparency when idle (0 is invisible, 1 is solid)</span>
            </label>
            <input
              id="idle-opacity"
              type="number"
              bind:value={settings.idleFadeOpacity}
              min="0"
              max="1"
              step="0.05"
              class="text-input"
              style="width: 100px"
            />
          </div>
          <div class="input-group">
            <label for="window-launch-mode" class="input-label">
              <span class="label-title">Window Launch Mode</span>
              <span class="label-desc">Launch app in Full Screen of monitor or at last saved window position & size</span>
            </label>
            <select id="window-launch-mode" bind:value={settings.windowLaunchMode} class="select-input">
              <option value="fullscreen">Full Screen (Default)</option>
              <option value="lastPosition">Remember Last Window Position & Size</option>
            </select>
          </div>
        </div>

        <!-- Section: Advanced Theme & Custom Design -->
        <div class="setting-section">
          <span class="section-title">🎨 ADVANCED THEME & CUSTOM DESIGN</span>

          <div class="input-group">
            <label for="accent-color-picker" class="input-label">
              <span class="label-title">Overlay Accent Color</span>
              <span class="label-desc">Primary highlight & glowing element color</span>
            </label>
            <div class="color-picker-wrapper">
              <input
                id="accent-color-picker"
                type="color"
                bind:value={settings.overlayAccentColor}
                class="color-input"
              />
              <span class="color-hex">{settings.overlayAccentColor}</span>
              <button class="reset-keybind-btn" onclick={() => settings.overlayAccentColor = '#38bdf8'} title="Reset accent color">↺</button>
            </div>
          </div>

          <div class="input-group">
            <label for="bg-color-picker" class="input-label">
              <span class="label-title">Overlay Background Base Color</span>
              <span class="label-desc">Base color for glassmorphic cards and panels</span>
            </label>
            <div class="color-picker-wrapper">
              <input
                id="bg-color-picker"
                type="color"
                bind:value={settings.overlayBgColor}
                class="color-input"
              />
              <span class="color-hex">{settings.overlayBgColor}</span>
              <button class="reset-keybind-btn" onclick={() => settings.overlayBgColor = '#121826'} title="Reset background color">↺</button>
            </div>
          </div>

          <div class="input-group">
            <label for="opacity-slider" class="input-label">
              <span class="label-title">Opacity Intensity ({Math.round(settings.overlayOpacity * 100)}%)</span>
              <span class="label-desc">Controls transparency strength of interface panels</span>
            </label>
            <input
              id="opacity-slider"
              type="range"
              min="0.05"
              max="1"
              step="0.05"
              bind:value={settings.overlayOpacity}
              class="range-input"
            />
          </div>

          <div class="input-group">
            <label for="radius-slider" class="input-label">
              <span class="label-title">Panel Corner Rounding ({settings.overlayCardRadius}px)</span>
              <span class="label-desc">Adjust corner radius of cards and panels</span>
            </label>
            <input
              id="radius-slider"
              type="range"
              min="0"
              max="32"
              step="1"
              bind:value={settings.overlayCardRadius}
              class="range-input"
            />
          </div>

          <div class="input-group">
            <label for="blur-slider" class="input-label">
              <span class="label-title">Glassmorphism Blur ({settings.overlayBackdropBlur}px)</span>
              <span class="label-desc">Backdrop blur filter intensity for frosted glass effect</span>
            </label>
            <input
              id="blur-slider"
              type="range"
              min="0"
              max="30"
              step="1"
              bind:value={settings.overlayBackdropBlur}
              class="range-input"
            />
          </div>

          <div class="input-group">
            <label for="custom-css-input" class="input-label">
              <span class="label-title">Custom CSS Styling</span>
              <span class="label-desc">Inject your own custom CSS rules into the overlay</span>
            </label>
            <textarea
              id="custom-css-input"
              bind:value={settings.customCss}
              rows="4"
              placeholder="/* Add custom CSS rules here */"
              class="text-input custom-css-textarea"
            ></textarea>
          </div>
        </div>

        <!-- Section: Keybindings & Shortcuts -->
        <div class="setting-section">
          <span class="section-title">KEYBINDINGS & SHORTCUTS</span>
          
          <div class="input-group">
            <label for="keybind-clickthrough" class="input-label">
              <span class="label-title">Interactive / Click-Through Mode Toggle</span>
              <span class="label-desc">Shortcut to switch between Interactive & Click-Through mode</span>
            </label>
            <div class="keybind-recorder">
              <input
                id="keybind-clickthrough"
                type="text"
                readonly
                value={settings.shortcutToggleClickThrough}
                onkeydown={(e) => recordKeybind(e, 'shortcutToggleClickThrough')}
                class="text-input keybind-input"
                placeholder="Click and press keys..."
              />
              <button class="reset-keybind-btn" onclick={() => settings.shortcutToggleClickThrough = 'Ctrl+Shift+X'} title="Reset to default (Ctrl+Shift+X)">↺</button>
            </div>
          </div>

          <div class="input-group">
            <label for="keybind-settings" class="input-label">
              <span class="label-title">Settings / Header Bar Toggle</span>
              <span class="label-desc">Shortcut to open Settings modal or restore Top Header</span>
            </label>
            <div class="keybind-recorder">
              <input
                id="keybind-settings"
                type="text"
                readonly
                value={settings.shortcutToggleSettings}
                onkeydown={(e) => recordKeybind(e, 'shortcutToggleSettings')}
                class="text-input keybind-input"
                placeholder="Click and press keys..."
              />
              <button class="reset-keybind-btn" onclick={() => settings.shortcutToggleSettings = 'Ctrl+Shift+S'} title="Reset to default (Ctrl+Shift+S)">↺</button>
            </div>
          </div>
        </div>

        <!-- Section 2: Main Panel Modules -->
        <div class="setting-section">
          <span class="section-title">MAIN INTERFACE PANELS</span>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Top Header Control Bar</span>
              <span class="toggle-desc">Title, status badge, theme selector, & quick toggles</span>
            </div>
            <input type="checkbox" bind:checked={settings.showHeader} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Compact Design Mode</span>
              <span class="toggle-desc">Minimalist layout, fully transparent panels, hidden titles</span>
            </div>
            <input type="checkbox" bind:checked={settings.compactMode} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Telemetry HUD Panel</span>
              <span class="toggle-desc">Speed, altitude, G-meter, compass, engine specs</span>
            </div>
            <input type="checkbox" bind:checked={settings.showTelemetryHud} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Combat Stats Tracker</span>
              <span class="toggle-desc">Real-time Kills, Deaths, Assists & K/D Ratio</span>
            </div>
            <input type="checkbox" bind:checked={settings.showStatsWidget} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Live Chat & Translation Feed</span>
              <span class="toggle-desc">Game chat with instant EN translation</span>
            </div>
            <input type="checkbox" bind:checked={settings.showChatWidget} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Tactical Map & Triangulation</span>
              <span class="toggle-desc">Live map feed with Air Sim range finding tools</span>
            </div>
            <input type="checkbox" bind:checked={settings.showMapWidget} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">Match Goals & Objectives</span>
              <span class="toggle-desc">Current primary and secondary objectives panel</span>
            </div>
            <input type="checkbox" bind:checked={settings.showObjectivesWidget} />
            <span class="slider"></span>
          </label>

          <label class="toggle-row master-toggle">
            <div class="toggle-info">
              <span class="toggle-label">AI Co-pilot</span>
              <span class="toggle-desc">Live telemetry-aware AI assistant</span>
            </div>
            <input type="checkbox" bind:checked={settings.showAiCopilotWidget} />
            <span class="slider"></span>
          </label>
        </div>

        <!-- Section 2: Fine-Grained Telemetry Elements -->
        {#if settings.showTelemetryHud}
          <div class="setting-section sub-section">
            <span class="section-title">INDIVIDUAL TELEMETRY GAUGES</span>

            <label class="toggle-row">
              <span class="toggle-label">🏎️ Speed Gauges (IAS / TAS / Mach)</span>
              <input type="checkbox" bind:checked={settings.showSpeed} />
              <span class="slider"></span>
            </label>

            <label class="toggle-row">
              <span class="toggle-label">🏔️ Altitude & Climb Indicator</span>
              <input type="checkbox" bind:checked={settings.showAltitude} />
              <span class="slider"></span>
            </label>

            <label class="toggle-row">
              <span class="toggle-label">⚠️ G-Force Meter & Warning Badges</span>
              <input type="checkbox" bind:checked={settings.showGForce} />
              <span class="slider"></span>
            </label>

            <label class="toggle-row">
              <span class="toggle-label">⚙️ Engine RPM & Throttle Level</span>
              <input type="checkbox" bind:checked={settings.showEngineRpm} />
              <span class="slider"></span>
            </label>

            <label class="toggle-row">
              <span class="toggle-label">📐 Pitch & Roll Artificial Horizon</span>
              <input type="checkbox" bind:checked={settings.showPitchRoll} />
              <span class="slider"></span>
            </label>
          </div>
        {/if}

        <!-- Tactical Map Settings -->
        {#if settings.showMapWidget}
          <div class="setting-section sub-section">
            <span class="section-title">TACTICAL MAP SETTINGS</span>

            <div class="input-group">
              <label for="distance-unit" class="input-label">
                <span class="label-title">Distance Unit</span>
                <span class="label-desc">Unit for triangulation measurement</span>
              </label>
              <select id="distance-unit" bind:value={settings.distanceUnit} class="select-input">
                <option value="km">Kilometers (Km)</option>
                <option value="nm">Nautical Miles (NM)</option>
              </select>
            </div>

            <div class="input-group">
              <label for="map-mode" class="input-label">
                <span class="label-title">Map Display Mode</span>
                <span class="label-desc">Display map as a free-floating widget or fullscreen overlay</span>
              </label>
              <select id="map-mode" bind:value={settings.mapWindowMode} class="select-input">
                <option value="draggable">Draggable Widget</option>
                <option value="fullscreen">Fullscreen Map Overlay</option>
              </select>
            </div>
          </div>
        {/if}

        <!-- Section: AI Co-pilot Settings -->
        {#if settings.showAiCopilotWidget}
          <div class="setting-section sub-section">
            <span class="section-title">AI CO-PILOT CONFIGURATION</span>

            <label class="toggle-row">
              <span class="toggle-label">🗣️ Enable Voice (Text-to-Speech)</span>
              <input type="checkbox" bind:checked={settings.aiTtsEnabled} />
              <span class="slider"></span>
            </label>

            {#if settings.aiTtsEnabled}
              <div class="input-group">
                <label for="ai-tts-provider" class="input-label">
                  <span class="label-title">Voice Provider</span>
                  <span class="label-desc">Choose Local (Robotic/Free) or OpenAI (Human/Paid)</span>
                </label>
                <select id="ai-tts-provider" bind:value={settings.aiTtsProvider} class="select-input">
                  <option value="local">Local System Voice</option>
                  <option value="google">Google Cloud (Free, Basic)</option>
                  <option value="openai">OpenAI TTS (Requires API Key)</option>
                  <option value="gemini">Google Gemini TTS (Requires API Key)</option>
                </select>
              </div>

              {#if settings.aiTtsProvider === 'local'}
                <div class="input-group">
                  <label for="ai-voice" class="input-label">
                    <span class="label-title">Select Local Voice</span>
                    <span class="label-desc">Choose the text-to-speech voice</span>
                  </label>
                  <select id="ai-voice" bind:value={settings.aiVoiceURI} class="select-input">
                    <option value="">Default System Voice</option>
                    {#each availableVoices as voice}
                      <option value={voice.voiceURI}>{voice.name} ({voice.lang})</option>
                    {/each}
                  </select>
                </div>
              {:else if settings.aiTtsProvider === 'openai'}
                <div class="input-group">
                  <label for="ai-openai-voice" class="input-label">
                    <span class="label-title">OpenAI Voice Persona</span>
                    <span class="label-desc">Choose the premium voice model</span>
                  </label>
                  <select id="ai-openai-voice" bind:value={settings.aiOpenAiVoice} class="select-input">
                    <option value="onyx">Onyx (Deep, Authoritative)</option>
                    <option value="echo">Echo (Neutral, Clear)</option>
                    <option value="alloy">Alloy (Versatile)</option>
                    <option value="fable">Fable (Expressive)</option>
                    <option value="nova">Nova (Energetic)</option>
                    <option value="shimmer">Shimmer (Clear, Calm)</option>
                  </select>
                </div>
              {:else if settings.aiTtsProvider === 'gemini'}
                <div class="input-group">
                  <label for="ai-gemini-voice" class="input-label">
                    <span class="label-title">Gemini Voice Persona</span>
                    <span class="label-desc">Choose the premium voice model</span>
                  </label>
                  <select id="ai-gemini-voice" bind:value={settings.aiGeminiVoice} class="select-input">
                    <option value="Puck">Puck</option>
                    <option value="Charon">Charon</option>
                    <option value="Kore">Kore</option>
                    <option value="Fenrir">Fenrir</option>
                    <option value="Aoede">Aoede</option>
                  </select>
                </div>
              {/if}

              <label class="toggle-row">
                <div class="toggle-info">
                  <span class="toggle-label">📻 Tower Radio Distortion</span>
                  <span class="toggle-desc">Applies pitch shifts to sound like an ATC tower (Can sound robotic)</span>
                </div>
                <input type="checkbox" bind:checked={settings.aiVoiceDistortion} />
                <span class="slider"></span>
              </label>
            {/if}

            <label class="toggle-row">
              <span class="toggle-label">🎤 Auto-Send Voice Commands</span>
              <input type="checkbox" bind:checked={settings.aiVoiceAutoSend} />
              <span class="slider"></span>
            </label>

            <div class="input-group">
              <label for="ai-provider" class="input-label">
                <span class="label-title">API Provider</span>
                <span class="label-desc">Select AI backend service</span>
              </label>
              <select id="ai-provider" bind:value={settings.aiApiProvider} class="select-input">
                <option value="openai">OpenAI (ChatGPT)</option>
                <option value="google">Google (Gemini)</option>
                <option value="custom">Custom (Local LLM)</option>
              </select>
            </div>

            <div class="input-group">
              <label for="ai-api-key" class="input-label">
                <span class="label-title">API Key</span>
                <span class="label-desc">Your secret API key (stored locally)</span>
              </label>
              <input
                id="ai-api-key"
                type="password"
                bind:value={settings.aiApiKey}
                placeholder="sk-..."
                class="text-input"
              />
            </div>

            <div class="input-group">
              <label for="ai-model" class="input-label">
                <span class="label-title">Model Name</span>
                <span class="label-desc">Model ID to use for inference</span>
              </label>
              <input
                id="ai-model"
                type="text"
                bind:value={settings.aiModel}
                placeholder="e.g. gpt-4o-mini"
                class="text-input"
              />
            </div>

            {#if settings.aiApiProvider === 'custom'}
              <div class="input-group">
                <label for="ai-custom-url" class="input-label">
                  <span class="label-title">Custom Endpoint URL</span>
                  <span class="label-desc">Base URL for OpenAI-compatible API</span>
                </label>
                <input
                  id="ai-custom-url"
                  type="text"
                  bind:value={settings.aiCustomEndpoint}
                  placeholder="http://localhost:11434/v1"
                  class="text-input"
                />
              </div>
            {/if}
          </div>
        {/if}

        <!-- Section 3: Chat Translation Settings -->
        {#if settings.showChatWidget}
          <div class="setting-section sub-section">
            <span class="section-title">CHAT TRANSLATION OPTIONS</span>

            <label class="toggle-row">
              <span class="toggle-label">🌐 Show Auto-Translation Box</span>
              <input type="checkbox" bind:checked={settings.showAutoTranslation} />
              <span class="slider"></span>
            </label>

            <label class="toggle-row">
              <span class="toggle-label">🙈 Hide Box if Message Matches Target Language</span>
              <input type="checkbox" bind:checked={settings.ignoreSameLanguage} />
              <span class="slider"></span>
            </label>

            <div class="select-row">
              <span class="select-label">🗣️ Target Language</span>
              <select bind:value={settings.targetLanguage} class="lang-select">
                {#each SUPPORTED_LANGUAGES as lang}
                  <option value={lang.code}>{lang.name}</option>
                {/each}
              </select>
            </div>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        <button class="reset-btn" onclick={resetToDefaults}>Reset Defaults</button>
        <button class="done-btn" onclick={onClose}>Done</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(8px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  }

  .modal-content {
    width: 90%;
    max-width: 480px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    padding: 18px 20px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 12px;
    margin-bottom: 14px;
  }

  .title-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .gear-icon {
    font-size: 1.1rem;
  }

  .modal-title {
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: var(--accent-color);
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 1rem;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .close-btn:hover {
    color: var(--danger-color);
  }

  .settings-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-right: 4px;
  }

  .settings-body::-webkit-scrollbar {
    width: 4px;
  }
  .settings-body::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
  }

  .setting-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .input-label {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .label-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .label-desc {
    font-size: 0.72rem;
    color: var(--text-muted);
  }

  .text-input {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    outline: none;
    transition: all 0.25s ease;
  }

  .text-input:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
  }

  .setting-section.sub-section {
    background: rgba(0, 0, 0, 0.15);
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    border-radius: 10px;
  }

  .section-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }

  .toggle-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }

  .toggle-row.master-toggle {
    background: rgba(255, 255, 255, 0.03);
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }

  .toggle-info {
    display: flex;
    flex-direction: column;
  }

  .toggle-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .toggle-desc {
    font-size: 0.68rem;
    color: var(--text-secondary);
  }

  .select-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    margin-top: 4px;
    border-top: 1px dashed var(--border-color);
  }

  .select-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .lang-select {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    cursor: pointer;
  }

  .lang-select:hover {
    border-color: var(--border-glow);
  }

  .lang-select option {
    background: #0f172a;
    color: #ffffff;
  }

  /* Custom Switch Toggle styling */
  .toggle-row input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
    background-color: rgba(255, 255, 255, 0.15);
    transition: 0.25s;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 14px;
    width: 14px;
    left: 2px;
    bottom: 2px;
    background-color: var(--text-secondary);
    transition: 0.25s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: var(--accent-color);
    border-color: var(--accent-color);
    box-shadow: var(--accent-glow);
  }

  input:checked + .slider:before {
    transform: translateX(16px);
    background-color: #0f172a;
  }

  .modal-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid var(--border-color);
    padding-top: 12px;
    margin-top: 14px;
  }

  .reset-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .reset-btn:hover {
    color: var(--warning-color);
    border-color: var(--warning-color);
  }

  .done-btn {
    background: var(--accent-color);
    color: #0f172a;
    border: none;
    font-weight: 700;
    padding: 6px 16px;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .done-btn:hover {
    background: var(--accent-hover);
  }

  .keybind-recorder {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .keybind-input {
    font-family: monospace;
    font-weight: 700;
    text-align: center;
    color: var(--accent-color);
    letter-spacing: 0.05em;
    cursor: pointer;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 6px 12px;
    width: 160px;
  }

  .keybind-input:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 10px var(--accent-glow);
  }

  .reset-keybind-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    border-radius: 6px;
    padding: 6px 10px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }

  .reset-keybind-btn:hover {
    color: var(--text-primary);
    border-color: var(--accent-color);
  }

  .color-picker-wrapper {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .color-input {
    -webkit-appearance: none;
    appearance: none;
    border: 1px solid var(--border-color);
    width: 38px;
    height: 34px;
    border-radius: 6px;
    cursor: pointer;
    background: transparent;
    padding: 2px;
  }

  .color-input::-webkit-color-swatch-wrapper {
    padding: 0;
  }

  .color-input::-webkit-color-swatch {
    border: none;
    border-radius: 4px;
  }

  .color-hex {
    font-family: monospace;
    font-size: 0.85rem;
    color: var(--text-secondary);
    min-width: 70px;
  }

  .range-input {
    width: 100%;
    max-width: 260px;
    accent-color: var(--accent-color);
    cursor: pointer;
  }

  .custom-css-textarea {
    font-family: 'Consolas', 'Fira Code', monospace;
    font-size: 0.8rem;
    line-height: 1.4;
    width: 100%;
    resize: vertical;
    box-sizing: border-box;
  }
</style>
