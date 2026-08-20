import json

svelte_content = """<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  import type { GameStatus, TelemetryPayload, TranslatedChatMessage, HudMsgPayload } from '$lib/types/telemetry';
  import { DEFAULT_SETTINGS, type InterfaceSettings } from '$lib/types/settings';

  import HeaderControl from '$lib/components/HeaderControl.svelte';
  import TelemetryHud from '$lib/components/TelemetryHud.svelte';
  import ChatWidget from '$lib/components/ChatWidget.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';
  import StatsCalculator from '$lib/components/StatsCalculator.svelte';
  import TacticalMap from '$lib/components/TacticalMap.svelte';
  import ObjectivesPanel from '$lib/components/ObjectivesPanel.svelte';
  import DraggableWidget from '$lib/components/DraggableWidget.svelte';

  // Svelte 5 $state runes
  let status = $state<GameStatus | null>({
    game_running: false,
    connected: false,
    message: 'Initializing assistant...'
  });
  
  let telemetryPayload = $state<TelemetryPayload | null>(null);
  let chatLog = $state<TranslatedChatMessage[]>([]);
  let lastChatMessage = $state<TranslatedChatMessage | null>(null);
  let lastHudMsg = $state<HudMsgPayload | null>(null);

  // Click-through & Toast State
  let isClickThrough = $state(false);
  let showToast = $state(false);
  let toastMessage = $state('');
  let toastTimeout: any = null;

  let isSettingsOpen = $state(false);
  let settings = $state<InterfaceSettings>(DEFAULT_SETTINGS);

  function triggerToast(msg: string, duration = 3000) {
    toastMessage = msg;
    showToast = true;
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      showToast = false;
    }, duration);
  }

  async function setClickThrough(enable: boolean) {
    try {
      await invoke('toggle_click_through', { ignore: enable });
      isClickThrough = enable;
      if (!isClickThrough) {
        triggerToast('Interactive Mode Restored - Window controls active.', 3000);
      }
    } catch (e) {
      console.warn('Failed to toggle click through:', e);
    }
  }

  function toggleClickThrough() {
    setClickThrough(!isClickThrough);
  }

  // Ensure interactive mode on mount
  $effect(() => {
    try {
      invoke('toggle_click_through', { ignore: false });
    } catch (e) {
      console.warn('Could not reset click-through on mount:', e);
    }
  });

  // Load settings on mount
  $effect(() => {
    try {
      const saved = localStorage.getItem('wt_assistant_settings');
      if (saved) {
        settings = { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.warn('Failed to load settings from localStorage:', e);
    }
  });

  // Save settings on update
  $effect(() => {
    try {
      localStorage.setItem('wt_assistant_settings', JSON.stringify(settings));
    } catch (e) {
      console.warn('Failed to save settings to localStorage:', e);
    }
  });

  // Global Keyboard Listener for Shortcuts
  $effect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ctrl + Shift + X -> Toggle Click Through
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'x') {
        e.preventDefault();
        toggleClickThrough();
      }
      // Esc -> Exit Click Through if active
      if (e.key === 'Escape' && isClickThrough) {
        e.preventDefault();
        setClickThrough(false);
      }
      // Ctrl + Shift + S -> Toggle Settings Modal
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        isSettingsOpen = !isSettingsOpen;
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  // Setup Tauri Listeners or Web Fallback
  $effect(() => {
    let unlistenStatus: any;
    let unlistenTelemetry: any;
    let unlistenChat: any;
    let unlistenHud: any;

    async function setupListeners() {
      try {
        unlistenStatus = await listen<GameStatus>('wt-status', (event) => {
          status = event.payload;
        });

        unlistenTelemetry = await listen<TelemetryPayload>('wt-telemetry', (event) => {
          telemetryPayload = event.payload;
        });

        unlistenChat = await listen<TranslatedChatMessage>('wt-chat', (event) => {
          lastChatMessage = event.payload;
          if (!chatLog.some(c => c.id === event.payload.id)) {
            chatLog = [...chatLog, event.payload];
          }
        });

        unlistenHud = await listen<HudMsgPayload>('wt-hudmsg', (event) => {
          lastHudMsg = event.payload;
        });
      } catch (err) {
        console.warn('Tauri event listener not active (running in web browser view):', err);
        startWebFallbackPolling();
      }
    }

    setupListeners();

    return () => {
      if (unlistenStatus) unlistenStatus();
      if (unlistenTelemetry) unlistenTelemetry();
      if (unlistenChat) unlistenChat();
      if (unlistenHud) unlistenHud();
    };
  });

  function startWebFallbackPolling() {
    const interval = setInterval(async () => {
      try {
        const stateRes = await fetch('http://127.0.0.1:8111/state');
        const indRes = await fetch('http://127.0.0.1:8111/indicators');
        if (stateRes.ok && indRes.ok) {
          const state = await stateRes.json();
          const indicators = await indRes.json();
          telemetryPayload = { state, indicators };
          status = {
            game_running: true,
            connected: true,
            message: 'Connected to 127.0.0.1:8111'
          };
        }
      } catch {
        status = {
          game_running: false,
          connected: false,
          message: 'Web fallback polling waiting for 127.0.0.1:8111...'
        };
      }
    }, 500);

    return () => clearInterval(interval);
  }
</script>

<main class="app-layout">
  <!-- Click-Through Active Persistent Banner or Auto-Disappearing Restoration Toast -->
  {#if isClickThrough}
    <div class="toast-banner click-through">
      <span class="toast-icon">🔒</span>
      <span class="toast-text">Click-Through Mode Active: Mouse passes to game</span>
      <span class="shortcut-tag">Press Ctrl + Shift + X or Esc to return</span>
    </div>
  {:else if showToast}
    <div class="toast-banner">
      <span class="toast-icon">✨</span>
      <span class="toast-text">{toastMessage}</span>
    </div>
  {/if}

  <div class="overlay-container">
    {#if settings.showHeader}
      <HeaderControl
        {status}
        {isClickThrough}
        onToggleClickThrough={toggleClickThrough}
        onOpenSettings={() => isSettingsOpen = true}
      />
    {:else}
      <button
        class="header-restore-btn"
        onclick={() => isSettingsOpen = true}
        title="Click or press Ctrl+Shift+S to open Settings and restore Top Header Bar"
      >
        ⚙️ Restore Header Bar (Ctrl+Shift+S)
      </button>
    {/if}

    <div class="freeform-canvas">
      {#if settings.showTelemetryHud}
        <DraggableWidget bind:bounds={settings.hudBounds} title="Live Telemetry" icon="📊">
          <TelemetryHud telemetry={telemetryPayload} {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showStatsWidget}
        <DraggableWidget bind:bounds={settings.statsBounds} title="Combat Stats" icon="⚔️">
          <StatsCalculator {lastChatMessage} {lastHudMsg} {settings} />
        </DraggableWidget>
      {/if}
      
      {#if settings.showObjectivesWidget}
        <DraggableWidget bind:bounds={settings.objectivesBounds} title="Match Objectives" icon="🎯">
          <ObjectivesPanel {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showChatWidget}
        <DraggableWidget bind:bounds={settings.chatBounds} title="Live Chat & Translation" icon="💬">
          <ChatWidget {chatLog} {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showMapWidget}
        <DraggableWidget bind:bounds={settings.mapBounds} title="Tactical Map" icon="🗺️">
          <div class="widget-map-container" class:fullscreen-map={settings.mapWindowMode === 'fullscreen'}>
            <TacticalMap {settings} />
          </div>
        </DraggableWidget>
      {/if}
    </div>

    <!-- Visual Corner Resize Grip -->
    <div class="resize-grip" title="Drag edges or corner to resize window">◢</div>
  </div>

  <SettingsModal
    isOpen={isSettingsOpen}
    bind:settings
    onClose={() => isSettingsOpen = false}
  />
</main>

<style>
  .app-layout {
    width: 100vw;
    height: 100vh;
    padding: 10px;
    box-sizing: border-box;
    display: flex;
    justify-content: center;
    align-items: stretch;
    background: transparent;
    overflow: hidden;
    position: relative;
  }

  .toast-banner {
    position: absolute;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid var(--accent-color);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    padding: 6px 16px;
    border-radius: 30px;
    backdrop-filter: blur(12px);
    pointer-events: none;
    animation: fadeInDown 0.3s ease;
  }

  .toast-banner.click-through {
    border-color: #f59e0b;
    box-shadow: 0 0 16px rgba(245, 158, 11, 0.5);
  }

  .toast-icon {
    font-size: 0.95rem;
  }

  .toast-text {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .shortcut-tag {
    background: rgba(245, 158, 11, 0.25);
    color: #fef08a;
    border: 1px solid rgba(245, 158, 11, 0.5);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.05em;
  }

  @keyframes fadeInDown {
    from { opacity: 0; transform: translate(-50%, -10px); }
    to { opacity: 1; transform: translate(-50%, 0); }
  }

  .overlay-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-sizing: border-box;
    position: relative;
  }

  .header-restore-btn {
    align-self: center;
    background: rgba(15, 23, 42, 0.7);
    border: 1px dashed var(--border-color);
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 20px;
    cursor: pointer;
    backdrop-filter: blur(8px);
    transition: all 0.25s ease;
    opacity: 0.5;
  }

  .header-restore-btn:hover {
    opacity: 1;
    color: var(--accent-color);
    border-color: var(--accent-color);
    background: rgba(15, 23, 42, 0.95);
    box-shadow: var(--accent-glow);
  }

  .freeform-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none; /* Let clicks pass through to empty space */
    z-index: 10;
  }

  .widget-map-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .widget-map-container.fullscreen-map {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1;
    pointer-events: auto;
  }

  .resize-grip {
    position: absolute;
    bottom: 2px;
    right: 4px;
    font-size: 0.7rem;
    color: var(--text-muted);
    opacity: 0.5;
    pointer-events: none;
    user-select: none;
  }
</style>
"""

with open("src/routes/+page.svelte", "w", encoding="utf-8") as f:
    f.write(svelte_content)
