import numpy as np
import sounddevice as sd
import csv
import os
import random
import threading
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, 
    Footer, 
    Button, 
    Label, 
    Static, 
    ProgressBar, 
    Input, 
    ListItem, 
    ListView, 
    RichLog
)
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message

# --- SCIENTIFIC CONSTANTS ---
LFO_RATE = 4.0        # Hz: Psychoacoustic rate to bypass neural adaptation
LFO_DEPTH = 0.05      # 5%: Prevents standing waves
SAMPLE_RATE = 44100
BASE_AMPLITUDE = 0.3  

ISO_FREQS = [
    1000.0, 40.0, 4000.0, 125.0, 800.0, 25.0, 500.0, 12500.0, 63.0, 2500.0, 20.0, 
    1600.0, 31.5, 10000.0, 80.0, 2000.0, 200.0, 16000.0, 50.0, 6300.0, 315.0, 
    20000.0, 100.0, 3150.0, 160.0, 5000.0, 250.0, 630.0, 1250.0, 400.0
]

class FileSelected(Message):
    def __init__(self, filename: str, mode: str, force: bool = False) -> None:
        self.filename = filename
        self.mode = mode
        self.force = force
        super().__init__()

class OverwriteScreen(Screen):
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Cancel")
    ]
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm_panel"):
            yield Label(f"FILE EXISTS: {self.filename}", id="confirm_title")
            yield Label("Overwrite this profile?", id="confirm_msg")
            with Horizontal(id="confirm_buttons"):
                yield Button("Cancel (Esc)", id="cancel_ovr", variant="error")
                yield Button("Overwrite", id="confirm_ovr", variant="primary")

    def action_dismiss_screen(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_ovr":
            self.post_message(FileSelected(self.filename, "save", force=True))
        self.action_dismiss_screen()

class FileBrowserScreen(Screen):
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Exit"), 
        Binding("enter", "submit", "Confirm"),
        Binding("up", "ignore", "", show=False),
        Binding("down", "ignore", "", show=False),
        Binding("left", "ignore", "", show=False),
        Binding("right", "ignore", "", show=False)
    ]
    
    def action_ignore(self) -> None:
        """Consume arrow key events to prevent bubbling to main app."""
        pass

    def __init__(self, mode="load"):
        super().__init__()
        self.mode = mode

    def compose(self) -> ComposeResult:
        files = sorted([f for f in os.listdir('.') if f.endswith('.csv')])
        with Vertical(id="browser_outer"):
            with Vertical(id="browser_panel"):
                yield Label(f"HEARCAL: {self.mode.upper()} PROFILE", id="browser_title")
                if self.mode == "save":
                    yield Input(placeholder="filename.csv", id="new_file_input")
                
                yield ListView(*[ListItem(Label(f)) for f in files], id="file_list")
                self.file_map = files
                
                with Horizontal(id="browser_buttons"):
                    yield Button("Cancel (Esc)", id="cancel", variant="error")
                    yield Button("Confirm (Enter)", id="confirm", variant="primary")

    def action_dismiss_screen(self) -> None:
        self.app.pop_screen()

    def action_submit(self) -> None:
        fn = self.get_selection()
        if not fn:
            return
        if not fn.endswith(".csv"):
            fn += ".csv"
            
        if self.mode == "save" and os.path.exists(fn):
            self.app.push_screen(OverwriteScreen(fn))
        else:
            self.post_message(FileSelected(fn, self.mode))
            self.action_dismiss_screen()

    def get_selection(self) -> str:
        new_val = self.query_one("#new_file_input").value.strip() if self.mode == "save" else ""
        list_view = self.query_one("#file_list")
        if list_view.index is not None and list_view.index < len(self.file_map):
            return new_val or self.file_map[list_view.index]
        return new_val

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.action_submit()
        else:
            self.action_dismiss_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_submit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_submit()

class VerificationScreen(Screen):
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Exit"),
        Binding("left", "prev_freq", "Prev"),
        Binding("right", "next_freq", "Next"),
        Binding("up", "gain_up", "+0.5dB"),
        Binding("down", "gain_down", "-0.5dB"),
        Binding("space", "play_audio", "Play"),
        Binding("p", "toggle_playback_mode", "Seq/Pulse"),
        Binding("r", "shuffle_freqs", "Shuffle"),
        Binding("a", "sort_ascending", "Ascending")
    ]

    def __init__(self, results):
        super().__init__()
        self.results = results
        self.freq_list = list(ISO_FREQS)
        self.v_idx = 0
        self.mode_sequence = True 

    def compose(self) -> ComposeResult:
        with Vertical(id="verify_container"):
            yield Label("VERIFICATION & REFINEMENT", variant="title")
            yield Static(
                "1. [L/R]: Navigates frequency list.\n"
                "2. [UP/DOWN]: Adjusts level +/-0.5dB.\n"
                "3. [P]: Toggle Playback (Anchor-Gap-Test vs. Level Adjusted Only).\n"
                "4. [R/A]: Shuffle or Sort list to re-evaluate perceptions.\n"
                "5. [SPACE]: Re-play current selection.",
                classes="instr", 
                markup=False
            )
            yield Label("", id="play_mode_label", classes="mode-indicator")
            yield Label("", id="v_freq_label")
            yield Label("", id="v_db_label", classes="mode-indicator")
            yield ProgressBar(total=len(ISO_FREQS), id="v_pbar", show_percentage=True)
            with Horizontal():
                yield Button("Exit (Esc)", id="exit_verify")

    def on_mount(self):
        self.update_v_ui()

    def update_v_ui(self):
        freq = self.freq_list[self.v_idx]
        db = self.results.get(freq, 0.0)
        mode_txt = "MODE: ANCHOR-GAP-TEST" if self.mode_sequence else "MODE: LEVEL ADJUSTED ONLY"
        
        self.query_one("#play_mode_label").update(mode_txt)
        self.query_one("#v_freq_label").update(
            f"Band {self.v_idx + 1}/{len(self.freq_list)}: [b]{int(freq)} Hz[/b]"
        )
        self.query_one("#v_db_label").update(f"Level: {db:+.1f} dB")
        self.query_one("#v_pbar").update(progress=self.v_idx + 1)

    def action_toggle_playback_mode(self):
        self.mode_sequence = not self.mode_sequence
        self.update_v_ui()
        self.action_play_audio()

    def action_shuffle_freqs(self):
        random.shuffle(self.freq_list)
        self.v_idx = 0
        self.notify("List Shuffled.")
        self.update_v_ui()
        self.action_play_audio()

    def action_sort_ascending(self):
        self.freq_list.sort()
        self.v_idx = 0
        self.notify("List Sorted: Ascending.")
        self.update_v_ui()
        self.action_play_audio()

    def action_prev_freq(self):
        self.v_idx = max(0, self.v_idx - 1)
        self.update_v_ui()
        self.action_play_audio()

    def action_next_freq(self):
        self.v_idx = min(len(self.freq_list) - 1, self.v_idx + 1)
        self.update_v_ui()
        self.action_play_audio()

    def action_gain_up(self):
        self.results[self.freq_list[self.v_idx]] += 0.5
        self.update_v_ui()
        self.action_play_audio()

    def action_gain_down(self):
        self.results[self.freq_list[self.v_idx]] -= 0.5
        self.update_v_ui()
        self.action_play_audio()

    def action_play_audio(self):
        freq = self.freq_list[self.v_idx]
        db = self.results.get(freq, 0.0)
        test_tone = self.app.generate_seamless_warble(freq, db, 1.2)
        
        if self.mode_sequence:
            ref = self.app.generate_seamless_warble(1000.0, 0.0, 1.2)
            silence = np.zeros(int(SAMPLE_RATE * 0.3), dtype=np.float32)
            self.app.audio_engine.play(np.concatenate([ref, silence, test_tone]), loop=False)
        else:
            # Level Adjusted Only mode: continuous looping
            self.app.audio_engine.play(test_tone, loop=True)

    def action_dismiss_screen(self):
        self.app.audio_engine.clear()
        self.dismiss()

    def on_button_pressed(self, event):
        self.app.audio_engine.clear()
        self.dismiss()

class AudioEngine:
    """Simple persistent audio stream to avoid device open/close crackling."""
    def __init__(self):
        self.stream = None
        self.current_audio = np.array([], dtype=np.float32)
        self.position = 0
        self.is_looping = False
        self.lock = threading.Lock()
    
    def callback(self, outdata, frames, time_info, status):
        with self.lock:
            if len(self.current_audio) == 0:
                outdata.fill(0)
                return
            
            # Get samples from current position
            remaining = len(self.current_audio) - self.position
            if remaining >= frames:
                # Simple case: enough samples available
                outdata[:] = self.current_audio[self.position:self.position + frames].reshape(-1, 1)
                self.position += frames
            elif self.is_looping:
                # Loop case: wrap around
                outdata[:remaining] = self.current_audio[self.position:].reshape(-1, 1)
                self.position = frames - remaining
                outdata[remaining:] = self.current_audio[:self.position].reshape(-1, 1)
            else:
                # End of non-looping audio
                outdata[:remaining] = self.current_audio[self.position:].reshape(-1, 1)
                outdata[remaining:].fill(0)
                self.position = len(self.current_audio)
    
    def start(self):
        """Open audio stream."""
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=self.callback,
                dtype=np.float32
            )
            self.stream.start()
    
    def stop(self):
        """Close audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def play(self, audio_data, loop=False):
        """Load new audio into buffer."""
        with self.lock:
            self.current_audio = audio_data.astype(np.float32)
            self.position = 0
            self.is_looping = loop
    
    def clear(self):
        """Clear audio buffer."""
        with self.lock:
            self.current_audio = np.array([], dtype=np.float32)
            self.position = 0
            self.is_looping = False

class HearCal(App):
    BINDINGS = [
        Binding("s", "request_save", "Save"), 
        Binding("l", "request_load", "Load"),
        Binding("t", "toggle_tone", "Toggle"), 
        Binding("space", "play_stop", "Play/Stop"),
        Binding("v", "enter_verify", "Verify"), 
        Binding("left", "prev_freq", "Prev"),
        Binding("right", "next_freq", "Next"), 
        Binding("up", "gain_up", "+0.5dB"),
        Binding("down", "gain_down", "-0.5dB"), 
        Binding("q", "quit", "Exit"),
    ]

    CSS = """
    Screen { align: center middle; }
    #main_container, #verify_container { 
        width: 85; height: auto; border: thick $primary; 
        padding: 1; background: $surface; 
    }
    Horizontal { height: auto; align: center middle; margin: 1 0; }
    #db_display { 
        text-align: center; color: $secondary; 
        text-style: bold; width: 100%; margin: 1 0; 
    }
    .mode-indicator { 
        text-align: center; background: $accent; 
        color: $text; padding: 0 1; margin-bottom: 1; 
    }
    .instr { 
        text-style: italic; color: $text-muted; 
        margin-bottom: 1; height: auto; 
    }
    #debug_terminal { 
        height: 8; border: solid $error; 
        background: black; color: #00FF00; margin-top: 1; 
    }
    #browser_outer { align: center middle; }
    #browser_panel { 
        width: 75; height: 80%; border: double $accent; 
        padding: 2; background: $panel; 
    }
    #file_list { height: 1fr; margin: 1 0; border: solid $primary; }
    #confirm_panel { 
        width: 50; height: auto; border: thick $error; 
        padding: 1; background: $surface; align: center middle; 
    }
    #confirm_title { text-style: bold; color: $error; margin-bottom: 1; }
    Button { margin: 0 1; }
    """

    def __init__(self):
        super().__init__()
        self.active_mode = "REF"
        self.current_idx = 0 
        self.results = {float(f): 0.0 for f in ISO_FREQS}
        self.is_playing = False
        self.audio_engine = AudioEngine()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main_container"):
            yield Label("HEARCAL: PERCEPTUAL CALIBRATION", variant="title")
            yield Static(
                "1. SPL: Set hardware volume at 1000Hz [Ref].\n"
                "2. MATCH: Toggle [T] for equal loudness.\n"
                "3. VERIFY: Press [V] for randomized or sequential passes.", 
                classes="instr", 
                markup=False
            )
            yield Label("MODE: REFERENCE (1000Hz)", id="mode_label", classes="mode-indicator")
            yield Label(id="freq_label")
            yield Static(id="db_display")
            with Horizontal():
                yield Button("AUDIO (Space)", variant="success", id="play_btn")
                yield Button("TOGGLE (T)", variant="primary", id="toggle_btn")
            yield ProgressBar(total=len(ISO_FREQS), id="pbar", show_percentage=True)
            yield RichLog(id="debug_terminal", highlight=True, markup=True)
        yield Footer()

    def update_ui(self):
        freq = ISO_FREQS[self.current_idx]
        db = self.results.get(freq, 0.0)
        mode_txt = "MODE: REFERENCE" if self.active_mode == "REF" else f"MODE: TESTING ({int(freq)}Hz)"
        
        self.query_one("#mode_label").update(mode_txt)
        self.query_one("#freq_label").update(
            f"Band {self.current_idx + 1}/{len(ISO_FREQS)}: [b]{int(freq)} Hz[/b]"
        )
        self.query_one("#db_display").update(f"{db:+.1f} dB")
        self.query_one("#pbar").update(progress=self.current_idx + 1)
        
        if self.is_playing:
            self.run_audio()

    def generate_seamless_warble(self, freq, gain_db, target_duration=2.0):
        lfo_samples = SAMPLE_RATE / LFO_RATE
        total_samples = int(max(1, round(target_duration * LFO_RATE)) * lfo_samples)
        t = np.linspace(0, total_samples / SAMPLE_RATE, total_samples, endpoint=False)
        phase = 2 * np.pi * (freq * t - (freq * LFO_DEPTH / (2 * np.pi * LFO_RATE)) * np.cos(2 * np.pi * LFO_RATE * t))
        return (np.sin(phase) * (10**(gain_db / 20.0)) * BASE_AMPLITUDE).astype(np.float32)

    def action_play_stop(self):
        self.is_playing = not self.is_playing
        if not self.is_playing:
            self.audio_engine.clear()
        else:
            self.run_audio()
        self.query_one("#play_btn").label = "STOP" if self.is_playing else "START"

    def run_audio(self):
        if not self.is_playing:
            return
        freq = 1000.0 if self.active_mode == "REF" else ISO_FREQS[self.current_idx]
        gain = 0.0 if self.active_mode == "REF" else self.results.get(freq, 0.0)
        self.audio_engine.play(self.generate_seamless_warble(freq, gain), loop=True)

    def action_toggle_tone(self):
        self.active_mode = "TEST" if self.active_mode == "REF" else "REF"
        self.update_ui()

    def action_enter_verify(self):
        if self.is_playing:
            self.action_play_stop()
        self.push_screen(VerificationScreen(self.results), callback=self._on_verify_return)
    
    def _on_verify_return(self, _):
        """Called when verification screen is dismissed."""
        self.update_ui()

    def on_file_selected(self, message: FileSelected) -> None:
        fn = message.filename
        if message.mode == "load":
            try:
                # Clear and reset all results to 0.0 before loading (preserves dict reference)
                self.results.clear()
                for f in ISO_FREQS:
                    self.results[float(f)] = 0.0
                
                with open(fn, 'r') as f:
                    for row in csv.DictReader(f):
                        f_in = float(row['frequency'])
                        db_in = float(row['raw'])
                        std_f = min(ISO_FREQS, key=lambda x: abs(x - f_in))
                        self.results[std_f] = db_in
                self.update_ui()
            except: 
                pass
        else:
            with open(fn, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(["frequency", "raw"])
                for freq in sorted(ISO_FREQS): 
                    w.writerow([f"{freq:.2f}", f"{self.results[freq]:.2f}"])
            self.notify(f"Saved: {fn}")
        
        # Dismiss file browser screen after operation completes
        for screen in self.screen_stack:
            if isinstance(screen, FileBrowserScreen):
                self.pop_screen()
                break

    def action_request_load(self): 
        self.push_screen(FileBrowserScreen(mode="load"))
    
    def action_request_save(self): 
        self.push_screen(FileBrowserScreen(mode="save"))

    def action_gain_up(self): 
        self.results[ISO_FREQS[self.current_idx]] += 0.5
        self.update_ui()

    def action_gain_down(self): 
        self.results[ISO_FREQS[self.current_idx]] -= 0.5
        self.update_ui()

    def action_next_freq(self): 
        self.current_idx = min(len(ISO_FREQS) - 1, self.current_idx + 1)
        self.update_ui()

    def action_prev_freq(self): 
        self.current_idx = max(0, self.current_idx - 1)
        self.update_ui()

    def on_mount(self): 
        self.audio_engine.start()
        self.update_ui()
    
    def on_unmount(self):
        self.audio_engine.stop()

if __name__ == "__main__": 
    HearCal().run()