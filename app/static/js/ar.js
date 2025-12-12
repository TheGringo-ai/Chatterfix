// Web Speech API Integration
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
        document.getElementById('voice-status').textContent = "LISTENING...";
        document.getElementById('voice-status').classList.add('voice-active');
    };

    recognition.onend = () => {
        document.getElementById('voice-status').textContent = "STANDBY";
        document.getElementById('voice-status').classList.remove('voice-active');
        // Auto-restart for continuous listening
        setTimeout(() => {
            try { recognition.start(); } catch (e) { }
        }, 1000);
    };

    recognition.onresult = (event) => {
        const last = event.results.length - 1;
        const command = event.results[last][0].transcript.trim().toLowerCase();
        console.log('Voice Command:', command);
        processCommand(command);
    };

    // Start listening on load
    window.addEventListener('load', () => {
        try { recognition.start(); } catch (e) { console.error(e); }
        speak("System online. Ready for commands.");
    });
} else {
    alert("Web Speech API not supported in this browser.");
}

function speak(text) {
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        return;
    }
    if (text !== '') {
        const utterThis = new SpeechSynthesisUtterance(text);
        utterThis.onend = function (event) {
            console.log('SpeechSynthesisUtterance.onend');
        }
        utterThis.onerror = function (event) {
            console.error('SpeechSynthesisUtterance.onerror');
        }
        synth.speak(utterThis);
    }
}

function processCommand(cmd) {
    document.getElementById('last-command').textContent = cmd;

    if (cmd.includes('work order') || cmd.includes('show orders')) {
        speak("Showing work orders.");
        window.location.href = '/ar/work-orders';
    } else if (cmd.includes('dashboard') || cmd.includes('home')) {
        speak("Returning to dashboard.");
        window.location.href = '/ar-mode';
    } else if (cmd.includes('read') || cmd.includes('details')) {
        const desc = document.getElementById('wo-description');
        if (desc) {
            speak(desc.textContent);
        } else {
            speak("No description available to read.");
        }
    } else if (cmd.includes('back')) {
        window.history.back();
    } else if (cmd.includes('select') || cmd.includes('open')) {
        // Logic to select items by number could go here
        speak("Selection command received.");
    }
}
