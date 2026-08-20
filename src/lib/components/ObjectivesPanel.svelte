<script lang="ts">
  import type { InterfaceSettings } from '$lib/types/settings';

  let { settings }: { settings: InterfaceSettings } = $props();

  type Objective = { id: number, type: 'primary' | 'secondary', text: string, status: string };
  let objectives = $state<Objective[]>([]);

  $effect(() => {
    let active = true;
    const poll = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8111/mission.json');
        if (res.ok) {
          const data = await res.json();
          if (data.objectives && Array.isArray(data.objectives)) {
            objectives = data.objectives.map((obj: any, idx: number) => {
              // Parse Unity-style rich text tags: <color=#HEX>text</color>
              let parsedText = obj.text || '';
              parsedText = parsedText.replace(/<color=(#[0-9a-fA-F]+)>(.*?)<\/color>/gi, '<span style="color: $1">$2</span>');
              
              return {
                id: idx,
                type: obj.primary ? 'primary' : 'secondary',
                text: parsedText,
                status: obj.status // usually 'in_progress', 'succeed', 'failed'
              };
            });
          }
        }
      } catch (e) {}
      if (active) setTimeout(poll, 2000);
    };
    poll();
    return () => { active = false; };
  });
</script>

<div class="objectives-panel {settings.compactMode ? 'compact' : ''}">
  {#if !settings.compactMode}
    <div class="panel-header">🎯 Match Objectives</div>
  {/if}
  
  <div class="objectives-list">
    {#if objectives.filter(o => o.type === 'primary').length > 0}
      <div class="obj-category">Primary Goals</div>
      {#each objectives.filter(o => o.type === 'primary') as obj}
        <div class="obj-item {obj.status}">
          <span class="status-icon">{obj.status === 'succeed' || obj.status === 'completed' ? '✅' : obj.status === 'failed' ? '❌' : '🔹'}</span>
          <span class="obj-text">{@html obj.text}</span>
        </div>
      {/each}
    {/if}

    {#if objectives.filter(o => o.type === 'secondary').length > 0}
      <div class="obj-category mt">Secondary Goals</div>
      {#each objectives.filter(o => o.type === 'secondary') as obj}
        <div class="obj-item {obj.status}">
          <span class="status-icon">{obj.status === 'succeed' || obj.status === 'completed' ? '✅' : obj.status === 'failed' ? '❌' : '🔸'}</span>
          <span class="obj-text">{@html obj.text}</span>
        </div>
      {/each}
    {/if}
    
    {#if objectives.length === 0}
      <div class="obj-item" style="opacity: 0.5;">
        <span class="obj-text">No active objectives...</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .objectives-panel {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    width: 250px;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    backdrop-filter: blur(10px);
    color: var(--text-primary);
    pointer-events: auto;
  }

  .panel-header {
    font-weight: bold;
    font-size: 0.9rem;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px;
    color: var(--accent-color);
  }

  .obj-category {
    font-size: 0.75rem;
    font-weight: bold;
    color: var(--text-muted);
    margin-bottom: 6px;
    text-transform: uppercase;
  }

  .mt {
    margin-top: 12px;
  }

  .obj-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 0.8rem;
    margin-bottom: 6px;
    line-height: 1.3;
  }

  .obj-item.completed {
    opacity: 0.5;
    text-decoration: line-through;
  }

  .status-icon {
    font-size: 0.8rem;
  }

  /* Compact Mode Styles */
  .objectives-panel.compact {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    padding: 0;
  }

  .objectives-panel.compact .obj-category,
  .objectives-panel.compact .obj-text,
  .objectives-panel.compact .status-icon {
    text-shadow: 1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000, 0px 4px 6px rgba(0,0,0,0.8);
  }
</style>
