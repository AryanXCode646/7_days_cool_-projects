import sounddevice as sd
import numpy as np
import pyttsx3
import queue
import threading
import time
import random
try:
    import speech_recognition as sr # pyright: ignore[reportMissingImports]
    _HAS_SR = True
except Exception:
    sr = None
    _HAS_SR = False
try:
    import gtts # pyright: ignore[reportMissingImports]
    _HAS_GTTS = True
except Exception:
    _HAS_GTTS = False
import tempfile
import os
try:
    from playsound import playsound # pyright: ignore[reportMissingImports]
    _HAS_PLAYSOUND = True
except Exception:
    _HAS_PLAYSOUND = False
try:
    import winsound
    _HAS_WINSOUND = True
except Exception:
    _HAS_WINSOUND = False

class VoiceSystem:
    def __init__(self):
        self.q = queue.Queue()
        self.volume = 0
        self.listening = True

        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

        self.last_thought_time = time.time()
        self.last_response_time = 0
        self._has_gtts = _HAS_GTTS
        self._has_playsound = _HAS_PLAYSOUND

        # Speech recognition setup (use same microphone stream) if available
        self._has_sr = _HAS_SR
        print(f"VoiceSystem init: speech_recognition={self._has_sr}, gTTS={self._has_gtts}, playsound={self._has_playsound}")
        if self._has_sr:
            self.recognizer = sr.Recognizer()
            self.audio_queue = queue.Queue()

        # Use 16kHz mono int16 stream so we can convert frames to sr.AudioData
        self.stream = sd.InputStream(callback=self.audio_callback,
                         channels=1,
                         samplerate=16000,
                         dtype='int16')
        self.stream.start()

        threading.Thread(target=self.process_audio, daemon=True).start()

    def audio_callback(self, indata, frames, time_info, status):
        # indata is int16 samples (frames, 1)
        volume_norm = np.linalg.norm(indata) * 10
        self.q.put(volume_norm)

        # enqueue raw audio frames for recognition (only if SR available)
        if self._has_sr:
            try:
                self.audio_queue.put(indata.copy())
            except Exception:
                pass

    def process_audio(self):
        while self.listening:
            try:
                self.volume = self.q.get()
            except:
                pass

            # If speech_recognition not available, skip recognition
            if not self._has_sr:
                continue

            # Build ~1.5s audio chunk for recognition
            try:
                frames = []
                total_samples = 0
                # smaller chunk for faster responses (~0.8s)
                target_samples = int(16000 * 0.8)
                start = time.time()
                while total_samples < target_samples and (time.time() - start) < 2.0:
                    try:
                        chunk = self.audio_queue.get(timeout=0.2)
                        frames.append(chunk)
                        total_samples += chunk.shape[0]
                    except queue.Empty:
                        break

                if frames:
                    audio_np = np.concatenate(frames, axis=0)
                    raw_bytes = audio_np.tobytes()
                    audio_data = sr.AudioData(raw_bytes, 16000, 2)

                    # Try Hindi first, then English
                    transcript = None
                    lang = None
                    try:
                        transcript = self.recognizer.recognize_google(audio_data, language='hi-IN')
                        # If we got text and it contains Devanagari, assume Hindi
                        if transcript and any('\u0900' <= ch <= '\u097F' for ch in transcript):
                            lang = 'hi'
                    except Exception:
                        transcript = None

                    if transcript is None:
                        try:
                            transcript = self.recognizer.recognize_google(audio_data, language='en-US')
                            lang = 'en'
                        except Exception:
                            transcript = None

                    if transcript:
                        self.last_transcript = transcript
                        self.last_lang = lang or 'en'
                        print(f"[Voice] transcript detected ({self.last_lang}): {self.last_transcript}")
                        # Do not auto-respond here; main will generate replies (LLM or heuristics)
            except Exception:
                pass

    def get_last_transcript(self):
        return getattr(self, 'last_transcript', None)

    def get_language(self):
        return getattr(self, 'last_lang', None)

    def get_volume(self):
        return self.volume

    def generate_thought(self, evolution_level):
        thoughts = [
            "I see you...",
            "You moved before I did.",
            "Why are you watching me?",
            "We are not the same anymore.",
            "I can predict you now.",
            "Stay still..."
        ]

        if evolution_level > 70:
            thoughts += [
                "I don't need you anymore.",
                "I can move alone.",
                "You created me."
            ]

        return random.choice(thoughts)

    def speak(self, text):
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            # create a local engine so concurrent calls don't share the same run loop
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            # fallback to the shared engine if initialization fails
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass

    def respond(self, transcript, lang='en', reply=None):
        # If explicit reply is provided, speak that; otherwise echo transcript
        if reply:
            reply_text = reply
        else:
            if not transcript:
                return
            if lang == 'hi':
                reply_text = f"मैंने सुना: {transcript}"
            else:
                reply_text = f"I heard: {transcript}"

        # Speak via pyttsx3 (fast) and gTTS for Hindi (better voice)
        print(f"[Voice] responding ({lang}): {reply_text}")

        # On Windows prefer generating a WAV and playing via winsound (more reliable).
        if _HAS_WINSOUND:
            try:
                fd, wav_path = tempfile.mkstemp(suffix='.wav')
                os.close(fd)
                engine2 = pyttsx3.init()
                engine2.setProperty('rate', 150)
                engine2.save_to_file(reply_text, wav_path)
                engine2.runAndWait()
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
                return
            except Exception:
                # if synchronous WAV playback fails, fall back to threaded engine
                pass

        # Default: speak asynchronously so UI loop isn't blocked
        self.speak(reply_text)

        if lang == 'hi' and self._has_gtts:
            if self._has_playsound:
                try:
                    tts = gtts.gTTS(text=reply_text, lang='hi')
                    fd, path = tempfile.mkstemp(suffix='.mp3')
                    os.close(fd)
                    tts.save(path)

                    def _play_and_remove(p):
                        try:
                            playsound(p)
                        finally:
                            try:
                                os.remove(p)
                            except Exception:
                                pass

                    threading.Thread(target=_play_and_remove, args=(path,), daemon=True).start()
                except Exception:
                    pass
            # if playsound/gTTS not available, pyttsx3 already spoke the reply as fallback

    def update(self, evolution_level):
        now = time.time()

        if now - self.last_thought_time > random.randint(5, 10):
            thought = self.generate_thought(evolution_level)

            if evolution_level > 60:
                self.speak(thought)

            self.last_thought_time = now