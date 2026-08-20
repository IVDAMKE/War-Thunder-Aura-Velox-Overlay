<script lang="ts">
  import type { TranslatedChatMessage } from '../types/telemetry';
  import { DEFAULT_SETTINGS, type InterfaceSettings } from '../types/settings';
  import { getTranslation, isSameLanguage, setTranslationUpdateCallback } from '../utils/translator';

  let {
    chatLog = [],
    settings = DEFAULT_SETTINGS
  }: {
    chatLog?: TranslatedChatMessage[];
    settings?: InterfaceSettings;
  } = $props();

  let activeFilter = $state<'all' | 'team'>('all');
  let chatContainerEl = $state<HTMLDivElement | null>(null);
  let translationRevision = $state(0);

  $effect(() => {
    setTranslationUpdateCallback(() => {
      translationRevision += 1;
    });
  });

  // Svelte 5 $derived rune for filtering chat messages
  let filteredChats = $derived(() => {
    if (activeFilter === 'all') return chatLog;
    if (activeFilter === 'team') {
      return chatLog.filter(c => {
        const m = (c.mode || '').toLowerCase();
        return m === 'team' || m === 'squad' || m === 'all';
      });
    }
    return chatLog;
  });

  // Auto-scroll on new message
  let isScrolledUp = false;

  function handleScroll(e: Event) {
    const target = e.target as HTMLElement;
    isScrolledUp = target.scrollHeight - target.scrollTop - target.clientHeight > 20;
  }

  $effect(() => {
    // React to changes
    chatLog;
    translationRevision;
    
    if (chatContainerEl && !isScrolledUp) {
      setTimeout(() => {
        if (chatContainerEl) chatContainerEl.scrollTop = chatContainerEl.scrollHeight;
      }, 50);
    }
  });

  function parseMessageHtml(text: string) {
    if (!text) return '';
    let safe = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    safe = safe.replace(/&lt;color=(#[0-9A-Fa-f]+)&gt;(.*?)&lt;\/color&gt;/gi, '<span style="color: $1; font-weight: bold;">$2</span>');
    return safe;
  }

  function getModeBadgeClass(mode: string, enemy: boolean): string {
    const m = (mode || '').toLowerCase();
    if (m === 'system') return 'mode-system';
    if (m === 'squad') return 'mode-squad';
    if (enemy) return 'mode-enemy';
    return 'mode-team';
  }
</script>

<div class="overlay-card chat-widget {settings.compactMode ? 'compact' : ''}">
  {#if !settings.compactMode}
    <div class="chat-header">
      <div class="title-row">
        <span class="title">LIVE CHAT & TRANSLATION</span>
        <span class="chat-count">{chatLog.length} msg</span>
      </div>
      <div class="filter-tabs">
        <button class="tab-btn" class:active={activeFilter === 'all'} onclick={() => activeFilter = 'all'}>All</button>
        <button class="tab-btn" class:active={activeFilter === 'team'} onclick={() => activeFilter = 'team'}>Team</button>
      </div>
    </div>
  {/if}

  <div class="chat-feed" bind:this={chatContainerEl} onscroll={handleScroll}>
    {#if filteredChats().length === 0}
      <div class="empty-state">Waiting for game chat messages...</div>
    {:else}
      {#each filteredChats() as chat (chat.id)}
        {@const translation = settings.showAutoTranslation && translationRevision >= 0 ? getTranslation(chat.original, settings.targetLanguage) : ''}
        {@const sameLang = isSameLanguage(chat.original, settings.targetLanguage, translation)}
        {@const showTrans = settings.showAutoTranslation && (!settings.ignoreSameLanguage || !sameLang) && translation}

        <div class="chat-row" class:enemy-row={chat.enemy}>
          <div class="meta-line">
            <span class="mode-badge {getModeBadgeClass(chat.mode, chat.enemy)}">
              {chat.mode.toUpperCase()}
            </span>
            <span class="sender">{chat.sender}</span>
          </div>

          <div class="message-content">
            {#if settings.compactMode}
              <span class="compact-text">{@html parseMessageHtml(showTrans ? translation : chat.original)}</span>
            {:else}
              <span class="original-text">{@html parseMessageHtml(chat.original)}</span>
              {#if showTrans}
                <div class="translated-box">
                  <span class="trans-icon">🌐</span>
                  <span class="translated-text">
                    {@html parseMessageHtml(translation)}
                  </span>
                </div>
              {/if}
            {/if}
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .chat-widget {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 160px;
    box-sizing: border-box;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 6px;
    margin-bottom: 8px;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
  }

  .chat-count {
    font-size: 0.68rem;
    color: var(--text-muted);
    font-family: monospace;
  }

  .filter-tabs {
    display: flex;
    gap: 4px;
  }

  .tab-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    cursor: pointer;
  }

  .tab-btn.active {
    background: rgba(255, 255, 255, 0.1);
    color: var(--accent-color);
    font-weight: 700;
  }

  .chat-feed {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-right: 4px;
  }

  /* Custom scrollbar */
  .chat-feed::-webkit-scrollbar {
    width: 4px;
  }
  .chat-feed::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
  }

  .empty-state {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-style: italic;
    margin: auto;
  }

  .chat-row {
    background: rgba(0, 0, 0, 0.2);
    border-left: 3px solid var(--accent-color);
    padding: 6px 10px;
    border-radius: 0 8px 8px 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .chat-row.enemy-row {
    border-left-color: var(--danger-color);
  }

  .meta-line {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .mode-badge {
    font-size: 0.6rem;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 3px;
  }

  .mode-team { background: rgba(56, 189, 248, 0.2); color: var(--accent-color); }
  .mode-squad { background: rgba(74, 222, 128, 0.2); color: var(--success-color); }
  .mode-enemy { background: rgba(239, 68, 68, 0.2); color: var(--danger-color); }
  .mode-system { background: rgba(251, 191, 36, 0.2); color: var(--warning-color); }

  .sender {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .message-content {
    font-size: 0.78rem;
    line-height: 1.3;
  }

  .original-text {
    color: var(--text-secondary);
  }

  .translated-box {
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 4px;
    background: rgba(56, 189, 248, 0.08);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid rgba(56, 189, 248, 0.15);
  }

  .trans-icon {
    font-size: 0.7rem;
  }

  .translated-text {
    color: var(--accent-color);
    font-weight: 600;
    font-size: 0.75rem;
  }
</style>
