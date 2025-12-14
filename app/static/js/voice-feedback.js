/**
 * Voice Command Visual Feedback System
 * Provides real-time visual feedback for hands-free operation
 *
 * Features:
 * - Waveform visualization during speech
 * - Listening state indicators
 * - Confidence scoring display
 * - Command confirmation dialogs
 * - Server-side transcription integration
 */

class VoiceFeedbackSystem {
    constructor(options = {}) {
        this.options = {
            containerId: options.containerId || 'voice-feedback-container',
            useServerTranscription: options.useServerTranscription ?? true,
            serverEndpoint: options.serverEndpoint || '/ai/speech/transcribe-and-execute',
            wakeWordEndpoint: options.wakeWordEndpoint || '/ai/speech/detect-wake-word',
            autoStart: options.autoStart ?? false,
            continuousListening: options.continuousListening ?? true,
            wakeWordRequired: options.wakeWordRequired ?? false,
            language: options.language || 'en-US',
            onCommand: options.onCommand || null,
            onTranscript: options.onTranscript || null,
            onStateChange: options.onStateChange || null,
        };

        this.state = {
            isListening: false,
            isProcessing: false,
            wakeWordDetected: false,
            lastTranscript: '',
            lastConfidence: 0,
            lastCommandType: '',
            noiseLevel: 'unknown',
            errorCount: 0,
        };

        this.audioContext = null;
        this.analyser = null;
        this.mediaStream = null;
        this.animationFrame = null;

        // Browser Speech Recognition (fallback)
        this.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = null;

        // Speech synthesis for voice feedback
        this.synth = window.speechSynthesis;

        this.init();
    }

    init() {
        this.createUI();
        this.bindEvents();

        if (this.options.autoStart) {
            this.start();
        }
    }

    createUI() {
        // Check if AI widget exists - if so, don't create voice feedback UI to avoid conflicts
        if (document.querySelector('.ai-assistant-widget')) {
            console.log('🤖 AI widget detected, disabling voice feedback system to avoid conflicts');
            return;
        }

        // Check if container exists, create if not
        let container = document.getElementById(this.options.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.containerId;
            document.body.appendChild(container);
        }

        container.innerHTML = `
            <div class="voice-feedback-widget" id="voice-widget">
                <!-- Main microphone button -->
                <button class="voice-mic-button" id="voice-mic-btn" title="Click to start voice commands">
                    <svg class="mic-icon" viewBox="0 0 24 24" width="32" height="32">
                        <path fill="currentColor" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/>
                        <path fill="currentColor" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                    <div class="mic-pulse" id="mic-pulse"></div>
                </button>

                <!-- Status indicator -->
                <div class="voice-status-indicator" id="voice-status-indicator">
                    <span class="status-dot" id="status-dot"></span>
                    <span class="status-text" id="status-text">Ready</span>
                </div>

                <!-- Waveform visualization -->
                <div class="voice-waveform-container" id="waveform-container">
                    <canvas id="voice-waveform" width="200" height="40"></canvas>
                </div>

                <!-- Transcript display -->
                <div class="voice-transcript-panel" id="transcript-panel">
                    <div class="transcript-header">
                        <span class="transcript-label">Heard:</span>
                        <span class="confidence-badge" id="confidence-badge">--</span>
                    </div>
                    <div class="transcript-text" id="transcript-text">
                        Say "Hey ChatterFix" to start...
                    </div>
                    <div class="command-type" id="command-type"></div>
                </div>

                <!-- Noise level indicator -->
                <div class="noise-indicator" id="noise-indicator">
                    <span class="noise-icon">🔊</span>
                    <span class="noise-level" id="noise-level">--</span>
                </div>

                <!-- Action buttons -->
                <div class="voice-actions" id="voice-actions">
                    <button class="voice-action-btn confirm-btn" id="confirm-btn" style="display:none;">
                        ✓ Confirm
                    </button>
                    <button class="voice-action-btn cancel-btn" id="cancel-btn" style="display:none;">
                        ✗ Cancel
                    </button>
                    <button class="voice-action-btn retry-btn" id="retry-btn" style="display:none;">
                        ↺ Retry
                    </button>
                </div>

                <!-- Error display -->
                <div class="voice-error" id="voice-error" style="display:none;">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text" id="error-text"></span>
                </div>
            </div>
        `;

        this.injectStyles();
        this.cacheElements();
    }

    injectStyles() {
        if (document.getElementById('voice-feedback-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'voice-feedback-styles';
        styles.textContent = `
            .voice-feedback-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 10px;
            }

            /* Microphone Button */
            .voice-mic-button {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                border: none;
                background: linear-gradient(145deg, #3b82f6, #1d4ed8);
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
                transition: all 0.3s ease;
            }

            .voice-mic-button:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
            }

            .voice-mic-button.listening {
                background: linear-gradient(145deg, #10b981, #059669);
                animation: pulse-glow 1.5s infinite;
            }

            .voice-mic-button.processing {
                background: linear-gradient(145deg, #f59e0b, #d97706);
            }

            .voice-mic-button.error {
                background: linear-gradient(145deg, #ef4444, #dc2626);
            }

            .mic-pulse {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(16, 185, 129, 0.3);
                opacity: 0;
                pointer-events: none;
            }

            .voice-mic-button.listening .mic-pulse {
                animation: pulse-ring 1.5s infinite;
            }

            @keyframes pulse-glow {
                0%, 100% { box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); }
                50% { box-shadow: 0 4px 25px rgba(16, 185, 129, 0.7); }
            }

            @keyframes pulse-ring {
                0% { transform: scale(1); opacity: 0.5; }
                100% { transform: scale(1.5); opacity: 0; }
            }

            /* Status Indicator */
            .voice-status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                background: rgba(0, 0, 0, 0.8);
                border-radius: 20px;
                color: white;
                font-size: 14px;
            }

            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #6b7280;
                transition: background 0.3s ease;
            }

            .status-dot.ready { background: #3b82f6; }
            .status-dot.listening { background: #10b981; animation: blink 1s infinite; }
            .status-dot.processing { background: #f59e0b; animation: blink 0.5s infinite; }
            .status-dot.error { background: #ef4444; }

            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            /* Waveform */
            .voice-waveform-container {
                background: rgba(0, 0, 0, 0.8);
                border-radius: 10px;
                padding: 10px;
                display: none;
            }

            .voice-waveform-container.active {
                display: block;
            }

            #voice-waveform {
                display: block;
            }

            /* Transcript Panel */
            .voice-transcript-panel {
                background: rgba(0, 0, 0, 0.9);
                border-radius: 12px;
                padding: 12px 16px;
                max-width: 300px;
                color: white;
                display: none;
            }

            .voice-transcript-panel.active {
                display: block;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .transcript-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }

            .transcript-label {
                font-size: 12px;
                color: #9ca3af;
                text-transform: uppercase;
            }

            .confidence-badge {
                font-size: 11px;
                padding: 2px 8px;
                border-radius: 10px;
                background: #374151;
            }

            .confidence-badge.high { background: #059669; }
            .confidence-badge.medium { background: #d97706; }
            .confidence-badge.low { background: #dc2626; }

            .transcript-text {
                font-size: 16px;
                line-height: 1.4;
                margin-bottom: 8px;
            }

            .command-type {
                font-size: 12px;
                color: #60a5fa;
                text-transform: uppercase;
            }

            /* Noise Indicator */
            .noise-indicator {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #9ca3af;
                padding: 4px 10px;
                background: rgba(0, 0, 0, 0.6);
                border-radius: 10px;
            }

            .noise-indicator.high .noise-level { color: #ef4444; }
            .noise-indicator.medium .noise-level { color: #f59e0b; }
            .noise-indicator.low .noise-level { color: #10b981; }

            /* Action Buttons */
            .voice-actions {
                display: flex;
                gap: 8px;
            }

            .voice-action-btn {
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .confirm-btn {
                background: #10b981;
                color: white;
            }

            .cancel-btn {
                background: #6b7280;
                color: white;
            }

            .retry-btn {
                background: #3b82f6;
                color: white;
            }

            .voice-action-btn:hover {
                transform: scale(1.05);
            }

            /* Error Display */
            .voice-error {
                background: rgba(239, 68, 68, 0.9);
                color: white;
                padding: 10px 16px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }

            /* Mobile responsive */
            @media (max-width: 640px) {
                .voice-feedback-widget {
                    bottom: 10px;
                    right: 10px;
                    left: 10px;
                    align-items: center;
                }

                .voice-transcript-panel {
                    max-width: 100%;
                    width: 100%;
                }
            }

            /* Dark mode support */
            @media (prefers-color-scheme: light) {
                .voice-status-indicator,
                .voice-waveform-container,
                .voice-transcript-panel {
                    background: rgba(255, 255, 255, 0.95);
                    color: #1f2937;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                }

                .transcript-label,
                .noise-indicator {
                    color: #6b7280;
                }

                .confidence-badge {
                    background: #e5e7eb;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    cacheElements() {
        this.elements = {
            widget: document.getElementById('voice-widget'),
            micBtn: document.getElementById('voice-mic-btn'),
            micPulse: document.getElementById('mic-pulse'),
            statusDot: document.getElementById('status-dot'),
            statusText: document.getElementById('status-text'),
            waveformContainer: document.getElementById('waveform-container'),
            waveformCanvas: document.getElementById('voice-waveform'),
            transcriptPanel: document.getElementById('transcript-panel'),
            transcriptText: document.getElementById('transcript-text'),
            confidenceBadge: document.getElementById('confidence-badge'),
            commandType: document.getElementById('command-type'),
            noiseIndicator: document.getElementById('noise-indicator'),
            noiseLevel: document.getElementById('noise-level'),
            confirmBtn: document.getElementById('confirm-btn'),
            cancelBtn: document.getElementById('cancel-btn'),
            retryBtn: document.getElementById('retry-btn'),
            errorDisplay: document.getElementById('voice-error'),
            errorText: document.getElementById('error-text'),
        };
    }

    bindEvents() {
        // Microphone button click
        this.elements.micBtn.addEventListener('click', () => {
            if (this.state.isListening) {
                this.stop();
            } else {
                this.start();
            }
        });

        // Action buttons
        this.elements.confirmBtn.addEventListener('click', () => this.confirmCommand());
        this.elements.cancelBtn.addEventListener('click', () => this.cancelCommand());
        this.elements.retryBtn.addEventListener('click', () => this.retry());
    }

    async start() {
        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Set up audio analysis for waveform
            this.setupAudioAnalysis();

            // Start recognition
            if (this.options.useServerTranscription) {
                this.startServerRecording();
            } else {
                this.startBrowserRecognition();
            }

            this.updateState({ isListening: true });
            this.speak('Listening');

        } catch (error) {
            console.error('Failed to start voice recognition:', error);
            this.showError('Microphone access denied. Please allow microphone access.');
        }
    }

    stop() {
        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Stop audio analysis
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        // Stop recognition
        if (this.recognition) {
            this.recognition.stop();
        }

        // Stop recording
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        this.updateState({ isListening: false });
    }

    setupAudioAnalysis() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        source.connect(this.analyser);

        this.drawWaveform();
    }

    drawWaveform() {
        const canvas = this.elements.waveformCanvas;
        const ctx = canvas.getContext('2d');
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            this.animationFrame = requestAnimationFrame(draw);
            this.analyser.getByteFrequencyData(dataArray);

            ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;

                // Gradient color based on height
                const hue = (dataArray[i] / 255) * 120; // Green to red
                ctx.fillStyle = `hsl(${120 - hue}, 70%, 50%)`;

                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        };

        draw();
    }

    startServerRecording() {
        const chunks = [];
        this.mediaRecorder = new MediaRecorder(this.mediaStream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        this.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunks.push(e.data);
            }
        };

        this.mediaRecorder.onstop = async () => {
            if (chunks.length > 0) {
                const audioBlob = new Blob(chunks, { type: 'audio/webm' });
                await this.sendToServer(audioBlob);
            }
        };

        // Record in 3-second chunks for continuous listening
        this.mediaRecorder.start();

        // Stop after 5 seconds for processing
        setTimeout(() => {
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();

                // Restart if continuous listening
                if (this.options.continuousListening && this.state.isListening) {
                    setTimeout(() => this.startServerRecording(), 500);
                }
            }
        }, 5000);
    }

    async sendToServer(audioBlob) {
        this.updateState({ isProcessing: true });

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('language_code', this.options.language);
            formData.append('sample_rate', '48000');

            const response = await fetch(this.options.serverEndpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.handleTranscriptionResult(result);
            } else {
                throw new Error(result.error || 'Transcription failed');
            }

        } catch (error) {
            console.error('Server transcription error:', error);
            this.showError('Could not process audio. Check your connection.');
            this.state.errorCount++;
        } finally {
            this.updateState({ isProcessing: false });
        }
    }

    handleTranscriptionResult(result) {
        const transcription = result.transcription;

        this.state.lastTranscript = transcription.transcript;
        this.state.lastConfidence = transcription.confidence;
        this.state.lastCommandType = result.command_type;
        this.state.noiseLevel = transcription.noise_level;
        this.state.wakeWordDetected = result.has_wake_word;

        // Update UI
        this.updateTranscriptDisplay(transcription.transcript, transcription.confidence);
        this.updateNoiseLevel(transcription.noise_level);

        if (result.command_type) {
            this.elements.commandType.textContent = result.command_type.replace('_', ' ');
        }

        // Show transcript panel
        this.elements.transcriptPanel.classList.add('active');

        // Speak feedback
        if (result.voice_feedback) {
            this.speak(result.voice_feedback);
        }

        // Callback
        if (this.options.onTranscript) {
            this.options.onTranscript(result);
        }

        // If command was executed, show result
        if (result.execution_result) {
            if (this.options.onCommand) {
                this.options.onCommand(result.execution_result);
            }
        }

        // Show confirmation for uncertain commands
        if (transcription.confidence >= 0.5 && transcription.confidence < 0.8) {
            this.showConfirmation();
        }
    }

    startBrowserRecognition() {
        if (!this.SpeechRecognition) {
            this.showError('Browser does not support speech recognition. Using server mode.');
            this.options.useServerTranscription = true;
            this.startServerRecording();
            return;
        }

        this.recognition = new this.SpeechRecognition();
        this.recognition.continuous = this.options.continuousListening;
        this.recognition.lang = this.options.language;
        this.recognition.interimResults = true;

        this.recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const result = event.results[last];
            const transcript = result[0].transcript;
            const confidence = result[0].confidence;

            this.state.lastTranscript = transcript;
            this.state.lastConfidence = confidence;

            this.updateTranscriptDisplay(transcript, confidence);

            if (result.isFinal) {
                this.processLocalCommand(transcript);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error !== 'no-speech') {
                this.showError(`Recognition error: ${event.error}`);
            }
        };

        this.recognition.onend = () => {
            if (this.options.continuousListening && this.state.isListening) {
                setTimeout(() => {
                    try { this.recognition.start(); } catch (e) { }
                }, 500);
            }
        };

        this.recognition.start();
    }

    processLocalCommand(transcript) {
        // Send to server for processing
        fetch('/ai/voice-command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `voice_text=${encodeURIComponent(transcript)}`
        })
        .then(res => res.json())
        .then(result => {
            if (this.options.onCommand) {
                this.options.onCommand(result);
            }
        })
        .catch(err => console.error('Command processing error:', err));
    }

    updateState(newState) {
        Object.assign(this.state, newState);

        // Update UI based on state
        const { isListening, isProcessing } = this.state;

        // Microphone button
        this.elements.micBtn.classList.toggle('listening', isListening && !isProcessing);
        this.elements.micBtn.classList.toggle('processing', isProcessing);

        // Status indicator
        this.elements.statusDot.className = 'status-dot';
        if (isProcessing) {
            this.elements.statusDot.classList.add('processing');
            this.elements.statusText.textContent = 'Processing...';
        } else if (isListening) {
            this.elements.statusDot.classList.add('listening');
            this.elements.statusText.textContent = 'Listening...';
        } else {
            this.elements.statusDot.classList.add('ready');
            this.elements.statusText.textContent = 'Ready';
        }

        // Waveform
        this.elements.waveformContainer.classList.toggle('active', isListening);

        // Callback
        if (this.options.onStateChange) {
            this.options.onStateChange(this.state);
        }
    }

    updateTranscriptDisplay(transcript, confidence) {
        this.elements.transcriptText.textContent = transcript || 'Say "Hey ChatterFix" to start...';

        // Confidence badge
        const confidencePercent = Math.round(confidence * 100);
        this.elements.confidenceBadge.textContent = `${confidencePercent}%`;
        this.elements.confidenceBadge.className = 'confidence-badge';

        if (confidence >= 0.8) {
            this.elements.confidenceBadge.classList.add('high');
        } else if (confidence >= 0.5) {
            this.elements.confidenceBadge.classList.add('medium');
        } else {
            this.elements.confidenceBadge.classList.add('low');
        }
    }

    updateNoiseLevel(level) {
        this.elements.noiseLevel.textContent = level;
        this.elements.noiseIndicator.className = 'noise-indicator';
        if (level) {
            this.elements.noiseIndicator.classList.add(level);
        }
    }

    showConfirmation() {
        this.elements.confirmBtn.style.display = 'block';
        this.elements.cancelBtn.style.display = 'block';
    }

    hideConfirmation() {
        this.elements.confirmBtn.style.display = 'none';
        this.elements.cancelBtn.style.display = 'none';
    }

    confirmCommand() {
        this.hideConfirmation();
        this.processLocalCommand(this.state.lastTranscript);
        this.speak('Command confirmed');
    }

    cancelCommand() {
        this.hideConfirmation();
        this.speak('Command cancelled');
    }

    retry() {
        this.elements.retryBtn.style.display = 'none';
        this.elements.errorDisplay.style.display = 'none';
        this.start();
    }

    showError(message) {
        this.elements.errorText.textContent = message;
        this.elements.errorDisplay.style.display = 'flex';
        this.elements.retryBtn.style.display = 'block';

        this.elements.micBtn.classList.add('error');
        this.elements.statusDot.className = 'status-dot error';
        this.elements.statusText.textContent = 'Error';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.elements.errorDisplay.style.display = 'none';
            this.elements.micBtn.classList.remove('error');
        }, 5000);
    }

    speak(text) {
        if (this.synth.speaking) {
            this.synth.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.1;
        utterance.pitch = 1;
        this.synth.speak(utterance);
    }

    // Public API
    setLanguage(langCode) {
        this.options.language = langCode;
        if (this.recognition) {
            this.recognition.lang = langCode;
        }
    }

    getState() {
        return { ...this.state };
    }

    destroy() {
        this.stop();
        const container = document.getElementById(this.options.containerId);
        if (container) {
            container.innerHTML = '';
        }
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceFeedbackSystem;
}

// Auto-initialize if data attribute present
document.addEventListener('DOMContentLoaded', () => {
    const autoInit = document.querySelector('[data-voice-feedback-auto]');
    if (autoInit) {
        window.voiceFeedback = new VoiceFeedbackSystem({
            autoStart: autoInit.dataset.autoStart === 'true',
            useServerTranscription: autoInit.dataset.useServer !== 'false',
        });
    }
});

// Global access
window.VoiceFeedbackSystem = VoiceFeedbackSystem;
