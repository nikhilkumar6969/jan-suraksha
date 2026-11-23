// PCM AudioWorklet Processor for Real-Time Offline Speech Streaming
// Captures raw microphone audio, handles variable hardware sample rates (16k/44.1k/48k),
// converts to 16kHz 16-bit mono PCM, and transfers Int16 buffers with zero memory leak.

class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.sourceSampleRate = sampleRate; // built-in global in AudioWorkletGlobalScope
    this.resampleRatio = this.sourceSampleRate / this.targetSampleRate;
    
    // Output 2048 samples = exactly 128ms of audio at 16kHz
    this.outputBufferSize = 2048;
    this.outputBuffer = new Int16Array(this.outputBufferSize);
    this.outputIndex = 0;
    
    // Resampling accumulator
    this.resamplePos = 0.0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0] || input[0].length === 0) {
      return true;
    }

    const channelData = input[0];
    const inLength = channelData.length;

    if (this.resampleRatio === 1.0) {
      // Hardware is already 16kHz
      for (let i = 0; i < inLength; i++) {
        let s = Math.max(-1, Math.min(1, channelData[i]));
        this.outputBuffer[this.outputIndex++] = s < 0 ? s * 0x8000 : s * 0x7FFF;

        if (this.outputIndex >= this.outputBufferSize) {
          this.flush();
        }
      }
    } else {
      // Linear interpolation downsampling to 16kHz
      while (this.resamplePos < inLength) {
        const index0 = Math.floor(this.resamplePos);
        const index1 = Math.min(index0 + 1, inLength - 1);
        const frac = this.resamplePos - index0;
        
        const sample0 = channelData[index0];
        const sample1 = channelData[index1];
        const interpolated = sample0 + frac * (sample1 - sample0);
        
        let s = Math.max(-1, Math.min(1, interpolated));
        this.outputBuffer[this.outputIndex++] = s < 0 ? s * 0x8000 : s * 0x7FFF;

        if (this.outputIndex >= this.outputBufferSize) {
          this.flush();
        }

        this.resamplePos += this.resampleRatio;
      }
      this.resamplePos -= inLength;
    }

    return true;
  }

  flush() {
    // Post transferable ArrayBuffer to main thread
    const transferCopy = this.outputBuffer.slice(0, this.outputIndex);
    this.port.postMessage(transferCopy.buffer, [transferCopy.buffer]);
    this.outputIndex = 0;
  }
}

registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
