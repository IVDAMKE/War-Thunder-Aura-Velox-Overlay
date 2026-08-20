<script lang="ts">
  import type { InterfaceSettings } from '$lib/types/settings';
  import type { TelemetryPayload } from '$lib/types/telemetry';
  import { sendChatMessage, type ChatMessage } from '$lib/utils/aiService';
  import { onMount, onDestroy } from 'svelte';
  import { DEFAULT_SETTINGS } from '$lib/types/settings';

  let {
    settings = DEFAULT_SETTINGS,
    telemetry = null
  }: {
    settings?: InterfaceSettings;
    telemetry?: TelemetryPayload | null;
  } = $props();

  let inputQuery = $state('');
  let isLoading = $state(false);
  let errorMsg = $state('');
  
  let chatHistory = $state<ChatMessage[]>([]);
  
  let isListening = $state(false);
  let recognition: any = null;
  let chatLogEl: HTMLDivElement;

  let audioContext: AudioContext | null = null;
  let currentAudioSource: any = null;

  $effect(() => {
    if (chatHistory.length || isLoading) {
      setTimeout(() => {
        if (chatLogEl) chatLogEl.scrollTop = chatLogEl.scrollHeight;
      }, 50);
    }
  });

  onMount(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        isListening = true;
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        inputQuery = (inputQuery + ' ' + transcript).trim();
      };

      recognition.onerror = (event: any) => {
        console.error("Speech Recognition Error:", event.error);
        if (event.error === 'not-allowed') {
          errorMsg = "Microphone access denied.";
        }
        isListening = false;
      };

      recognition.onend = () => {
        isListening = false;
        if (settings.aiVoiceAutoSend && inputQuery.trim().length > 0) {
          handleSend();
        }
      };
    }
  });

  async function speakWithTowerVoice(text: string) {
    if (!settings.aiTtsEnabled) return;

    if (settings.aiTtsProvider === 'openai' && settings.aiApiKey) {
      try {
        const response = await fetch('https://api.openai.com/v1/audio/speech', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${settings.aiApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: 'tts-1',
            input: text,
            voice: settings.aiOpenAiVoice || 'onyx',
            response_format: 'mp3'
          })
        });

        if (!response.ok) throw new Error("OpenAI TTS failed");
        
        const arrayBuffer = await response.arrayBuffer();
        
        if (!audioContext) audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        if (currentAudioSource) {
          try { currentAudioSource.stop(); } catch(e){}
        }

        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        currentAudioSource = source;

        if (settings.aiVoiceDistortion) {
          const highpass = audioContext.createBiquadFilter();
          highpass.type = 'highpass';
          highpass.frequency.value = 800; 

          const lowpass = audioContext.createBiquadFilter();
          lowpass.type = 'lowpass';
          lowpass.frequency.value = 3500; 

          const distortion = audioContext.createWaveShaper();
          function makeDistortionCurve(amount: number) {
            let k = amount, n_samples = 44100, curve = new Float32Array(n_samples), deg = Math.PI / 180, i = 0, x;
            for ( ; i < n_samples; ++i ) {
              x = i * 2 / n_samples - 1;
              curve[i] = ( 3 + k ) * x * 20 * deg / ( Math.PI + k * Math.abs(x) );
            }
            return curve;
          }
          distortion.curve = makeDistortionCurve(5);
          
          source.connect(highpass);
          highpass.connect(lowpass);
          lowpass.connect(distortion);
          distortion.connect(audioContext.destination);
        } else {
          source.connect(audioContext.destination);
        }

        source.start();
      } catch (e) {
        console.error("Failed OpenAI TTS", e);
      }
    } else if (settings.aiTtsProvider === 'gemini' && settings.aiApiKey) {
      try {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.5-flash-preview-tts:generateContent?key=${settings.aiApiKey}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text }] }],
            generationConfig: {
              responseModalities: ["AUDIO"],
              response_modalities: ["AUDIO"],
              speechConfig: {
                voiceConfig: {
                  prebuiltVoiceConfig: {
                    voiceName: settings.aiGeminiVoice || 'Puck',
                    voice_name: settings.aiGeminiVoice || 'Puck'
                  }
                }
              },
              speech_config: {
                voice_config: {
                  prebuilt_voice_config: {
                    voiceName: settings.aiGeminiVoice || 'Puck',
                    voice_name: settings.aiGeminiVoice || 'Puck'
                  }
                }
              }
            }
          })
        });

        if (!response.ok) throw new Error("Gemini TTS failed: " + await response.text());
        const json = await response.json();
        
        const base64Audio = json.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
        if (!base64Audio) throw new Error("No audio data returned from Gemini");

        const binaryString = atob(base64Audio);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        if (!audioContext) audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        if (currentAudioSource) {
          if (typeof currentAudioSource.pause === 'function') currentAudioSource.pause();
          if (typeof currentAudioSource.stop === 'function') try { currentAudioSource.stop(); } catch(e){}
        }

        const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        currentAudioSource = source;

        if (settings.aiVoiceDistortion) {
          const highpass = audioContext.createBiquadFilter();
          highpass.type = 'highpass';
          highpass.frequency.value = 800; 

          const lowpass = audioContext.createBiquadFilter();
          lowpass.type = 'lowpass';
          lowpass.frequency.value = 3500; 

          const distortion = audioContext.createWaveShaper();
          function makeDistortionCurve(amount: number) {
            let k = amount, n_samples = 44100, curve = new Float32Array(n_samples), deg = Math.PI / 180, i = 0, x;
            for ( ; i < n_samples; ++i ) {
              x = i * 2 / n_samples - 1;
              curve[i] = ( 3 + k ) * x * 20 * deg / ( Math.PI + k * Math.abs(x) );
            }
            return curve;
          }
          distortion.curve = makeDistortionCurve(5);
          
          source.connect(highpass);
          highpass.connect(lowpass);
          lowpass.connect(distortion);
          distortion.connect(audioContext.destination);
        } else {
          source.connect(audioContext.destination);
        }

        source.start();
      } catch (e) {
        console.error("Gemini TTS Error", e);
      }
    } else if (settings.aiTtsProvider === 'google') {
      try {
        const textChunk = encodeURIComponent(text.substring(0, 200));
        const url = `https://translate.googleapis.com/translate_tts?client=gtx&ie=UTF-8&tl=en&q=${textChunk}`;
        const audio = new Audio(url);
        
        audio.onended = () => {
          if (currentAudioSource === audio) {
            currentAudioSource = null;
          }
        };

        if (currentAudioSource) {
          if (typeof currentAudioSource.pause === 'function') currentAudioSource.pause();
          if (typeof currentAudioSource.stop === 'function') try { currentAudioSource.stop(); } catch(e){}
        }

        currentAudioSource = audio;
        audio.play().catch(e => console.error("Google TTS failed to play", e));
      } catch (e) {
        console.error("Google TTS Error", e);
      }
    } else {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        
        if (settings.aiVoiceURI) {
          const voices = window.speechSynthesis.getVoices();
          const selectedVoice = voices.find(v => v.voiceURI === settings.aiVoiceURI);
          if (selectedVoice) {
            utterance.voice = selectedVoice;
          }
        }

        if (settings.aiVoiceDistortion) {
          utterance.pitch = 0.6;
          utterance.rate = 1.1;
        }
        
        window.speechSynthesis.speak(utterance);
      }
    }
  }

  onDestroy(() => {
    if (recognition) recognition.stop();
  });

  async function handleSend() {
    const q = inputQuery.trim();
    if (!q) return;

    if (!settings.aiApiKey && settings.aiApiProvider !== 'custom') {
      errorMsg = "API Key is missing! Set it in Settings.";
      return;
    }

    errorMsg = '';
    
    // Add user message to history
    chatHistory = [...chatHistory, { role: 'user', content: q }];
    inputQuery = '';
    isLoading = true;

    try {
      const responseText = await sendChatMessage(chatHistory, telemetry, settings);
      chatHistory = [...chatHistory, { role: 'assistant', content: responseText }];
      speakWithTowerVoice(responseText);
    } catch (err: any) {
      errorMsg = err.message || "Failed to contact AI Copilot";
      chatHistory = chatHistory.slice(0, -1); // Remove failed user message
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function stopTts() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (currentAudioSource) {
      if (typeof currentAudioSource.pause === 'function') currentAudioSource.pause();
      if (typeof currentAudioSource.stop === 'function') try { currentAudioSource.stop(); } catch(e){}
    }
  }

  function toggleListen() {
    if (!recognition) {
      errorMsg = "Microphone not supported in this environment.";
      return;
    }
    if (isListening) {
      recognition.stop();
    } else {
      errorMsg = '';
      try {
        recognition.start();
      } catch (e) {
        console.error(e);
      }
    }
  }
</script>

<div class="ai-copilot-container {settings?.compactMode ? 'compact' : ''}">
  <div class="chat-log" id="ai-chat-log" bind:this={chatLogEl}>
    {#if chatHistory.length === 0}
      {#if settings?.compactMode}
        <div class="message assistant">
          <span class="bubble">🤖 AI Co-pilot online.<br/>Ask me about your telemetry or current situation.</span>
        </div>
      {:else}
        <div class="welcome-message">
          <span class="icon">🤖</span>
          <p>AI Co-pilot online.<br/>Ask me about your telemetry or current situation.</p>
        </div>
      {/if}
    {/if}
    
    {#each chatHistory as msg}
      <div class="message {msg.role}">
        <span class="bubble">
          {msg.content}
        </span>
      </div>
    {/each}

    {#if isLoading}
      <div class="message assistant typing">
        <span class="bubble">Processing...</span>
      </div>
    {/if}
  </div>

  {#if errorMsg}
    <div class="error-banner">{errorMsg}</div>
  {/if}

  <div class="input-area" class:compact-input={settings?.compactMode}>
    {#if settings?.compactMode}
      <div class="message user" style="width: 100%; margin-bottom: 0;">
        <div class="bubble" style="display: flex; gap: 8px; width: 100%; max-width: 90%; padding: 8px 12px;">
          <textarea 
            bind:value={inputQuery} 
            on:keydown={handleKeydown}
            placeholder="Write here..." 
            rows="2"
            disabled={isLoading}
            class="compact-textarea"
          ></textarea>
          <div class="btn-group compact-btns">
            <button class="mic-btn" class:listening={isListening} on:click={toggleListen} title="Voice Input">
              <span class="material-symbols-outlined">{isListening ? 'graphic_eq' : 'mic'}</span>
            </button>
            <button class="send-btn" on:click={handleSend} disabled={isLoading || !inputQuery.trim()} title="Send Message">
              <span class="material-symbols-outlined">send</span>
            </button>
          </div>
        </div>
      </div>
    {:else}
      <textarea 
        bind:value={inputQuery} 
        on:keydown={handleKeydown}
        placeholder="Ask Co-pilot... (Enter to send)" 
        rows="2"
        disabled={isLoading}
      ></textarea>
      <div class="btn-group">
        <button class="mic-btn" class:listening={isListening} on:click={toggleListen} title="Voice Input">
          <span class="material-symbols-outlined">{isListening ? 'graphic_eq' : 'mic'}</span>
        </button>
        <button class="send-btn" on:click={handleSend} disabled={isLoading || !inputQuery.trim()} title="Send Message">
          <span class="material-symbols-outlined">send</span>
        </button>
        {#if settings.aiTtsEnabled}
          <button class="stop-btn" on:click={stopTts} title="Stop Voice">
            <span class="material-symbols-outlined">volume_off</span>
          </button>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .ai-copilot-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 6px;
    overflow: hidden;
  }

  .chat-log {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  /* Custom scrollbar for chat log */
  .chat-log::-webkit-scrollbar {
    width: 6px;
  }
  .chat-log::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
  }
  .chat-log::-webkit-scrollbar-thumb {
    background: rgba(245, 158, 11, 0.3);
    border-radius: 3px;
  }

  .welcome-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--text-muted);
    height: 100%;
    opacity: 0.7;
  }

  .welcome-message .icon {
    font-size: 2rem;
    margin-bottom: 8px;
  }

  .welcome-message p {
    font-size: 0.8rem;
    line-height: 1.4;
    margin: 0;
  }

  .message {
    display: flex;
    width: 100%;
  }

  .message.user {
    justify-content: flex-end;
  }

  .message.assistant {
    justify-content: flex-start;
  }

  .bubble {
    max-width: 85%;
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 0.8rem;
    line-height: 1.35;
    word-break: break-word;
    white-space: pre-wrap;
  }

  .message.user .bubble {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: #93c5fd;
    border-bottom-right-radius: 4px;
  }

  .message.assistant .bubble {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: var(--text-primary);
    border-bottom-left-radius: 4px;
  }

  .message.typing .bubble {
    font-style: italic;
    opacity: 0.7;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0% { opacity: 0.4; }
    50% { opacity: 0.8; }
    100% { opacity: 0.4; }
  }

  .error-banner {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    font-size: 0.7rem;
    padding: 6px 10px;
    border-top: 1px solid rgba(239, 68, 68, 0.3);
    text-align: center;
  }

  .input-area {
    display: flex;
    padding: 8px;
    background: rgba(15, 23, 42, 0.6);
    border-top: 1px solid var(--border-color);
    gap: 8px;
  }

  textarea {
    flex: 1;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    padding: 6px 10px;
    font-family: inherit;
    font-size: 0.8rem;
    resize: none;
    outline: none;
  }

  textarea:focus {
    border-color: rgba(245, 158, 11, 0.5);
    box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2);
  }

  .btn-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  button {
    flex: 1;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: var(--accent-color);
    border-radius: 6px;
    padding: 0 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  button:hover:not(:disabled) {
    background: rgba(245, 158, 11, 0.25);
    box-shadow: var(--accent-glow);
  }

  button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  button.mic-btn {
    flex: 0 0 auto;
    font-size: 1.1rem;
    padding: 6px;
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.4);
  }

  button.mic-btn:hover {
    background: rgba(59, 130, 246, 0.3);
    box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
  }

  button.mic-btn.listening {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.5);
    animation: pulse 1.5s infinite;
  }

  button.send-btn {
    flex: 1;
  }

  button.stop-btn {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.4);
    padding: 4px;
    font-size: 1rem;
    flex: 0 0 auto;
  }
  
  button.stop-btn:hover {
    background: rgba(239, 68, 68, 0.3);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  }

  /* Compact Mode Styles */
  .ai-copilot-container.compact {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
  }

  .ai-copilot-container.compact .chat-log,
  .ai-copilot-container.compact .input-area {
    background: transparent;
    border: none;
  }

  .compact-input {
    background: transparent !important;
    border: none !important;
    padding: 4px 10px 10px 10px !important;
  }

  .compact-textarea {
    flex: 1;
    background: transparent !important;
    border: none !important;
    color: #93c5fd !important;
    font-size: 0.8rem;
    outline: none;
    resize: none;
    padding: 0;
  }

  .compact-textarea::placeholder {
    color: rgba(147, 197, 253, 0.5);
  }

  .compact-btns {
    flex-direction: row !important;
    align-items: center;
  }

  .compact-btns button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 2px 4px;
    font-size: 1.2rem;
    color: #93c5fd;
  }

  .compact-btns button:hover:not(:disabled) {
    color: #fff;
    transform: scale(1.1);
  }
</style>
