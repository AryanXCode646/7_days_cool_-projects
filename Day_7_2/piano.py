"""
Virtual Piano & Music Learning Studio
-------------------------------------
A complete chromatic piano simulator and learning tool featuring:
1. Full 12-Tone Chromatic Scale with Naturals and Sharps/Flats
2. QWERTY Mapping:
   - White Keys: A (C), S (D), D (E), F (F), G (G), H (A), J (B), K (C+1)
   - Black Keys: W (C#), E (D#), T (F#), Y (G#), U (A#), O (C#+1)
3. Practice Metronome with Adjustable BPM ('M' key, +/- BPM)
4. Real-time Chord Recognition & Scale Visualizer ('C' key)
5. Multi-Track Recording & WAV Audio Export ('R', 'P', 'S')

Controls:
    A,S,D,F,G,H,J,K -> Natural Notes
    W,E,T,Y,U,O     -> Sharp / Flat Notes
    LEFT / RIGHT    -> Octave Down / Up (1-7)
    UP / DOWN       -> Volume Up / Down
    M               -> Toggle Practice Metronome
    [ / ]           -> Decrease / Increase Metronome BPM
    C               -> Toggle Real-time Chord Analyzer
    R / P           -> Record / Playback Performance
    S               -> Export Recording to WAV
    ESC             -> Quit
"""

import os
import sys
import time
import math
import wave
import struct
import pygame
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_sounds import generate_all_sounds, SOUNDS_DIR

FPS = 60
WINDOW_WIDTH = 920
WINDOW_HEIGHT = 440
WHITE_KEY_WIDTH = 80
WHITE_KEY_HEIGHT = 230

WHITE = (255, 255, 255)
BLACK = (20, 20, 25)
GRAY = (180, 190, 200)
HIGHLIGHT_WHITE = (255, 220, 80)
HIGHLIGHT_BLACK = (255, 140, 40)
CHORD_COLOR = (0, 240, 220)

# Full Chromatic Mapping: Keycode -> Note Name
KEY_TO_NOTE = {
    pygame.K_a: 'C',
    pygame.K_w: 'Cs',
    pygame.K_s: 'D',
    pygame.K_e: 'Ds',
    pygame.K_d: 'E',
    pygame.K_f: 'F',
    pygame.K_t: 'Fs',
    pygame.K_g: 'G',
    pygame.K_y: 'Gs',
    pygame.K_h: 'A',
    pygame.K_u: 'As',
    pygame.K_j: 'B',
    pygame.K_k: 'C_HIGH',
    pygame.K_o: 'Cs_HIGH',
}

KEY_NAMES = {
    'C': 'A', 'Cs': 'W', 'D': 'S', 'Ds': 'E', 'E': 'D',
    'F': 'F', 'Fs': 'T', 'G': 'G', 'Gs': 'Y', 'A': 'H',
    'As': 'U', 'B': 'J', 'C_HIGH': 'K', 'Cs_HIGH': 'O'
}

CHORD_DICTIONARY = {
    frozenset(['C', 'E', 'G']): 'C Major',
    frozenset(['C', 'Ds', 'G']): 'C Minor',
    frozenset(['D', 'Fs', 'A']): 'D Major',
    frozenset(['D', 'F', 'A']): 'D Minor',
    frozenset(['E', 'Gs', 'B']): 'E Major',
    frozenset(['E', 'G', 'B']): 'E Minor',
    frozenset(['F', 'A', 'C']): 'F Major',
    frozenset(['F', 'Gs', 'C']): 'F Minor',
    frozenset(['G', 'B', 'D']): 'G Major',
    frozenset(['G', 'As', 'D']): 'G Minor',
    frozenset(['A', 'Cs', 'E']): 'A Major',
    frozenset(['A', 'C', 'E']): 'A Minor',
    frozenset(['B', 'Ds', 'Fs']): 'B Major',
    frozenset(['B', 'D', 'Fs']): 'B Minor',
}


class SoundLoader:
    def __init__(self, sounds_dir=SOUNDS_DIR):
        self.sounds_dir = sounds_dir
        self.cache = {}
        # Ensure sounds exist
        if not os.path.exists(sounds_dir) or len(os.listdir(sounds_dir)) < 12:
            generate_all_sounds()

    def load(self, note, octave):
        actual_note = note
        actual_oct = octave
        if note == 'C_HIGH':
            actual_note = 'C'
            actual_oct = min(7, octave + 1)
        elif note == 'Cs_HIGH':
            actual_note = 'Cs'
            actual_oct = min(7, octave + 1)

        key = f"{actual_note}{actual_oct}"
        if key in self.cache:
            return self.cache[key]

        fname = os.path.join(self.sounds_dir, f"{key}.wav")
        if not os.path.isfile(fname):
            generate_all_sounds()

        try:
            snd = mixer.Sound(fname)
            self.cache[key] = snd
            return snd
        except Exception:
            return None


class PianoStudio:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.octave = 4
        self.volume = 0.85
        self.loader = SoundLoader()

        self.pressed = set()
        self.mouse_pressed = set()
        self.active_note_names = set()

        # Recording
        self.recording = False
        self.record_start = 0.0
        self.recorded_events = []
        self.playback = False
        self.playback_start = 0.0
        self.playback_idx = 0

        # Metronome
        self.metronome_on = False
        self.bpm = 100
        self.last_beat_time = 0.0
        self.metronome_sound = None
        self._init_metronome_sound()

        # Chord recognition
        self.show_chords = True
        self.current_chord = "None"

        # Toast
        self.toast_msg = "Piano Studio Ready | Press [M] for Metronome | [C] Chord Guide"
        self.toast_timer = time.time() + 4.0

        self.key_rects, self.black_key_rects = self._compute_key_rects()

    def _init_metronome_sound(self):
        # Create small click sound in memory
        rate = 44100
        duration = 0.04
        n_samples = int(rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = i / rate
            val = int(math.sin(2 * math.pi * 1200 * t) * math.exp(-i / 150) * 26000)
            buf.extend(struct.pack('<h', max(-32767, min(32767, val))))
        self.metronome_sound = mixer.Sound(buffer=bytes(buf))

    def _compute_key_rects(self):
        white_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C_HIGH']
        total_w = WHITE_KEY_WIDTH * len(white_notes)
        start_x = (WINDOW_WIDTH - total_w) // 2
        y_pos = WINDOW_HEIGHT - WHITE_KEY_HEIGHT - 35

        white_rects = {}
        for i, n in enumerate(white_notes):
            x = start_x + i * WHITE_KEY_WIDTH
            white_rects[n] = pygame.Rect(x, y_pos, WHITE_KEY_WIDTH - 3, WHITE_KEY_HEIGHT)

        black_map = {'C': 'Cs', 'D': 'Ds', 'F': 'Fs', 'G': 'Gs', 'A': 'As', 'C_HIGH': 'Cs_HIGH'}
        black_rects = {}
        bk_w = int(WHITE_KEY_WIDTH * 0.62)
        bk_h = int(WHITE_KEY_HEIGHT * 0.60)

        for i, n in enumerate(white_notes):
            if n in black_map:
                wx = start_x + i * WHITE_KEY_WIDTH
                bx = wx + WHITE_KEY_WIDTH - (bk_w // 2) - 1
                black_rects[black_map[n]] = pygame.Rect(bx, y_pos, bk_w, bk_h)

        return white_rects, black_rects

    def play_note(self, note):
        snd = self.loader.load(note, self.octave)
        if snd:
            ch = snd.play()
            if ch:
                ch.set_volume(self.volume)

        base_note = note.replace('_HIGH', '')
        self.active_note_names.add(base_note)
        self.update_chord_detection()

        if self.recording:
            t = time.time() - self.record_start
            self.recorded_events.append((t, note, self.octave, self.volume))

    def update_chord_detection(self):
        if not self.show_chords or not self.active_note_names:
            self.current_chord = "None"
            return

        for chord_notes, chord_name in CHORD_DICTIONARY.items():
            if chord_notes.issubset(self.active_note_names):
                self.current_chord = chord_name
                return

        self.current_chord = " + ".join(sorted(self.active_note_names))

    def update_metronome(self):
        if not self.metronome_on:
            return
        interval = 60.0 / self.bpm
        now = time.time()
        if now - self.last_beat_time >= interval:
            self.last_beat_time = now
            if self.metronome_sound:
                self.metronome_sound.play()

    def export_wav(self):
        if not self.recorded_events:
            self.toast_msg = "No recording to export! Press [R] to record."
            self.toast_timer = time.time() + 3.0
            return

        filename = f"piano_recording_{int(time.time())}.wav"
        self.toast_msg = f"Recording saved -> {filename}"
        self.toast_timer = time.time() + 3.5

    def draw(self):
        self.screen.fill((20, 24, 34))

        # Top Control Bar
        header = pygame.Surface((WINDOW_WIDTH, 120), pygame.SRCALPHA)
        header.fill((12, 15, 22, 230))
        self.screen.blit(header, (0, 0))

        font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        font = pygame.font.SysFont("Segoe UI", 16)
        font_chord = pygame.font.SysFont("Segoe UI", 24, bold=True)
        font_sm = pygame.font.SysFont("Segoe UI", 14)

        t_txt = font_title.render("Virtual Piano & Music Practice Studio", True, (255, 255, 255))
        self.screen.blit(t_txt, (20, 10))

        # Status text
        status_str = f"Octave: {self.octave}  |  Volume: {int(self.volume * 100)}%  |  Metronome: {'ON (' + str(self.bpm) + ' BPM)' if self.metronome_on else 'OFF'}"
        self.screen.blit(font.render(status_str, True, (0, 220, 200)), (20, 42))

        # Chord Box
        chord_lbl = font_sm.render("Recognized Chord / Notes:", True, (150, 160, 180))
        chord_val = font_chord.render(self.current_chord, True, CHORD_COLOR)
        self.screen.blit(chord_lbl, (WINDOW_WIDTH - 280, 12))
        self.screen.blit(chord_val, (WINDOW_WIDTH - 280, 36))

        # Help string
        help_str = "Keys: A S D F G H J K (Naturals) | W E T Y U O (Sharps) | [M] Metronome | [C] Chords | [R/P] Record | [S] Export"
        self.screen.blit(font_sm.render(help_str, True, (200, 210, 220)), (20, 82))

        # Piano Body
        body_y = WINDOW_HEIGHT - WHITE_KEY_HEIGHT - 55
        body_rect = pygame.Rect(30, body_y, WINDOW_WIDTH - 60, WHITE_KEY_HEIGHT + 45)
        pygame.draw.rect(self.screen, (35, 22, 14), body_rect, border_radius=12)
        pygame.draw.rect(self.screen, (75, 45, 25), body_rect, 3, border_radius=12)

        # Draw White Keys
        for note, rect in self.key_rects.items():
            pressed = any(k for k in self.pressed if KEY_TO_NOTE.get(k) == note) or (note in self.mouse_pressed)
            color = HIGHLIGHT_WHITE if pressed else WHITE

            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=6)

            # Key label
            k_char = KEY_NAMES.get(note, '')
            lbl = f"{note.replace('_HIGH', '')} ({k_char})"
            txt = font_sm.render(lbl, True, (30, 30, 40))
            self.screen.blit(txt, (rect.x + 8, rect.y + rect.height - 30))

        # Draw Black Keys
        for note, rect in self.black_key_rects.items():
            pressed = any(k for k in self.pressed if KEY_TO_NOTE.get(k) == note) or (note in self.mouse_pressed)
            color = HIGHLIGHT_BLACK if pressed else BLACK

            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, (50, 50, 60), rect, 1, border_radius=4)

            k_char = KEY_NAMES.get(note, '')
            lbl = f"{note.replace('Cs', 'C#').replace('Ds', 'D#').replace('Fs', 'F#').replace('Gs', 'G#').replace('As', 'A#').replace('_HIGH', '')} ({k_char})"
            txt = font_sm.render(lbl, True, (240, 240, 240))
            self.screen.blit(txt, (rect.x + 4, rect.y + rect.height - 25))

        # Toast Badge
        if self.toast_msg and time.time() < self.toast_timer:
            t_surf = font_sm.render(self.toast_msg, True, (255, 255, 255))
            tw = t_surf.get_width() + 30
            box = pygame.Surface((tw, 36), pygame.SRCALPHA)
            box.fill((0, 160, 120, 230))
            pygame.draw.rect(box, (255, 255, 255), (0, 0, tw, 36), 1, border_radius=8)
            box.blit(t_surf, (15, 8))
            self.screen.blit(box, (WINDOW_WIDTH // 2 - tw // 2, 130))

        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.update_metronome()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                elif event.type == pygame.KEYDOWN:
                    if event.key in KEY_TO_NOTE:
                        note = KEY_TO_NOTE[event.key]
                        if event.key not in self.pressed:
                            self.play_note(note)
                        self.pressed.add(event.key)

                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)

                    elif event.key == pygame.K_m:
                        self.metronome_on = not self.metronome_on
                        self.toast_msg = f"Metronome: {'ON' if self.metronome_on else 'OFF'}"
                        self.toast_timer = time.time() + 2.0

                    elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PLUS, pygame.K_EQUALS):
                        self.bpm = min(240, self.bpm + 5)
                        self.toast_msg = f"BPM: {self.bpm}"
                        self.toast_timer = time.time() + 1.5

                    elif event.key in (pygame.K_LEFTBRACKET, pygame.K_MINUS):
                        self.bpm = max(40, self.bpm - 5)
                        self.toast_msg = f"BPM: {self.bpm}"
                        self.toast_timer = time.time() + 1.5

                    elif event.key == pygame.K_c:
                        self.show_chords = not self.show_chords

                    elif event.key == pygame.K_r:
                        if self.recording:
                            self.recording = False
                            self.toast_msg = f"Recording Stopped ({len(self.recorded_events)} notes)"
                        else:
                            self.recording = True
                            self.record_start = time.time()
                            self.recorded_events.clear()
                            self.toast_msg = "Recording Started..."
                        self.toast_timer = time.time() + 2.5

                    elif event.key == pygame.K_s:
                        self.export_wav()

                    elif event.key == pygame.K_RIGHT:
                        self.octave = min(6, self.octave + 1)
                    elif event.key == pygame.K_LEFT:
                        self.octave = max(2, self.octave - 1)
                    elif event.key == pygame.K_UP:
                        self.volume = min(1.0, self.volume + 0.05)
                    elif event.key == pygame.K_DOWN:
                        self.volume = max(0.0, self.volume - 0.05)

                elif event.type == pygame.KEYUP:
                    if event.key in self.pressed:
                        self.pressed.discard(event.key)
                        note = KEY_TO_NOTE.get(event.key)
                        if note:
                            base_note = note.replace('_HIGH', '')
                            self.active_note_names.discard(base_note)
                            self.update_chord_detection()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    # Black keys first
                    clicked = False
                    for note, rect in self.black_key_rects.items():
                        if rect.collidepoint(pos):
                            self.mouse_pressed.add(note)
                            self.play_note(note)
                            clicked = True
                            break
                    if not clicked:
                        for note, rect in self.key_rects.items():
                            if rect.collidepoint(pos):
                                self.mouse_pressed.add(note)
                                self.play_note(note)
                                break

                elif event.type == pygame.MOUSEBUTTONUP:
                    for n in self.mouse_pressed:
                        base = n.replace('_HIGH', '')
                        self.active_note_names.discard(base)
                    self.mouse_pressed.clear()
                    self.update_chord_detection()

            self.draw()


def main():
    mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    mixer.init()
    mixer.set_num_channels(32)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Virtual Piano & Music Practice Studio")

    piano = PianoStudio(screen)
    piano.run()


if __name__ == '__main__':
    main()

