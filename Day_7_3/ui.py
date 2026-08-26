import random, os, time, math, tempfile, struct, wave, winsound, json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from analyzer import TypingAnalyzer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# ---------------- COLORS ----------------
BG_START = "#0b0b0b"
BG_END = "#1c1c1c"
CARD_BG = "#1f1f1f"
TEXT_MAIN = "#e0e0e0"
TEXT_ACCENT = "#ffeb3b"
TEXT_ERROR = "#ff4d4d"
BUTTON_PRIMARY = "#ff6b6b"
BUTTON_HOVER = "#ff4d4d"
SUBTEXT = "#888"

# ---------------- DEVELOPER CODE SNIPPETS ----------------
CODE_SNIPPETS = [
    "def calculate_total(items, tax_rate=0.08):\n    return sum(item['price'] * (1 + tax_rate) for item in items)",
    "const fetchUserData = async (userId) => {\n    const response = await fetch(`/api/users/${userId}`);\n    return response.json();\n};",
    "SELECT users.id, users.name, COUNT(orders.id) AS total_orders\nFROM users JOIN orders ON users.id = orders.user_id\nGROUP BY users.id HAVING total_orders > 5;",
    "docker run -d -p 8080:80 --name web_service -v $(pwd)/app:/var/www/html nginx:alpine",
    "git commit -m 'feat(auth): implement jwt session token verification middleware' && git push origin main",
    "for (let i = 0; i < array.length; i++) {\n    if (array[i] % 2 === 0) {\n        console.log(`Even: ${array[i]}`);\n    }\n}",
    "class DataPipeline:\n    def __init__(self, source, sink):\n        self.source = source\n        self.sink = sink",
]

# ---------------- MECHANICAL KEY SOUND ----------------
def play_mechanical_key():
    try:
        sample_rate = 44100
        duration = 0.08
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        filename = temp_file.name
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                thump = math.sin(2 * math.pi * 95 * t) * math.exp(-i / 900)
                clack = math.sin(2 * math.pi * 450 * t) * math.exp(-i / 400)
                combined = (thump * 0.55 + clack * 0.35) * random.uniform(0.95, 1.05)
                val = int(max(-1, min(1, combined)) * 32000)
                wav_file.writeframes(struct.pack('<h', val))
        winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception:
        pass


# ---------------- TYPING APP ----------------
class TypingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Typing Analyzer Pro — Developer & Productivity Edition")
        self.resize(1180, 750)
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {BG_START}, stop:1 {BG_END});
                color: {TEXT_MAIN};
                font-family: Consolas, 'Courier New', monospace;
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 25, 40, 25)
        self.main_layout.setSpacing(12)

        # Mode selector
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Wisdom & Quotes", "Developer Code Syntax", "Custom Study Notes", "Weak-Key Drill"])
        self.mode_selector.setStyleSheet(f"""
            QComboBox {{
                background:{CARD_BG}; padding:8px 16px; border-radius:8px; color:{TEXT_MAIN}; font-size:15px; border:1px solid #333;
            }}
        """)
        self.mode_selector.currentIndexChanged.connect(self.new_sentence)

        # Word count selector
        self.word_selector = QComboBox()
        self.word_selector.addItems(["15", "25", "50", "100"])
        self.word_selector.setCurrentText("25")
        self.word_selector.setStyleSheet(f"""
            QComboBox {{
                background:{CARD_BG}; padding:8px 16px; border-radius:8px; color:{TEXT_MAIN}; font-size:15px; border:1px solid #333;
            }}
        """)
        self.word_selector.currentIndexChanged.connect(self.new_sentence)

        self.custom_text = ""
        self.lifetime_weak_keys = []
        self.start_screen()

    # ---------------- START SCREEN ----------------
    def start_screen(self):
        self.clear_layout()
        self.start_t = None
        self.buffer = ""

        # Top selector layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Practice Mode:"), alignment=Qt.AlignRight)
        top.addWidget(self.mode_selector, alignment=Qt.AlignLeft)
        top.addSpacing(20)
        top.addWidget(QLabel("Length:"), alignment=Qt.AlignRight)
        top.addWidget(self.word_selector, alignment=Qt.AlignLeft)
        top.addStretch()

        # Custom text paste button
        custom_btn = QPushButton("Paste Study Text")
        custom_btn.setStyleSheet("background:#2a2f3a; padding:6px 14px; border-radius:8px; font-size:14px;")
        custom_btn.clicked.connect(self.open_custom_text_dialog)
        top.addWidget(custom_btn)

        self.main_layout.addLayout(top)

        # Typing card
        self.card = QFrame()
        self.card.setStyleSheet(f"QFrame {{ background:{CARD_BG}; border-radius:18px; padding:30px; border:1px solid #2a2a2a; }}")
        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(15)

        # Display label
        self.text_display = QLabel()
        self.text_display.setWordWrap(True)
        self.text_display.setAlignment(Qt.AlignCenter)
        self.text_display.setStyleSheet("font-size:26px; line-height:1.6;")
        card_layout.addWidget(self.text_display)

        # Hidden input
        self.input = QLineEdit()
        self.input.setFixedSize(1, 1)
        self.input.setStyleSheet("border:none; background:transparent; color:transparent;")
        self.input.textChanged.connect(self.on_type)
        self.input.installEventFilter(self)
        self.input.setFocusPolicy(Qt.StrongFocus)
        card_layout.addWidget(self.input)
        self.main_layout.addWidget(self.card, stretch=6)

        # Stats
        self.stats = QLabel("0 WPM   0% ACC")
        self.stats.setAlignment(Qt.AlignCenter)
        self.stats.setStyleSheet(f"color:{SUBTEXT}; font-size:22px; font-weight:bold;")
        self.main_layout.addWidget(self.stats)

        # Controls Hint
        hint = QLabel("[TAB] Restart Test  |  [Mode] Switch to Developer Code or Study Text")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#666; font-size:13px;")
        self.main_layout.addWidget(hint)

        # Restart button
        self.restart_btn = QPushButton("Restart Test")
        self.restart_btn.setStyleSheet(f"""
            QPushButton {{ background:{BUTTON_PRIMARY}; color:#111; font-size:16px; font-weight:bold; padding:10px 24px; border-radius:10px; }}
            QPushButton:hover {{ background:{BUTTON_HOVER}; }}
        """)
        self.restart_btn.clicked.connect(self.start_screen)
        self.main_layout.addWidget(self.restart_btn, alignment=Qt.AlignCenter)

        # Generate first sentence
        self.new_sentence()
        QTimer.singleShot(60, self.input.setFocus)

    def open_custom_text_dialog(self):
        text, ok = QInputDialog.getMultiLineText(self, "Paste Study Text", "Paste any text, vocabulary list, or notes to practice:")
        if ok and text.strip():
            self.custom_text = text.strip()
            self.mode_selector.setCurrentText("Custom Study Notes")
            self.new_sentence()

    # ---------------- NEW SENTENCE ----------------
    def new_sentence(self):
        mode = self.mode_selector.currentText()
        word_count = int(self.word_selector.currentText())

        if mode == "Developer Code Syntax":
            self.target = random.choice(CODE_SNIPPETS)
        elif mode == "Custom Study Notes" and self.custom_text:
            self.target = self.custom_text
        elif mode == "Weak-Key Drill" and self.lifetime_weak_keys:
            # Generate targeted drill for weak keys
            keys = "".join([k[0] for k in self.lifetime_weak_keys[:3]])
            drill_words = [f"{keys}{random.choice('aeiou')}{keys}" for _ in range(word_count)]
            self.target = " ".join(drill_words)
        else:
            self.target = self.generate_dynamic_text(word_count)

        self.buffer = ""
        if hasattr(self, "input"):
            self.input.clear()
            QTimer.singleShot(60, self.input.setFocus)
        self.update_text("")
        self.analyzer = TypingAnalyzer(self.target)
        self.analyzer.start()

    # ---------------- DYNAMIC TEXT (paragraph style) ----------------
    def generate_dynamic_text(self, word_count):
        corpus = """
        The art of programming is the ability to believe that a complex system 
        can be built from simple parts. Efficiency is doing things right, but 
        effectiveness is doing the right things at the right time. In the world 
        of software, the only constant is change and the evolution of logic. 
        Success in typing depends more on consistent practice than on speed. 
        An algorithm is a set of steps designed to solve a problem efficiently. 
        Great developers design solutions that help people solve real problems. 
        Artificial intelligence is a tool to amplify our creative capabilities.
        Stay curious, stay humble, and never stop learning new things every day.
        The keyboard is a piano, and the code is the symphony we compose together.
        Focus on the rhythm of the keys and the flow of the sentences. Deep work 
        allows us to master difficult tasks and produce at an elite level. 
        Innovation comes from the intersection of technology and human intent.
        Every line of code is a signature of the author's creative mind.
        """
        words = corpus.split()
        chain = {}
        for i in range(len(words) - 2):
            key = (words[i], words[i + 1])
            if key not in chain:
                chain[key] = []
            chain[key].append(words[i + 2])

        starters = [i for i in range(len(words) - 2) if words[i][0].isupper()]
        idx = random.choice(starters)
        current_key = (words[idx], words[idx + 1])
        result = [words[idx], words[idx + 1]]

        while len(result) < word_count:
            if current_key in chain:
                next_word = random.choice(chain[current_key])
                result.append(next_word)
                current_key = (current_key[1], next_word)
            else:
                new_idx = random.choice(starters)
                result.append(words[new_idx])
                current_key = (words[new_idx], words[new_idx + 1])

        final_sentence = " ".join(result[:word_count])
        if not final_sentence.endswith(('.', '!', '?')):
            final_sentence = final_sentence.rstrip(', ') + "."
        return final_sentence.capitalize()

    # ---------------- TYPING ----------------
    def on_type(self):
        typed = self.input.text()
        if typed:
            play_mechanical_key()

        if not self.start_t:
            self.start_t = time.time()
            self.analyzer.start_time = self.start_t

        self.buffer = typed
        self.analyzer.process_input(typed)

        elapsed = max(1 / 60, time.time() - self.start_t)
        correct_chars = sum(1 for i, c in enumerate(typed) if i < len(self.target) and c == self.target[i])
        wpm = round((correct_chars / 5) / (elapsed / 60))
        accuracy = round((correct_chars / max(len(typed), 1)) * 100)
        self.stats.setText(f"{wpm} WPM   {accuracy}% ACC")

        self.update_text(typed)

        if len(typed) >= len(self.target):
            self.analyzer.stop()
            results = self.analyzer.calculate_results()
            self.final_results = results
            self.final_weak = self.analyzer.get_weak_keys()
            self.lifetime_weak_keys = self.final_weak
            self.final_insights = self.analyzer.generate_insights()
            self.save_session_history(results)
            self.show_results()

    def save_session_history(self, results):
        history_file = "typing_history.json"
        history = []
        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "wpm": results.get("wpm", 0),
                "accuracy": results.get("accuracy", 0),
                "mode": self.mode_selector.currentText()
            })
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history[-30:], f, indent=2)
        except Exception:
            pass

    # ---------------- UPDATE TEXT ----------------
    def update_text(self, typed):
        styled = ""
        for i, char in enumerate(self.target):
            display_char = char
            if char == '\n':
                display_char = ' ↵\n'

            if i < len(typed):
                color = TEXT_ACCENT if typed[i] == char else TEXT_ERROR
                styled += f'<span style="color:{color};">{display_char}</span>'
            else:
                styled += f'<span style="color:#666;">{display_char}</span>'
        self.text_display.setText(styled)

    # ---------------- RESULTS ----------------
    def show_results(self):
        self.clear_layout()
        results = getattr(self, "final_results", {"wpm": 0, "accuracy": 0, "timeline": []})
        weak = getattr(self, "final_weak", [])
        insights = getattr(self, "final_insights", [])

        wpm = QLabel(f"{results['wpm']}")
        wpm.setAlignment(Qt.AlignCenter)
        wpm.setStyleSheet(f"font-size:90px; color:{TEXT_ACCENT}; font-weight:bold;")
        label = QLabel("WPM")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color:{SUBTEXT}; font-size:22px;")

        acc = QLabel(f"{results['accuracy']}% Accuracy")
        acc.setAlignment(Qt.AlignCenter)
        acc.setStyleSheet(f"color:#4caf50; font-size:24px; font-weight:bold;")

        weak_text = "\n".join([f"Key '{k}' → {v} errors" for k, v in weak]) or "None! Flawless execution."
        weak_label = QLabel(f"Weak Key Breakdown:\n{weak_text}")
        weak_label.setAlignment(Qt.AlignCenter)
        weak_label.setStyleSheet(f"color:{BUTTON_PRIMARY}; font-size:16px;")

        insights_label = QLabel("\n".join(insights))
        insights_label.setAlignment(Qt.AlignCenter)
        insights_label.setStyleSheet("color:#bbb; font-size:15px;")

        fig, ax = plt.subplots(figsize=(10, 3))
        if results.get("timeline"):
            ax.plot(results["timeline"], color=TEXT_ACCENT, linewidth=2, marker='o', markersize=3)
        ax.set_title("WPM Speed Velocity Over Session", color=TEXT_ACCENT, fontsize=12)
        ax.set_facecolor(CARD_BG)
        fig.patch.set_facecolor(BG_START)
        ax.tick_params(colors=TEXT_MAIN)
        canvas = FigureCanvas(fig)

        self.main_layout.addWidget(wpm)
        self.main_layout.addWidget(label)
        self.main_layout.addWidget(acc)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(weak_label)
        self.main_layout.addWidget(insights_label)
        self.main_layout.addWidget(canvas)

        restart = QPushButton("Start Next Practice Session")
        restart.setStyleSheet(f"""
            QPushButton {{ background:{BUTTON_PRIMARY}; padding:12px 28px; border-radius:10px; font-size:16px; font-weight:bold; }}
            QPushButton:hover {{ background:{BUTTON_HOVER}; }}
        """)
        restart.clicked.connect(self.start_screen)
        self.main_layout.addWidget(restart, alignment=Qt.AlignCenter)

    # ---------------- UTILS ----------------
    def clear_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

    # ---------------- KEYBOARD SHORTCUT ----------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.start_screen()
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.start_screen()
                return True
        return super().eventFilter(obj, event)


# ---------------- RUN ----------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = TypingApp()
    w.show()
    sys.exit(app.exec_())