import requests
import datasets
import io
import soundfile as sf
# pip install datasets soundfile librosa

# API Endpoint
API_URL = "http://localhost:8000/stt"
HEADERS = {"User-Agent": "ovos-metrics"}

# Load Dataset from Hugging Face
dataset = datasets.load_dataset("Jarbas/VocativesEuropeanPortuguese", split="train")

# Default metadata
DEFAULT_MODEL = "community-dataset"
DEFAULT_PLUGIN = "ovos-stt-plugin"

for sample in dataset:
    print(sample)
    label = sample["transcript"]  # Wake word name
    sample_rate = sample["audio"]["sampling_rate"]  # Sample rate
    audio_array = sample["audio"]["array"]  # NumPy array

    # Convert NumPy array to WAV using soundfile
    audio_bytes = io.BytesIO()
    sf.write(audio_bytes, audio_array, sample_rate, format="WAV")
    audio_bytes.seek(0)  # Reset file pointer

    # Upload via REST API
    files = {"audio": ("stt.wav", audio_bytes, "audio/wav")}
    data = {
        "transcript": label,
        "lang": "pt",
        "model": DEFAULT_MODEL,
        "plugin": DEFAULT_PLUGIN,
        "plugin_config": "{}",
    }

    response = requests.post(API_URL, headers=HEADERS, data=data, files=files)

    if response.status_code == 200:
        print(f"✅ Uploaded: {label}")
    else:
        print(f"❌ Failed: {label} | {response.text}")
        exit()

print("🎉 STT import complete!")
