<script lang="ts">
  import type { WidgetBounds } from '../types/settings';
  import type { Snippet } from 'svelte';
  import { onMount, onDestroy } from 'svelte';

  let {
    bounds = $bindable(),
    title = '',
    icon = '',
    neverFade = false,
    idleFadeTime = 15,
    idleFadeOpacity = 0.33,
    compactMode = false,
    onPopOut,
    children
  }: {
    bounds: WidgetBounds;
    title?: string;
    icon?: string;
    neverFade?: boolean;
    idleFadeTime?: number;
    idleFadeOpacity?: number;
    compactMode?: boolean;
    onPopOut?: () => void;
    children: Snippet;
  } = $props();

  let isDragging = $state(false);
  let isResizing = $state(false);
  
  let startX = 0;
  let startY = 0;
  let initialBounds = { x: 0, y: 0, w: 0, h: 0 };

  // --- IDLE LOGIC ---
  let idleTimeout: ReturnType<typeof setTimeout>;
  let isIdle = $state(false);
  let widgetContainer: HTMLDivElement | null = $state(null);
  let observer: MutationObserver | null = null;

  function resetIdle() {
    isIdle = false;
    clearTimeout(idleTimeout);
    if (neverFade) return;
    
    idleTimeout = setTimeout(() => {
      if (!isDragging && !isResizing) {
        isIdle = true;
      }
    }, idleFadeTime * 1000);
  }

  onMount(() => {
    resetIdle();
    if (widgetContainer) {
      observer = new MutationObserver(() => resetIdle());
      observer.observe(widgetContainer, { childList: true, subtree: true, characterData: true });
    }
  });

  onDestroy(() => {
    clearTimeout(idleTimeout);
    if (observer) observer.disconnect();
  });

  function handlePointerDown(e: PointerEvent, mode: 'drag' | 'resize') {
    // Only allow left click
    if (e.button !== 0) return;
    
    e.preventDefault();
    e.stopPropagation();

    startX = e.clientX;
    startY = e.clientY;
    initialBounds = { ...bounds };

    if (mode === 'drag') {
      isDragging = true;
    } else {
      isResizing = true;
    }

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
  }

  function handlePointerMove(e: PointerEvent) {
    if (isDragging) {
      bounds.x = initialBounds.x + (e.clientX - startX);
      bounds.y = initialBounds.y + (e.clientY - startY);
    } else if (isResizing) {
      bounds.w = Math.max(150, initialBounds.w + (e.clientX - startX));
      bounds.h = Math.max(100, initialBounds.h + (e.clientY - startY));
    }
  }

  function handlePointerUp() {
    isDragging = false;
    isResizing = false;
    window.removeEventListener('pointermove', handlePointerMove);
    window.removeEventListener('pointerup', handlePointerUp);
  }
</script>

<div
  bind:this={widgetContainer}
  class="draggable-widget {isIdle ? 'idle' : ''} {compactMode ? 'compact' : ''}"
  style="left: {bounds.x}px; top: {bounds.y}px; width: {bounds.w}px; height: {bounds.h}px; --idle-opacity: {idleFadeOpacity};"
  onpointermove={resetIdle}
  role="presentation"
>
  <div
    class="widget-header"
    role="presentation"
    onpointerdown={(e) => handlePointerDown(e, 'drag')}
  >
    <div class="drag-handle">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
        <circle cx="2" cy="2" r="1.5" />
        <circle cx="6" cy="2" r="1.5" />
        <circle cx="10" cy="2" r="1.5" />
        <circle cx="2" cy="6" r="1.5" />
        <circle cx="6" cy="6" r="1.5" />
        <circle cx="10" cy="6" r="1.5" />
        <circle cx="2" cy="10" r="1.5" />
        <circle cx="6" cy="10" r="1.5" />
        <circle cx="10" cy="10" r="1.5" />
      </svg>
    </div>
    {#if !compactMode && (icon || title)}
      <span class="widget-title">
        {#if icon}{icon} {/if}{title}
      </span>
    {/if}
    
    <div style="flex: 1;"></div>
    
    {#if onPopOut}
      <button 
        class="pop-out-btn" 
        onpointerdown={(e) => { e.stopPropagation(); onPopOut(); }} 
        title="Pop out into separate window"
      >
        <span class="material-symbols-outlined">open_in_new</span>
      </button>
    {/if}
  </div>

  <div class="widget-content">
    {@render children()}
  </div>

  <div
    class="resize-handle"
    role="presentation"
    onpointerdown={(e) => handlePointerDown(e, 'resize')}
  >
    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
      <path d="M12 0 L12 12 L0 12 Z" opacity="0.3" />
      <path d="M12 6 L12 12 L6 12 Z" opacity="0.6" />
      <path d="M12 10 L12 12 L10 12 Z" />
    </svg>
  </div>
</div>

<style>
  .draggable-widget {
    position: absolute;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--card-radius);
    display: flex;
    flex-direction: column;
    backdrop-filter: var(--backdrop-blur);
    -webkit-backdrop-filter: var(--backdrop-blur);
    box-shadow: var(--shadow-card);
    pointer-events: auto;
    overflow: hidden;
    transition: box-shadow 0.2s ease, border-color 0.2s ease, opacity 0.5s ease, background 0.25s ease, border-radius 0.25s ease;
    opacity: 1;
  }

  .draggable-widget.idle {
    opacity: var(--idle-opacity, 0.33);
  }

  .draggable-widget.compact {
    background: transparent;
    border: none;
    box-shadow: none;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }

  .draggable-widget.compact .widget-header {
    background: transparent;
    border-bottom: none;
  }
  
  .draggable-widget.compact .drag-handle {
    opacity: 0.3;
  }
  
  .draggable-widget.compact:hover .drag-handle {
    opacity: 1;
  }
  
  .draggable-widget.compact .pop-out-btn {
    opacity: 0.3;
  }
  
  .draggable-widget.compact:hover .pop-out-btn {
    opacity: 1;
  }

  /* Override inner overlay-cards so glassmorphism isn't doubled */
  .draggable-widget :global(.overlay-card) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
  }

  .draggable-widget:hover {
    border-color: var(--border-glow);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
  }

  .widget-header {
    height: 28px;
    background: rgba(0, 0, 0, 0.25);
    display: flex;
    align-items: center;
    padding: 0 8px;
    cursor: grab;
    border-bottom: 1px solid var(--border-color);
    user-select: none;
    flex-shrink: 0;
  }

  .pop-out-btn {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.2s, color 0.2s;
    line-height: 1;
  }

  .pop-out-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }

  .widget-header:active {
    cursor: grabbing;
  }

  .drag-handle {
    color: rgba(255, 255, 255, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 8px;
  }

  .widget-header:hover .drag-handle {
    color: rgba(255, 255, 255, 0.8);
  }

  .widget-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.6);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .widget-content {
    flex: 1;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  /* Make sure children components fill the widget completely */
  .widget-content :global(> div) {
    width: 100%;
    height: 100%;
    box-sizing: border-box;
  }

  .resize-handle {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 16px;
    height: 16px;
    cursor: nwse-resize;
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    padding: 2px;
    color: rgba(255, 255, 255, 0.3);
    z-index: 100;
  }

  .resize-handle:hover {
    color: rgba(255, 255, 255, 0.8);
  }
</style>
