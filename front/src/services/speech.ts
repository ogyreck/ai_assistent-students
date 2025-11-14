/**
 * Speech Recognition Service
 * Records audio and sends to backend for transcription
 */

export interface SpeechRecognitionConfig {
  onStart?: () => void
  onStop?: () => void
  onError?: (error: string) => void
  onRecordingStateChange?: (isRecording: boolean) => void
}

export class SpeechRecorder {
  private mediaRecorder: MediaRecorder | null = null
  private audioChunks: Blob[] = []
  private stream: MediaStream | null = null
  private isRecording = false
  private config: SpeechRecognitionConfig

  constructor(config: SpeechRecognitionConfig = {}) {
    this.config = config
  }

  async startRecording(): Promise<void> {
    try {
      // Check browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser does not support audio recording')
      }

      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      // Create MediaRecorder
      const mimeType = this.getSupportedMimeType()
      this.mediaRecorder = new MediaRecorder(this.stream, { mimeType })

      this.audioChunks = []

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }

      this.mediaRecorder.start()
      this.isRecording = true
      this.config.onStart?.()
      this.config.onRecordingStateChange?.(true)

      console.log('Recording started...')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start recording'
      this.config.onError?.(message)
      console.error('Recording error:', error)
    }
  }

  async stopRecording(): Promise<Blob | null> {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || !this.isRecording) {
        resolve(null)
        return
      }

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder!.mimeType })

        // Stop all tracks
        if (this.stream) {
          this.stream.getTracks().forEach((track) => track.stop())
        }

        this.isRecording = false
        this.config.onStop?.()
        this.config.onRecordingStateChange?.(false)

        console.log('Recording stopped. Audio blob size:', audioBlob.size)
        resolve(audioBlob)
      }

      this.mediaRecorder.stop()
    })
  }

  cancelRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop()
      this.isRecording = false

      if (this.stream) {
        this.stream.getTracks().forEach((track) => track.stop())
      }

      this.audioChunks = []
      this.config.onRecordingStateChange?.(false)
      console.log('Recording cancelled')
    }
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording
  }

  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav',
    ]

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type
      }
    }

    // Fallback to default
    return 'audio/webm'
  }
}

/**
 * Send audio blob to backend for transcription
 */
export async function transcribeAudio(audioBlob: Blob, apiUrl: string = 'http://localhost:8000'): Promise<string> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'audio.wav')

  try {
    const response = await fetch(`${apiUrl}/api/transcribe`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`)
    }

    const data = await response.json()
    return data.text || ''
  } catch (error) {
    console.error('Transcription error:', error)
    throw error
  }
}

export default SpeechRecorder
