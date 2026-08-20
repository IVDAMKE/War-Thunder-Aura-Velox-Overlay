<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  import { WebviewWindow, getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
  import { getCurrentWindow } from '@tauri-apps/api/window';
  import { LogicalSize, PhysicalSize, PhysicalPosition } from '@tauri-apps/api/dpi';
  import { page } from '$app/stores';
  import type { GameStatus, TelemetryPayload, TranslatedChatMessage, HudMsgPayload } from '$lib/types/telemetry';
  import { DEFAULT_SETTINGS, type InterfaceSettings } from '$lib/types/settings';

  import HeaderControl from '$lib/components/HeaderControl.svelte';
  import TelemetryHud from '$lib/components/TelemetryHud.svelte';
  import ChatWidget from '$lib/components/ChatWidget.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';
  import StatsCalculator from '$lib/components/StatsCalculator.svelte';
  import TacticalMap from '$lib/components/TacticalMap.svelte';
  import ObjectivesPanel from '$lib/components/ObjectivesPanel.svelte';
  import AiCopilotWidget from '$lib/components/AiCopilotWidget.svelte';
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

  // Standalone mode state
  let widgetMode = $derived($page.url.searchParams.get('widget'));

  async function popOutWidget(widgetId: string, title: string, settingKey: keyof InterfaceSettings) {
    try {
      // In a browser environment, fallback to window.open
      if (!(window as any).__TAURI_INTERNALS__) {
        window.open(`/?widget=${widgetId}`, `widget-${widgetId}`, 'width=400,height=400');
        (settings as any)[settingKey] = false;
        return;
      }

      const webview = new WebviewWindow(`widget-${widgetId}`, {
        url: `/?widget=${widgetId}`,
        title: title,
        transparent: true,
        decorations: false,
        alwaysOnTop: true,
        width: 400,
        height: 400,
        minWidth: 200,
        minHeight: 200
      });
      
      webview.once('tauri://created', () => {
        (settings as any)[settingKey] = false;
      });

      webview.once('tauri://error', (e) => {
        triggerToast(`Error creating window: ${e.payload}`);
      });

      webview.once('tauri://close-requested', () => {
        (settings as any)[settingKey] = true;
      });
    } catch (e: any) {
      triggerToast(`Popout failed: ${e.message || e}`);
    }
  }

  function closeStandaloneWindow() {
    if (!(window as any).__TAURI_INTERNALS__) {
      window.close();
      return;
    }
    getCurrentWebviewWindow().close();
  }

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
      const keyCombo = settings.shortcutToggleClickThrough || 'Ctrl+Shift+X';
      if (isClickThrough) {
        triggerToast(`Click-Through Mode Active: Mouse passes to game (Press ${keyCombo} or Esc to return)`, 4000);
      } else {
        triggerToast('Interactive Mode Restored - Window controls active.', 3000);
      }
    } catch (e) {
      console.warn('Failed to toggle click through:', e);
    }
  }

  function toggleClickThrough() {
    setClickThrough(!isClickThrough);
  }

  function matchShortcut(e: KeyboardEvent, shortcutString: string): boolean {
    if (!shortcutString) return false;
    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return false;

    const parts: string[] = [];
    if (e.ctrlKey) parts.push('Ctrl');
    if (e.altKey) parts.push('Alt');
    if (e.shiftKey) parts.push('Shift');
    if (e.metaKey) parts.push('Win');

    let key = e.key;
    if (key === ' ') key = 'Space';
    else if (key.length === 1) key = key.toUpperCase();

    parts.push(key);
    const pressed = parts.join('+');

    return pressed.toLowerCase() === shortcutString.trim().toLowerCase();
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

  // Helper to convert hex color and opacity float to rgba string
  function hexToRgba(hex: string, alpha: number): string {
    if (!hex || !hex.startsWith('#')) return `rgba(18, 24, 38, ${alpha})`;
    let c = hex.substring(1);
    if (c.length === 3) c = c.split('').map(x => x + x).join('');
    const num = parseInt(c, 16);
    if (isNaN(num)) return `rgba(18, 24, 38, ${alpha})`;
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  // Apply Window Launch Mode (Full Screen vs Last Saved Position & Size)
  async function applyWindowLaunchMode() {
    if (widgetMode || !(window as any).__TAURI_INTERNALS__) return;
    const appWin = getCurrentWindow();

    if (settings.windowLaunchMode === 'fullscreen') {
      try {
        await appWin.setFullscreen(true);
      } catch (e) {
        try {
          await appWin.setSize(new LogicalSize(window.screen.width, window.screen.height));
          await appWin.setPosition(new PhysicalPosition(0, 0));
        } catch (e2) {
          console.warn('Could not set fullscreen size:', e2);
        }
      }
    } else if (settings.windowLaunchMode === 'lastPosition') {
      try {
        await appWin.setFullscreen(false);
        if (settings.savedWindowSize?.w && settings.savedWindowSize?.h) {
          await appWin.setSize(new PhysicalSize(settings.savedWindowSize.w, settings.savedWindowSize.h));
        }
        if (settings.savedWindowPosition?.x !== undefined && settings.savedWindowPosition?.y !== undefined) {
          await appWin.setPosition(new PhysicalPosition(settings.savedWindowPosition.x, settings.savedWindowPosition.y));
        }
      } catch (e) {
        console.warn('Could not restore window position/size:', e);
      }
    }
  }

  $effect(() => {
    applyWindowLaunchMode();
  });

  // Save window position & size when user moves or resizes the main window
  $effect(() => {
    if (widgetMode || !(window as any).__TAURI_INTERNALS__) return;

    let unlistenMove: any;
    let unlistenResize: any;

    async function trackTransform() {
      try {
        const appWin = getCurrentWindow();
        unlistenMove = await appWin.onMoved(({ payload: position }) => {
          settings.savedWindowPosition = { x: position.x, y: position.y };
        });
        unlistenResize = await appWin.onResized(({ payload: size }) => {
          settings.savedWindowSize = { w: size.width, h: size.height };
        });
      } catch (e) {
        console.warn('Could not attach transform listeners:', e);
      }
    }

    trackTransform();

    return () => {
      if (unlistenMove) unlistenMove();
      if (unlistenResize) unlistenResize();
    };
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
      // Configurable Click Through Shortcut
      if (matchShortcut(e, settings.shortcutToggleClickThrough || 'Ctrl+Shift+X')) {
        e.preventDefault();
        toggleClickThrough();
      }
      // Esc -> Exit Click Through if active
      if (e.key === 'Escape' && isClickThrough) {
        e.preventDefault();
        setClickThrough(false);
      }
      // Configurable Settings / Header Bar Shortcut
      if (matchShortcut(e, settings.shortcutToggleSettings || 'Ctrl+Shift+S')) {
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
          if (!event.payload.sender) return; // Filter out combat logs
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

<main
  class="app-layout"
  style="
    {settings.overlayAccentColor ? `--accent-color: ${settings.overlayAccentColor}; --accent-hover: ${settings.overlayAccentColor}; --accent-glow: 0 0 16px ${settings.overlayAccentColor}66;` : ''}
    {settings.overlayBgColor && settings.overlayOpacity !== undefined ? `--bg-card: ${hexToRgba(settings.overlayBgColor, settings.overlayOpacity)}; --bg-card-hover: ${hexToRgba(settings.overlayBgColor, Math.min(1, settings.overlayOpacity + 0.1))};` : ''}
    {settings.overlayCardRadius !== undefined ? `--card-radius: ${settings.overlayCardRadius}px;` : ''}
    {settings.overlayBackdropBlur !== undefined ? `--backdrop-blur: blur(${settings.overlayBackdropBlur}px);` : ''}
  "
>
  {#if settings.customCss}
    {@html `<style>${settings.customCss}</style>`}
  {/if}
  {#if widgetMode}
    <div class="standalone-container">
      <div
        class="standalone-header"
        data-tauri-drag-region
        onmousedown={async (e) => {
          if (e.button === 0) {
            try {
              await getCurrentWindow().startDragging();
            } catch (err) {
              try { await invoke('start_drag'); } catch (err2) {}
            }
          }
        }}
        role="presentation"
      >
        <span class="standalone-title" data-tauri-drag-region>
          {#if widgetMode === 'map'}Tactical Map
          {:else if widgetMode === 'chat'}Live Chat
          {:else if widgetMode === 'telemetryHud'}Live Telemetry
          {:else if widgetMode === 'stats'}Combat Stats
          {:else if widgetMode === 'objectives'}Match Objectives
          {:else if widgetMode === 'aiCopilot'}AI Co-pilot
          {/if}
        </span>
        <button 
          class="standalone-close" 
          style="-webkit-app-region: no-drag;" 
          onpointerdown={(e) => { e.stopPropagation(); closeStandaloneWindow(); }}
          title="Close Window"
        ><span class="material-symbols-outlined">close</span></button>
      </div>
      
      <div class="standalone-content">
        {#if widgetMode === 'map'}
          <div class="widget-map-container" style="width: 100%; height: 100%;">
            <TacticalMap {settings} {chatLog} />
          </div>
        {:else if widgetMode === 'chat'}
          <ChatWidget {chatLog} {settings} />
        {:else if widgetMode === 'telemetryHud'}
          <TelemetryHud telemetry={telemetryPayload} {settings} />
        {:else if widgetMode === 'stats'}
          <StatsCalculator {lastChatMessage} {lastHudMsg} {settings} />
        {:else if widgetMode === 'objectives'}
          <ObjectivesPanel {settings} />
        {:else if widgetMode === 'aiCopilot'}
          <AiCopilotWidget {settings} telemetry={telemetryPayload} />
        {/if}
      </div>
    </div>
  {:else}
  <!-- Auto-Disappearing Mode & Info Toast Banner -->
  {#if showToast}
    <div class="toast-banner" class:click-through={isClickThrough}>
      <span class="toast-icon"><span class="material-symbols-outlined">{isClickThrough ? 'lock' : 'auto_awesome'}</span></span>
      <span class="toast-text">{toastMessage}</span>
    </div>
  {/if}

  <div class="overlay-container">
    {#if settings.showHeader}
      <HeaderControl
        {status}
        {isClickThrough}
        idleFadeTime={settings.idleFadeTime}
        idleFadeOpacity={settings.idleFadeOpacity}
        compactMode={settings.compactMode}
        shortcutClickThrough={settings.shortcutToggleClickThrough || 'Ctrl+Shift+X'}
        shortcutSettings={settings.shortcutToggleSettings || 'Ctrl+Shift+S'}
        onToggleClickThrough={toggleClickThrough}
        onOpenSettings={() => isSettingsOpen = true}
      />
    {:else}
      <button
        class="header-restore-btn"
        onclick={() => isSettingsOpen = true}
        title="Open Settings and restore Top Header Bar ({settings.shortcutToggleSettings || 'Ctrl+Shift+S'})"
      >
        <span class="material-symbols-outlined">settings</span>
      </button>
    {/if}

    <div class="freeform-canvas">
      {#if settings.showTelemetryHud}
        <DraggableWidget 
          bind:bounds={settings.hudBounds} 
          title="Live Telemetry" 
          icon="📊"
          idleFadeTime={settings.idleFadeTime}
          idleFadeOpacity={settings.idleFadeOpacity}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('telemetryHud', 'Live Telemetry', 'showTelemetryHud')}
        >
          <TelemetryHud telemetry={telemetryPayload} {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showStatsWidget}
        <DraggableWidget 
          bind:bounds={settings.statsBounds} 
          title="Combat Stats" 
          icon="⚔️"
          idleFadeTime={settings.idleFadeTime}
          idleFadeOpacity={settings.idleFadeOpacity}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('stats', 'Combat Stats', 'showStatsWidget')}
        >
          <StatsCalculator {lastChatMessage} {lastHudMsg} {settings} />
        </DraggableWidget>
      {/if}
      
      {#if settings.showObjectivesWidget}
        <DraggableWidget 
          bind:bounds={settings.objectivesBounds} 
          title="Match Objectives" 
          icon="🎯"
          idleFadeTime={settings.idleFadeTime}
          idleFadeOpacity={settings.idleFadeOpacity}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('objectives', 'Match Objectives', 'showObjectivesWidget')}
        >
          <ObjectivesPanel {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showChatWidget}
        <DraggableWidget 
          bind:bounds={settings.chatBounds} 
          title="Live Chat & Translation" 
          icon="💬"
          idleFadeTime={settings.idleFadeTime}
          idleFadeOpacity={settings.idleFadeOpacity}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('chat', 'Live Chat & Translation', 'showChatWidget')}
        >
          <ChatWidget {chatLog} {settings} />
        </DraggableWidget>
      {/if}

      {#if settings.showMapWidget}
        <DraggableWidget 
          bind:bounds={settings.mapBounds} 
          title="Tactical Map" 
          icon="🗺️"
          neverFade={true}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('map', 'Tactical Map', 'showMapWidget')}
        >
          <div class="widget-map-container" class:fullscreen-map={settings.mapWindowMode === 'fullscreen'}>
            <TacticalMap {settings} {chatLog} />
          </div>
        </DraggableWidget>
      {/if}

      {#if settings.showAiCopilotWidget}
        <DraggableWidget 
          bind:bounds={settings.aiCopilotBounds} 
          title="AI Co-pilot" 
          icon="🤖"
          idleFadeTime={settings.idleFadeTime}
          idleFadeOpacity={settings.idleFadeOpacity}
          compactMode={settings.compactMode}
          onPopOut={() => popOutWidget('aiCopilot', 'AI Co-pilot', 'showAiCopilotWidget')}
        >
          <AiCopilotWidget {settings} telemetry={telemetryPayload} />
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
  {/if}
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
  .standalone-container {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
    backdrop-filter: var(--backdrop-blur);
    -webkit-backdrop-filter: var(--backdrop-blur);
    border: 1px solid var(--border-color);
    box-sizing: border-box;
    overflow: hidden;
  }

  .standalone-header {
    height: 32px;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    padding: 0 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    user-select: none;
    flex-shrink: 0;
  }

  .standalone-title {
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    flex: 1;
    cursor: default;
  }

  .standalone-close {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    font-size: 14px;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s, color 0.2s;
    line-height: 1;
    z-index: 10;
  }

  .standalone-close:hover {
    background: rgba(255, 50, 50, 0.8);
    color: #fff;
  }

  .standalone-content {
    flex: 1;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: stretch;
  }
</style>
