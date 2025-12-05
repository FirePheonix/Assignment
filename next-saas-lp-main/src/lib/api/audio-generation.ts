/**
 * Audio Generation API Service
 * Connects to Django backend for AI audio generation using AI/ML API with ElevenLabs eleven_turbo_v2_5 model
 */

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

// Helper function to get CSRF token from cookies
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  const csrfCookie = cookies.find(c => c.trim().startsWith('csrftoken='));
  
  if (csrfCookie) {
    return csrfCookie.split('=')[1];
  }
  
  return null;
}

// Ensure CSRF token is available
async function ensureCSRFToken(): Promise<void> {
  if (getCsrfToken()) return; // Already have token
  
  try {
    // Make a GET request to get CSRF cookie
    await fetch(`${DJANGO_BACKEND}/api/auth/csrf/`, {
      method: 'GET',
      credentials: 'include',
    });
  } catch {
    // Ignore errors, just trying to get CSRF token
  }
}

export type OutputFormat = 
  | 'mp3_22050_32' | 'mp3_44100_32' | 'mp3_44100_64' | 'mp3_44100_96' 
  | 'mp3_44100_128' | 'mp3_44100_192' | 'pcm_8000' | 'pcm_16000' 
  | 'pcm_22050' | 'pcm_24000' | 'pcm_44100' | 'pcm_48000' 
  | 'ulaw_8000' | 'alaw_8000' | 'opus_48000_32' | 'opus_48000_64' 
  | 'opus_48000_96' | 'opus_48000_128' | 'opus_48000_192';

export interface GenerateAudioFromTextParams {
  text: string;
  voice?: string;  // Voice name instead of ID
  output_format?: OutputFormat;
  stability?: number;
  similarity_boost?: number;
  use_speaker_boost?: boolean;
  style?: number;
  speed?: number;
}

export interface UploadAudioFileParams {
  audio_file: File;
}

export interface AudioGenerationResponse {
  success: boolean;
  audio_url?: string;
  type?: 'generated' | 'uploaded';
  file_path?: string;
  text?: string;
  voice?: string;
  model?: string;
  output_format?: string;
  error?: string;
}

/**
 * Available voices for AI/ML API ElevenLabs eleven_turbo_v2_5 model
 */
export const AIML_VOICES = {
  // Female voices
  rachel: { name: 'Rachel', gender: 'female', description: 'Calm, professional female voice' },
  drew: { name: 'Drew', gender: 'female', description: 'Female voice' },
  aria: { name: 'Aria', gender: 'female', description: 'Female voice' },
  domi: { name: 'Domi', gender: 'female', description: 'Female voice' },
  sarah: { name: 'Sarah', gender: 'female', description: 'Female voice' },
  laura: { name: 'Laura', gender: 'female', description: 'Female voice' },
  emily: { name: 'Emily', gender: 'female', description: 'Female voice' },
  elli: { name: 'Elli', gender: 'female', description: 'Youthful female voice' },
  charlotte: { name: 'Charlotte', gender: 'female', description: 'Female voice' },
  alice: { name: 'Alice', gender: 'female', description: 'Female voice' },
  matilda: { name: 'Matilda', gender: 'female', description: 'Female voice' },
  jessica: { name: 'Jessica', gender: 'female', description: 'Female voice' },
  grace: { name: 'Grace', gender: 'female', description: 'Female voice' },
  lily: { name: 'Lily', gender: 'female', description: 'Female voice' },
  serena: { name: 'Serena', gender: 'female', description: 'Female voice' },
  nicole: { name: 'Nicole', gender: 'female', description: 'Female voice' },
  jessie: { name: 'Jessie', gender: 'female', description: 'Female voice' },
  glinda: { name: 'Glinda', gender: 'female', description: 'Female voice' },
  mimi: { name: 'Mimi', gender: 'female', description: 'Female voice' },
  
  // Male voices
  antoni: { name: 'Antoni', gender: 'male', description: 'Well-rounded male voice' },
  clyde: { name: 'Clyde', gender: 'male', description: 'Male voice' },
  paul: { name: 'Paul', gender: 'male', description: 'Male voice' },
  dave: { name: 'Dave', gender: 'male', description: 'Male voice' },
  roger: { name: 'Roger', gender: 'male', description: 'Male voice' },
  fin: { name: 'Fin', gender: 'male', description: 'Male voice' },
  thomas: { name: 'Thomas', gender: 'male', description: 'Male voice' },
  charlie: { name: 'Charlie', gender: 'male', description: 'Male voice' },
  george: { name: 'George', gender: 'male', description: 'Male voice' },
  callum: { name: 'Callum', gender: 'male', description: 'Male voice' },
  patrick: { name: 'Patrick', gender: 'male', description: 'Male voice' },
  river: { name: 'River', gender: 'male', description: 'Male voice' },
  harry: { name: 'Harry', gender: 'male', description: 'Male voice' },
  liam: { name: 'Liam', gender: 'male', description: 'Male voice' },
  dorothy: { name: 'Dorothy', gender: 'male', description: 'Male voice' },
  josh: { name: 'Josh', gender: 'male', description: 'Deep, resonant male voice' },
  arnold: { name: 'Arnold', gender: 'male', description: 'Crisp, authoritative male voice' },
  joseph: { name: 'Joseph', gender: 'male', description: 'Male voice' },
  will: { name: 'Will', gender: 'male', description: 'Male voice' },
  jeremy: { name: 'Jeremy', gender: 'male', description: 'Male voice' },
  eric: { name: 'Eric', gender: 'male', description: 'Male voice' },
  michael: { name: 'Michael', gender: 'male', description: 'Male voice' },
  ethan: { name: 'Ethan', gender: 'male', description: 'Male voice' },
  chris: { name: 'Chris', gender: 'male', description: 'Male voice' },
  gigi: { name: 'Gigi', gender: 'male', description: 'Male voice' },
  freya: { name: 'Freya', gender: 'male', description: 'Male voice' },
  brian: { name: 'Brian', gender: 'male', description: 'Male voice' },
  daniel: { name: 'Daniel', gender: 'male', description: 'Male voice' },
  adam: { name: 'Adam', gender: 'male', description: 'Male voice' },
  bill: { name: 'Bill', gender: 'male', description: 'Male voice' },
  sam: { name: 'Sam', gender: 'male', description: 'Dynamic, raspy male voice' },
  giovanni: { name: 'Giovanni', gender: 'male', description: 'Male voice' },
  
  // Special
  santa: { name: 'Santa Claus', gender: 'male', description: 'Santa Claus voice' },
};

/**
 * Available output formats for audio generation
 */
export const OUTPUT_FORMATS = {
  mp3_standard: { format: 'mp3_44100_128' as OutputFormat, description: 'MP3 44.1kHz 128kbps (default)' },
  mp3_high: { format: 'mp3_44100_192' as OutputFormat, description: 'MP3 44.1kHz 192kbps (high quality)' },
  mp3_good: { format: 'mp3_44100_96' as OutputFormat, description: 'MP3 44.1kHz 96kbps (good quality)' },
  mp3_medium: { format: 'mp3_44100_64' as OutputFormat, description: 'MP3 44.1kHz 64kbps (medium)' },
  mp3_low: { format: 'mp3_44100_32' as OutputFormat, description: 'MP3 44.1kHz 32kbps (low)' },
  pcm_cd: { format: 'pcm_44100' as OutputFormat, description: 'PCM/WAV 44.1kHz (CD quality)' },
  pcm_high: { format: 'pcm_24000' as OutputFormat, description: 'PCM/WAV 24kHz (high quality)' },
  opus_high: { format: 'opus_48000_128' as OutputFormat, description: 'Opus 48kHz 128kbps (high quality)' },
  opus_good: { format: 'opus_48000_96' as OutputFormat, description: 'Opus 48kHz 96kbps (good quality)' },
};

/**
 * Generate audio from text using AI/ML API with ElevenLabs eleven_turbo_v2_5 model
 */
export async function generateAudioFromText(
  params: GenerateAudioFromTextParams
): Promise<AudioGenerationResponse> {
  try {
    // Get auth token from localStorage (stored by login function)
    const token = localStorage.getItem('auth_token');
    
    console.log('Audio generation - Token available:', !!token);
    
    // Ensure CSRF token is available
    await ensureCSRFToken();
    const csrfToken = getCsrfToken();
    
    console.log('Audio generation - CSRF token available:', !!csrfToken);
    
    const formData = new FormData();
    formData.append('text', params.text);
    
    if (params.voice) {
      formData.append('voice', params.voice);
    }
    
    if (params.output_format) {
      formData.append('output_format', params.output_format);
    }
    
    if (params.stability !== undefined) {
      formData.append('stability', params.stability.toString());
    }
    
    if (params.similarity_boost !== undefined) {
      formData.append('similarity_boost', params.similarity_boost.toString());
    }
    
    if (params.use_speaker_boost !== undefined) {
      formData.append('use_speaker_boost', params.use_speaker_boost.toString());
    }
    
    if (params.style !== undefined) {
      formData.append('style', params.style.toString());
    }
    
    if (params.speed !== undefined) {
      formData.append('speed', params.speed.toString());
    }

    const response = await fetch(`${DJANGO_BACKEND}/api/ai/generate-audio/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        ...(csrfToken && { 'X-CSRFToken': csrfToken }),
        ...(token && { 'Authorization': `Token ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = 'Failed to generate audio';
      try {
        const error = await response.json();
        errorMsg = error.error || error.detail || JSON.stringify(error);
      } catch (e) {
        errorMsg = `HTTP ${response.status}: ${response.statusText}`;
      }
      console.error('Audio generation error:', errorMsg);
      return {
        success: false,
        error: errorMsg,
      };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error generating audio from text:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Upload an audio file
 */
export async function uploadAudioFile(
  params: UploadAudioFileParams
): Promise<AudioGenerationResponse> {
  try {
    // Ensure CSRF token is available
    await ensureCSRFToken();
    const csrfToken = getCsrfToken();
    
    const formData = new FormData();
    formData.append('audio_file', params.audio_file);

    const response = await fetch(`${DJANGO_BACKEND}/api/ai/generate-audio/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        ...(csrfToken && { 'X-CSRFToken': csrfToken }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        success: false,
        error: error.error || 'Failed to upload audio file',
      };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error uploading audio file:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Helper function to create an audio element from URL
 */
export function createAudioPlayer(audioUrl: string): HTMLAudioElement {
  const audio = new Audio(audioUrl);
  audio.controls = true;
  return audio;
}

/**
 * Helper function to download audio file
 */
export async function downloadAudio(audioUrl: string, filename: string = 'audio.mp3'): Promise<void> {
  try {
    const response = await fetch(audioUrl);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading audio:', error);
    throw error;
  }
}
