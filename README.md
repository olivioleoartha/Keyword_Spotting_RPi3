
## DEVICE & OPERATING SYSTEM (OS)

- **Device** : Raspberry Pi 3 Model B+
- **Operating System** : Raspberry Pi OS (Legacy)
- **Architecture** : 32-bit
- **Base System** : Debian-based Linux

---

## MODEL

- **Model** : Vosk Speech Recognition
- **Variant** : vosk-model-small-en-us-0.15
- **Language** : English (US)
- **Type** : Lightweight / Small model
- **Purpose** : Real-time speech recognition on resource-constrained devices

---

## SOURCE

The Vosk model and toolkit are obtained from the official source:
https://alphacephei.com/vosk/models

---

## CONCEPT

The system captures conversational audio from a microphone through the ALSA
audio interface with an initial sampling rate of 44.1 kHz.
To match the requirements of the speech recognition model,
the audio is resampled and standardized to 16 kHz.

Audio is then processed incrementally using a windowing mechanism,
allowing continuous and low-latency analysis.
Before speech recognition is performed, the signal passes through
basic noise filtering and Voice Activity Detection (VAD)
to ensure that only segments containing human speech are processed.

Keyword Spotting is implemented using an
Automatic Speech Recognition (ASR)-based approach with Vosk.
The model is used with a limited grammar that focuses only on
service trigger keywords, such as session start and end commands.
Detection is not based on a single recognition result,
but on consistent keyword appearances across multiple audio windows,
which improves reliability and reduces false activations.

Once a service session is successfully triggered,
the system begins streaming conversational audio to the API server.
Audio is collected in one-second chunks and encoded in 16-bit PCM format
before being transmitted via the MQTT protocol.
Audio streaming remains active only while the service session is ongoing,
ensuring that the server processes audio strictly within the service context.
