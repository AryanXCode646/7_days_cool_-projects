import cv2
import sys
import os
import datetime
import traceback
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vision import VisionSystem
from memory import MemorySystem
from prediction import PredictionEngine
from evolution import EvolutionEngine
from renderer import Renderer
from utils import FPSCounter, sanitize_points
from voice import VoiceSystem
from llm import get_reply
from detector import ObjectDetector

vision = VisionSystem()
memory = MemorySystem()
predictor = PredictionEngine()
evolution = EvolutionEngine()
renderer = Renderer()
fps_counter = FPSCounter()
voice = VoiceSystem()
detector = ObjectDetector()

def _log_exc(exc_type, exc, tb):
    try:
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('\n--- Unhandled Exception ---\n')
            traceback.print_exception(exc_type, exc, tb, file=f)
    except Exception:
        pass


def _thread_excepthook(args):
    _log_exc(args.exc_type, args.exc_value, args.exc_traceback)


sys.excepthook = _log_exc
if hasattr(threading, 'excepthook'):
    threading.excepthook = _thread_excepthook


try:
    # module-level state for detection throttles
    __detect_counter = 0
    __last_detection = None
    __last_detection_time = 0
    __last_response_time = 0

    while True:
        frame, landmarks, velocity, detected_objects = vision.get_frame()

        if frame is None:
            break

        # main loop body continues below (normal processing)

        transcript = voice.get_last_transcript()
        lang = voice.get_language()

        memory.update(landmarks, velocity, transcript)
        profile = memory.get_profile()

        staring = memory.is_staring()
        evolution.update(profile, staring, transcript)

        volume = voice.get_volume()

        if volume > 5:
            evolution.level += 0.1

        voice.update(evolution.level)

        predicted = predictor.predict(
            landmarks,
            strength=(evolution.level / 100) + (volume * 0.02)
        )

        autonomous_flag = False
        if evolution.independent_trigger():
            autonomous_flag = True
            predicted = evolution.autonomous_action(predicted)

        if predicted is not None:
            h, w, _ = frame.shape
            predicted = sanitize_points(predicted, w, h)

        sync = 100 - abs(evolution.level - 50)
        sync = max(0, min(100, sync))

        fps = fps_counter.update()

        # object detection every N frames
        __detect_counter += 1
        detection_text = None
        detection_conf = 0.0
        if __detect_counter % 15 == 0:
            try:
                dets = detector.detect(frame)
                if dets:
                    # take highest confidence
                    dets.sort(key=lambda x: x[1], reverse=True)
                    detection_text, detection_conf = dets[0]
            except Exception:
                detection_text = None

        # fallback to mediapipe hints (face/hand) when detector didn't return anything
        if detection_text is None and detected_objects:
            # choose most informative
            if 'phone' in detected_objects:
                detection_text = 'phone'
            else:
                detection_text = detected_objects[0]
            detection_conf = 1.0

        # announce detection when it changes (throttle)
        last_det = __last_detection
        last_time = __last_detection_time
        import time
        if detection_text and (detection_text != last_det) and (time.time() - last_time > 1.2):
            voice.respond(f"I see {detection_text}", lang='en' if lang != 'hi' else 'hi')
            __last_detection = detection_text
            __last_detection_time = time.time()

        # Keyword-driven immediate reactions & Daily Notes / Productivity Handling
        highlight = False
        if transcript:
            t = transcript.lower()
            
            # 1. Daily Notes / Task Manager Integration
            if any(k in t for k in ["take note", "save note", "add task", "add todo", "likh lo", "note banao"]):
                note_content = transcript
                for prefix in ["take note", "save note", "add task", "add todo", "likh lo", "note banao"]:
                    if prefix in t:
                        idx = t.find(prefix) + len(prefix)
                        note_content = transcript[idx:].strip(": ")
                        break
                if not note_content:
                    note_content = transcript
                try:
                    with open("daily_notes.txt", "a", encoding="utf-8") as nf:
                        nf.write(f"[{datetime.datetime.now().strftime('%I:%M %p')}] {note_content}\n")
                    reply = f"Saved note: {note_content}" if lang != 'hi' else f"नोट सहेज लिया गया: {note_content}"
                except Exception as e:
                    reply = "Could not save note."
                voice.respond(transcript, lang=lang, reply=reply)
                voice.last_transcript = None
                __last_response_time = time.time()

            elif any(k in t for k in ["read note", "read notes", "my tasks", "kya note hai", "tasks kya"]):
                try:
                    if os.path.exists("daily_notes.txt"):
                        with open("daily_notes.txt", "r", encoding="utf-8") as nf:
                            lines = [l.strip() for l in nf.readlines() if l.strip()]
                        recent = lines[-3:] if lines else []
                        if recent:
                            summary = "; ".join(recent)
                            reply = f"Your latest notes are: {summary}" if lang != 'hi' else f"आपके ताज़ा नोट्स हैं: {summary}"
                        else:
                            reply = "Your daily notes list is currently empty." if lang != 'hi' else "आपकी नोट्स सूची खाली है।"
                    else:
                        reply = "No notes saved yet."
                except Exception:
                    reply = "Unable to read notes."
                voice.respond(transcript, lang=lang, reply=reply)
                voice.last_transcript = None
                __last_response_time = time.time()

            # 2. General / Vision / Study Q&A
            else:
                question_words = ["what", "what's", "what is", "what are", "tell me", "kya", "ye kya", "batado", "batao", "kaun", "pomodoro", "study", "time", "date"]
                if any(q in t for q in question_words):
                    if detection_text:
                        prompt = f"The user asked: '{transcript}'. In the camera I see: {detection_text}. Reply concisely in the user's language."
                    else:
                        prompt = f"The user asked: '{transcript}'. Reply concisely and helpfully in the user's language."

                    reply = get_reply(prompt, lang=lang)
                    voice.respond(transcript, lang=lang, reply=reply)
                    voice.last_transcript = None
                    __last_response_time = time.time()
                else:
                    now = time.time()
                    if now - __last_response_time > 1.0:
                        prompt = f"User said: '{transcript}'. Camera observation: {detection_text or 'none'}. Reply concisely in the user's language."
                        reply = get_reply(prompt, lang=lang)
                        voice.respond(transcript, lang=lang, reply=reply)
                        voice.last_transcript = None
                        __last_response_time = now

            # English keywords for evolution
            if any(k in t for k in ["look", "stare", "predict", "hello", "hi"]):
                evolution.level = min(100, evolution.level + 2)
                highlight = True
            if any(k in t for k in ["stop", "leave", "no"]):
                evolution.level = max(0, evolution.level - 2)
                highlight = True
            # Hindi keywords
            if any(k in t for k in ["ruk", "rukna", "namaste", "hello", "haan"]):
                evolution.level = min(100, evolution.level + 2)
                highlight = True

        last_action = getattr(evolution, 'last_action', None)
        try:
            output = renderer.draw(frame, predicted, evolution, profile, fps, sync, volume, transcript, lang, highlight, autonomous_flag, last_action, detection_text, detection_conf)
        except Exception as e:
            # log and continue; avoid crashing the whole app due to render error
            print('Renderer error:', e)
            output = frame

        cv2.imshow("Digital Soul Engine", output)

        key = cv2.waitKey(1)

        if key == 27:
            break
        if key == ord('r'):
            evolution.level = 0
            memory.history.clear()

    cv2.destroyAllWindows()
except Exception:
    traceback.print_exc()
    _log_exc(*sys.exc_info())
    raise