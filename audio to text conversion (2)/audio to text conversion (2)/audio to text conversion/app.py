from flask import Flask, render_template, request, jsonify
import os
import librosa
import soundfile as sf
import speech_recognition as sr
import google.generativeai as genai  # Gemini API

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Gemini API (Replace with your actual API key)
genai.configure(api_key="AIzaSyDVJ1hk-cXUvcPc9J7b7_E2uM9XCjLbgm8")

def convert_mp3_to_wav(input_file, output_file):
    """Convert MP3 to WAV using librosa and soundfile."""
    audio, sr = librosa.load(input_file, sr=None)
    sf.write(output_file, audio, sr)

def transcribe_audio(audio_file):
    """Convert speech from an audio file to text using speech_recognition."""
    r = sr.Recognizer()
    
    if not audio_file.lower().endswith(".wav"):
        wav_file = audio_file.rsplit(".", 1)[0] + ".wav"
        convert_mp3_to_wav(audio_file, wav_file)
    else:
        wav_file = audio_file

    with sr.AudioFile(wav_file) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    
    return text

def summarize_text(text):
    """Summarize the transcribed text using Gemini API."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Summarize this text in a short paragraph: {text}")
        return response.text
    except Exception as e:
        return f"Summarization Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def upload_file():
    text = ""
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("index.html", text="No file uploaded", summary="")

        file = request.files["file"]
        if file.filename == "":
            return render_template("index.html", text="No file selected", summary="")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        try:
            text = transcribe_audio(file_path)
        except Exception as e:
            text = f"Error: {str(e)}"

        os.remove(file_path)

    return render_template("index.html", text=text, summary="")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    text = data.get("text", "")
    summary = summarize_text(text)
    return jsonify({"summary": summary})

if __name__ == "__main__":
    app.run(debug=True)
