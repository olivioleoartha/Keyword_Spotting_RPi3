import json
import time
import queue
import base64
import sounddevice as sd
import numpy as np
import webrtcvad
from vosk import Model, KaldiRecognizer
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# CONFIG
RP_ID = "RP0001"
BROKER = "10.159.121.208"
PORT = 1883
MODEL_PATH = "model"

SAMPLE_RATE = 16000
BLOCK_SIZE = 640                
BYTES_PER_SEC = 32000
STREAM_SEC = 1
STREAM_BYTES = BYTES_PER_SEC * STREAM_SEC

MIN_DBFS = -35
VAD_RATIO_TH = 0.4

# WINDOW-BASED KWS
WINDOW = 5
COOLDOWN = 0.8

START_TH = 2
END_TH   = 4

START_WORDS = {
    "mulai", "mu", "mul", "lai"
}

END_WORDS = {
    "selesai", "sel", "se", "sai"}

GRAMMAR = list(START_WORDS | END_WORDS)

# SESSION LIMIT
MIN_SESSION_TIME = 1.2
MIN_CHUNKS_BEFORE_END = 2

# STATE
session_active = False
streaming_active = False

session_start_time = 0
last_event = 0
last_chunk_time = 0
chunk_number = 0

tokens = []

audio_q = queue.Queue()
audio_buffer = bytearray()

# VOICE ACTIVITY DETECTION (VAD)
vad = webrtcvad.Vad(2)

def pcm16_dbfs(pcm):
    pcm = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    if len(pcm) == 0:
        return -100
    rms = np.sqrt(np.mean(pcm ** 2))
    return 20 * np.log10(rms / 32768.0) if rms > 0 else -100

def has_speech(pcm):
    frame_size = int(SAMPLE_RATE * 0.02) * 2
    speech = total = 0
    for i in range(0, len(pcm), frame_size):
        frame = pcm[i:i + frame_size]
        if len(frame) < frame_size:
            continue
        total += 1
        if vad.is_speech(frame, SAMPLE_RATE):
            speech += 1
    return total > 0 and (speech / total) >= VAD_RATIO_TH

# AUDIO
def callback(indata, frames, time_info, status):
    audio_q.put(bytes(indata))

# MQTT
def on_connect(client, userdata, flags, reason_code, properties):
    print("MQTT CONNECT rc =", reason_code)
    client.subscribe(f"server/control/{RP_ID}/#")

def reset_state():
    global session_active, streaming_active
    global tokens, audio_buffer, chunk_number

    session_active = False
    streaming_active = False
    tokens.clear()
    audio_buffer.clear()
    chunk_number = 0

def on_message(client, userdata, msg):
    if msg.topic == f"server/control/{RP_ID}/end":
        reset_state()
        print("[SESSION END CONFIRMED & AUDIO STREAM ENDED]")

mqtt_client = mqtt.Client(
    client_id=f"RP_{RP_ID}",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_start()

def publish(topic, payload, pcm=b""):
    payload["audio"] = base64.b64encode(pcm).decode()
    payload["format"] = "pcm_s16le"
    payload["sample_rate"] = SAMPLE_RATE
    mqtt_client.publish(topic, json.dumps(payload), qos=1)

# MODEL (VOSK)
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE, json.dumps(GRAMMAR))
rec.SetWords(False)

# UTILS
def count_hits(tokens, vocab):
    return sum(1 for t in tokens if t in vocab)

# MAIN
with sd.RawInputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    dtype="int16",
    channels=1,
    callback=callback
):
    print("[KWS RASPBERRY PI READY]")

    while True:
        data = audio_q.get()

        # NOISE & SILENCE FILTER
        if pcm16_dbfs(data) < MIN_DBFS:
            continue
        if not has_speech(data):
            continue

        audio_buffer.extend(data)

        # KWS WINDOW LOGIC
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = res.get("text", "").strip()
            now = time.time()

            if not text:
                continue

            words = text.split()
            tokens.extend(words)
            tokens[:] = tokens[-WINDOW:]

            s_hits = count_hits(tokens, START_WORDS)
            e_hits = count_hits(tokens, END_WORDS)

            # IDLE
            if not session_active:
                print(f"[IDLE] '{text}' | START={s_hits}")

                if (
                    s_hits >= START_TH
                    and now - last_event > COOLDOWN
                ):
                    session_active = True
                    streaming_active = True
                    session_start_time = now
                    last_event = now

                    tokens.clear()
                    audio_buffer.clear()
                    chunk_number = 0

                    publish(
                        f"rp/{RP_ID}/event/kws/start",
                        {
                            "rp_id": RP_ID,
                            "event": "start",
                            "chunk_number": 0,
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                    print("[SESSION STARTED]")

            # ACTIVE
            else:
                print(f"[ACTIVE] '{text}' | START={s_hits} END={e_hits}")

                if (
                    e_hits >= END_TH
                    and now - last_event > COOLDOWN
                ):
                    last_event = now

                    publish(
                        f"rp/{RP_ID}/event/kws/end",
                        {
                            "rp_id": RP_ID,
                            "event": "end",
                            "chunk_number": chunk_number,
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                    print("[END SESSION TO BE CONFIRM]")

        # STREAMING AUDIO
        if streaming_active and len(audio_buffer) >= STREAM_BYTES:
            pcm = bytes(audio_buffer[:STREAM_BYTES])
            del audio_buffer[:STREAM_BYTES]

            if pcm16_dbfs(pcm) < MIN_DBFS:
                continue
            if not has_speech(pcm):
                continue

            chunk_number += 1
            last_chunk_time = time.time()

            publish(
                f"rp/{RP_ID}/audio/stream",
                {
                    "rp_id": RP_ID,
                    "chunk_number": chunk_number,
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                },
                pcm
            )
