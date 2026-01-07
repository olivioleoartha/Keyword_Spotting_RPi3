<h1>KEYWORD SPOTTING ENGINE FOR SMART SERVICE COMPLIANCE ASSISTANT'S PROJECT</h1>

<p align="justify">
Repository: https://github.com/vinsensutanto/smart-service-compliance
</p>

<hr>

<h3>DEVICE & OPERATING SYSTEM (OS)</h3>

<p align="justify">
<strong>Device</strong> : Raspberry Pi 3 Model B+<br>
<strong>Operating System</strong> : Raspberry Pi OS (Legacy)<br>
<strong>Architecture</strong> : 32-bit<br>
<strong>Base System</strong> : Debian-based Linux
</p>

<hr>

<h3>MODEL</h3>

<p align="justify">
<strong>Model</strong> : Vosk Speech Recognition<br>
<strong>Variant</strong> : vosk-model-small-en-us-0.15<br>
<strong>Language</strong> : English (US)<br>
<strong>Type</strong> : Lightweight / Small model<br>
<strong>Purpose</strong> : Real-time speech recognition on resource-constrained devices
</p>

<hr>

<h3>SOURCE</h3>

<p align="justify">
The Vosk model and toolkit are obtained from the official source:<br>
https://alphacephei.com/vosk/models
</p>

<hr>

<h3>CONCEPT</h3>

<p align="justify">
The system captures conversational audio from a microphone through the ALSA
audio interface with an initial sampling rate of 44.1 kHz.
To match the requirements of the speech recognition model,
the audio is resampled and standardized to 16 kHz.
</p>

<p align="justify">
Audio is then processed incrementally using a windowing mechanism,
allowing continuous and low-latency analysis.
Before speech recognition is performed, the signal passes through
basic noise filtering and Voice Activity Detection (VAD)
to ensure that only segments containing human speech are processed.
</p>

<p align="justify">
Keyword Spotting is implemented using an
Automatic Speech Recognition (ASR)-based approach with Vosk.
The model is used with a limited grammar that focuses only on
service trigger keywords, such as session start and end commands.
Detection is not based on a single recognition result,
but on consistent keyword appearances across multiple audio windows,
which improves reliability and reduces false activations.
</p>

<p align="justify">
Once a service session is successfully triggered,
the system begins streaming conversational audio to the API server.
Audio is collected in one-second chunks and encoded in 16-bit PCM format
before being transmitted via the MQTT protocol.
Audio streaming remains active only while the service session is ongoing,
ensuring that the server processes audio strictly within the service context.
</p>
