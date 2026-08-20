import type { InterfaceSettings } from '../types/settings';
import type { TelemetryPayload } from '../types/telemetry';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

function buildSystemPrompt(telemetry: TelemetryPayload | null): string {
  let prompt = `You are an expert AI Co-pilot for a player in the game War Thunder.
You act as a RIO (Radar Intercept Officer), co-driver, or commander.
Keep your answers concise, direct, and highly relevant to the situation. No fluff.

`;

  if (telemetry) {
    const { state, indicators } = telemetry;
    prompt += `CURRENT TELEMETRY DATA:
Speed (TAS): ${Math.round(state['TAS, km/h'] || 0)} km/h (Mach ${state['M'] || 0})
Speed (IAS): ${Math.round(state['IAS, km/h'] || 0)} km/h
Altitude: ${Math.round(state['H, m'] || 0)} m
Climb Rate: ${state['Vy, m/s'] ? state['Vy, m/s'].toFixed(1) : 0} m/s
Heading: ${indicators?.compass || 0}°
Pitch: ${indicators?.aviahorizon_pitch || 0}°
Roll: ${indicators?.aviahorizon_roll || 0}°
Engine RPM: ${Math.round(state['RPM 1'] || 0)}
Throttle: ${state['throttle 1, %'] || 0}%
Oil Temp: ${state['oil temp 1, C'] || 0}°C
Water Temp: ${(state as any)['water temp 1, C'] || 0}°C
Gear: ${(state as any)['gear, %'] === 100 ? 'DOWN' : 'UP'}
`;
  } else {
    prompt += `Currently waiting for live game telemetry...`;
  }

  return prompt;
}

export async function sendChatMessage(
  messages: ChatMessage[],
  telemetry: TelemetryPayload | null,
  settings: InterfaceSettings
): Promise<string> {
  const { aiApiProvider, aiApiKey, aiModel, aiCustomEndpoint } = settings;

  const systemContent = buildSystemPrompt(telemetry);
  const cleanModel = aiModel.trim();
  const cleanKey = aiApiKey.trim();

  let endpoint = '';
  let headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  let body: any;

  if (aiApiProvider === 'openai' || aiApiProvider === 'custom') {
    const fullMessages = [
      { role: 'system', content: systemContent },
      ...messages
    ];
    endpoint = aiApiProvider === 'openai' 
      ? 'https://api.openai.com/v1/chat/completions' 
      : aiCustomEndpoint.trim();
    
    if (cleanKey) {
      headers['Authorization'] = `Bearer ${cleanKey}`;
    }

    body = {
      model: cleanModel,
      messages: fullMessages,
      temperature: 0.7,
      max_tokens: 300,
    };
  } else if (aiApiProvider === 'google') {
    // Google Gemini via REST API
    endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${cleanModel}:generateContent?key=${cleanKey}`;
    body = {
      systemInstruction: {
        parts: [{ text: systemContent }]
      },
      contents: messages.map(msg => ({
        role: msg.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: msg.content }]
      })),
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 300,
      }
    };
  }

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errText}`);
    }

    const data = await response.json();

    if (aiApiProvider === 'google') {
      return data.candidates[0].content.parts[0].text;
    } else {
      return data.choices[0].message.content;
    }
  } catch (error) {
    console.error("AI Service Error:", error);
    throw error;
  }
}
