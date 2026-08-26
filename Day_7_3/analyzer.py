# analyzer.py
import time
from collections import Counter, defaultdict

class TypingAnalyzer:
    def __init__(self, target_text):
        self.target_text = target_text
        self.start_time = None
        self.end_time = None
        self.typed_text = ""
        self.keystrokes = 0
        self.backspaces = 0
        self.mistakes = defaultdict(int)
        self.timeline_wpm = []            # Timeline for plotting
        self.correct_chars = 0
        self.last_time = None              # For timeline interval tracking

    def start(self):
        self.start_time = time.time()
        self.last_time = self.start_time
        self.timeline_wpm = []

    def stop(self):
        self.end_time = time.time()
        # Add final timeline entry
        self._record_timeline(self.typed_text)

    def process_input(self, typed_text):
        if not self.start_time:
            self.start()

        # Count keystrokes and backspaces
        if len(typed_text) < len(self.typed_text):
            self.backspaces += len(self.typed_text) - len(typed_text)
        self.keystrokes += abs(len(typed_text) - len(self.typed_text))
        self.typed_text = typed_text

        # Reset mistakes and count correct chars
        self.mistakes.clear()
        self.correct_chars = 0
        for i, char in enumerate(typed_text):
            if i < len(self.target_text):
                if char != self.target_text[i]:
                    self.mistakes[self.target_text[i]] += 1
                else:
                    self.correct_chars += 1

        # Record timeline every ~0.5 seconds
        now = time.time()
        if not self.last_time or (now - self.last_time) >= 0.5:
            self._record_timeline(typed_text)
            self.last_time = now

    def _record_timeline(self, typed_text):
        elapsed = max(1/60, time.time() - self.start_time)
        words = len(typed_text) / 5
        raw_wpm = (words / elapsed) * 60
        accuracy_factor = self.correct_chars / max(len(typed_text), 1)
        adjusted_wpm = raw_wpm * accuracy_factor
        self.timeline_wpm.append(round(adjusted_wpm, 2))

    def calculate_results(self):
        if not self.start_time:
            return {
                "wpm": 0,
                "accuracy": 0,
                "keystrokes": 0,
                "backspaces": 0,
                "mistakes": {},
                "timeline": []
            }

        end_time = self.end_time or time.time()
        elapsed = max(1/60, end_time - self.start_time)
        total_chars = len(self.typed_text)
        raw_wpm = (total_chars / 5) / (elapsed/60)

        correct_chars = sum(
            1 for i in range(min(len(self.typed_text), len(self.target_text)))
            if self.typed_text[i] == self.target_text[i]
        )
        extra_chars = max(0, len(self.typed_text) - len(self.target_text))
        total_errors = sum(self.mistakes.values()) + extra_chars + self.backspaces

        accuracy = max(0, (correct_chars - total_errors) / max(len(self.target_text),1) * 100)
        adjusted_wpm = raw_wpm * (accuracy / 100)

        return {
            "wpm": round(adjusted_wpm, 2),
            "raw_wpm": round(raw_wpm, 2),
            "accuracy": round(accuracy, 2),
            "keystrokes": self.keystrokes,
            "backspaces": self.backspaces,
            "mistakes": dict(self.mistakes),
            "timeline": self.timeline_wpm
        }

    def get_weak_keys(self, top_n=5):
        return Counter(self.mistakes).most_common(top_n)

    def generate_insights(self):
        insights = []
        weak = self.get_weak_keys()
        if weak:
            insights.append(f"You often mistype '{weak[0][0]}'")
        if len(weak) > 1:
            insights.append(f"Common mistakes: '{weak[0][0]}' and '{weak[1][0]}'")
        if len(self.timeline_wpm) > 5 and self.timeline_wpm[-1] < self.timeline_wpm[0]:
            insights.append("Typing speed decreases over time. Keep a steady pace!")
        if self.backspaces > 0:
            insights.append(f"You used backspace {self.backspaces} times. Focus on accuracy.")
        insights.append("Practice weak keys daily.")
        insights.append("Prioritize accuracy before speed.")
        return insights