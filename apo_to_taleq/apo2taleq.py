import os
import sys
import re
import platform
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom
import tkinter as tk
from tkinter import simpledialog, messagebox

# --- 1. APO DOMAIN MODEL (Full Specification) ---

class APOCommand:
    def __init__(self, device="all", channel="all", stage="post-mix"):
        self.device = device
        self.channel = channel
        self.stage = stage

class APOPreamp(APOCommand):
    def __init__(self, db, **ctx):
        super().__init__(**ctx)
        self.db = float(db)

class APOFilter(APOCommand):
    def __init__(self, kind, fc, gain=0.0, q=0.707, is_on=True, **ctx):
        super().__init__(**ctx)
        self.kind = kind.upper()
        self.fc = float(fc)
        self.gain = float(gain)
        self.q = float(q)
        self.is_on = is_on

class APOGraphicEQ(APOCommand):
    def __init__(self, points, **ctx):
        super().__init__(**ctx)
        self.points = points # List of (freq, gain) tuples

class APOModel:
    """Recursively parses APO files and maintains state contexts."""
    def __init__(self, main_file_path: Path):
        self.commands = []
        self.root_path = main_file_path.parent
        self._parse_file(main_file_path)

    def _parse_file(self, path: Path, device="all", channel="all", stage="post-mix"):
        if not path.exists(): return

        patterns = {
            'preamp': re.compile(r"^Preamp:\s*([-\d.]+)\s*dB", re.I),
            'filter': re.compile(r"^Filter(?:\s+\d+)?:\s*(ON|OFF)\s+([A-Z0-9]+)\s+Fc\s+([\d.]+)\s+Hz(?:(?:\s+Gain\s+([-\d.]+)\s+dB)?(?:\s+(?:Q|BW Oct)\s+([\d.]+))?)?", re.I),
            'device': re.compile(r"^Device:\s*(.*)", re.I),
            'channel': re.compile(r"^Channel:\s*(.*)", re.I),
            'stage': re.compile(r"^Stage:\s*(pre-mix|post-mix|capture)", re.I),
            'include': re.compile(r"^Include:\s*(.*)", re.I),
            'graphic': re.compile(r"^GraphicEQ:\s*(.*)", re.I)
        }

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue

                if m := patterns['device'].match(line): device = m.group(1)
                elif m := patterns['channel'].match(line): channel = m.group(1)
                elif m := patterns['stage'].match(line): stage = m.group(1)
                elif m := patterns['include'].match(line):
                    self._parse_file(self.root_path / m.group(1).strip(), device, channel, stage)
                elif m := patterns['preamp'].match(line):
                    self.commands.append(APOPreamp(m.group(1), device=device, channel=channel, stage=stage))
                elif m := patterns['filter'].match(line):
                    on_off, kind, fc, gain, q = m.groups()
                    self.commands.append(APOFilter(kind, fc, gain or 0, q or 0.707, on_off.upper()=="ON", device=device, channel=channel, stage=stage))
                elif m := patterns['graphic'].match(line):
                    pairs = [p.strip().split(' ') for p in m.group(1).split(';') if p.strip()]
                    self.commands.append(APOGraphicEQ([(float(p[0]), float(p[1])) for p in pairs if len(p)==2], device=device, channel=channel, stage=stage))

# --- 2. TAL-EQ XML MODEL ---

# TAL-EQ filter type codes (derived from preset examples)
# type 0 = Bell/Peak
# type 1 = Low Shelf
# type 2 = High Cut (Low Pass)
# type 3 = High Shelf
# type 4 = Low Cut (High Pass)

TAL_MAX_BANDS = 16

# EqualizerAPO filter kind → TAL type code
TAL_TYPE_MAP = {
    "PK": 0, "PEQ": 0, "BELL": 0,
    "LS": 1, "LSC": 1, "LSQ": 1,
    "HS": 3, "HSC": 3, "HSQ": 3,
    "LP": 2, "LPQ": 2,
    "HP": 4, "HPQ": 4,
}

class TALBand:
    def __init__(self, cmd: APOFilter):
        self.tal_type = TAL_TYPE_MAP.get(cmd.kind, 0)
        self.q = cmd.q
        self.gain = cmd.gain
        self.frequency = cmd.fc
        self.on = cmd.is_on

    def to_xml_attrs(self):
        return {
            "type": str(self.tal_type),
            "q": str(self.q),
            "gain": str(self.gain),
            "frequency": str(self.frequency),
            "dboctave": "0",
            "mode": "0",
            "on": "1" if self.on else "0",
            "enabled": "1" if self.on else "0",
            "DynamicEnabled": "0",
            "DynamicAutoThreshold": "1",
            "DynamicSideChain": "0",
            "DynamicRange": "-3.0",
            "DynamicThreshold": "-20.0",
            "DynamicAttack": "0.02500000037252903",
            "DynamicRelease": "0.1000000014901161",
        }

class TALProgram:
    def __init__(self, name, preamp=0.0):
        self.name = name
        self.preamp = preamp
        self.bands = []

    def add_filter(self, cmd: APOFilter):
        if len(self.bands) < TAL_MAX_BANDS:
            self.bands.append(TALBand(cmd))

    def add_graphic_eq(self, cmd: APOGraphicEQ):
        """Convert GraphicEQ points to peaking bands, fitting within the band limit."""
        # Filter out near-zero gain points, keep neighbors for accuracy
        points = cmd.points
        non_zero = {i for i, (_, g) in enumerate(points) if abs(g) > 0.01}
        keep = set()
        for i in non_zero:
            keep.add(i)
            if i > 0: keep.add(i - 1)
            if i < len(points) - 1: keep.add(i + 1)
        filtered = [points[i] for i in sorted(keep)]
        if not filtered: return

        available = TAL_MAX_BANDS - len(self.bands)
        if available <= 0: return
        if len(filtered) > available:
            filtered.sort(key=lambda p: abs(p[1]), reverse=True)
            filtered = filtered[:available]
            filtered.sort(key=lambda p: p[0])

        for freq, gain in filtered:
            fake_cmd = APOFilter("PK", freq, gain, 1.5, True)
            self.add_filter(fake_cmd)

    def _preamp_to_volume(self):
        """TAL volume: 0.5 = 0dB (unity). Linear map ±20dB to 0..1."""
        volume = 0.5 + self.preamp / 40.0
        return max(0.0, min(1.0, volume))

    def to_xml_string(self):
        max_gain = max((abs(b.gain) for b in self.bands), default=0.0)
        visible_db_range = max(12.7597541809082, max_gain * 1.5)
        volume = self._preamp_to_volume()

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('')
        lines.append('<tal curprogram="0" version="3" mainPosX="0">')

        prog_attrs = [
            ('bypass', '0.0'), ('volume', str(volume)), ('pan', '0.5'),
            ('phase', '0.0'), ('middleSideVolumeEnabled', '0.0'),
            ('middleVolume', '0.5'), ('sideVolume', '0.5'), ('gainScale', '0.5'),
            ('showspectrum', '1.0'), ('selectedband', '0.0'),
            ('midilearn', '0.0'), ('midiclear', '0.0'), ('midilock', '0.0'),
            ('midieditselected', '0.0'),
            ('Reserve00', '0.0'), ('Reserve01', '0.0'), ('Reserve02', '0.0'),
            ('Reserve03', '0.0'), ('Reserve04', '0.0'), ('Reserve05', '0.0'),
            ('Reserve06', '0.0'), ('Reserve07', '0.0'),
            ('programname', self.name),
        ]

        prog_line = '  <program'
        for key, val in prog_attrs:
            prog_line += f' {key}="{val}"'
        prog_line += '>'
        lines.append(prog_line)

        lines.append('    <midimap/>')
        lines.append(f'    <parametriceq visibledecibelrange="{visible_db_range}">')

        for band in self.bands:
            attrs = band.to_xml_attrs()
            eq_line = '      <eq'
            for key, val in attrs.items():
                eq_line += f' {key}="{val}"'
            eq_line += '/>'
            lines.append(eq_line)

        for _ in range(TAL_MAX_BANDS - len(self.bands)):
            lines.append('      <eq/>')

        lines.append('    </parametriceq>')
        lines.append('  </program>')
        lines.append('</tal>')
        lines.append('')

        return '\n'.join(lines)

# --- 3. APPLICATION CONTROLLER ---

class ConverterApp:
    def __init__(self):
        self.target_dir = self._resolve_dir()
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_dir(self):
        os_name = platform.system()
        if os_name == "Windows": return Path(os.environ['APPDATA']) / "ToguAudioLine/TAL-EQ/presets/Converted"
        if os_name == "Linux": return Path.home() / ".toguaudioline/TAL-EQ/presets/Converted"
        if os_name == "Darwin": return Path.home() / "Library/Application Support/ToguAudioLine/TAL-EQ/presets/Converted"
        self._dialog("Unknown OS", f"Unsupported operating system: {os_name}", True); sys.exit()

    def _dialog(self, title, msg, is_err=False):
        root = tk.Tk(); root.withdraw()
        if is_err: messagebox.showerror(title, msg)
        else: messagebox.showinfo(title, msg)
        root.destroy()

    def _get_unique_dest(self, dest: Path):
        if not dest.exists(): return dest
        root = tk.Tk(); root.withdraw()
        new_name = simpledialog.askstring("File Conflict", f"Rename '{dest.name}':", initialvalue=dest.stem+"_new.taleq")
        root.destroy()
        return self.target_dir / (new_name if new_name.endswith(".taleq") else new_name + ".taleq") if new_name else None

    def run(self):
        file_paths = [Path(arg) for arg in sys.argv[1:] if arg.lower().endswith(".txt")]
        if not file_paths: return

        success_count = 0
        error_log = []

        for p in file_paths:
            try:
                apo = APOModel(p)
                preamp_val = sum(c.db for c in apo.commands if isinstance(c, APOPreamp))
                prog = TALProgram(p.stem, preamp_val)
                for cmd in apo.commands:
                    if isinstance(cmd, APOFilter): prog.add_filter(cmd)
                    elif isinstance(cmd, APOGraphicEQ): prog.add_graphic_eq(cmd)

                dest = self._get_unique_dest(self.target_dir / f"{p.stem}.taleq")
                if dest:
                    dest.write_text(prog.to_xml_string(), encoding='utf-8')
                    success_count += 1
            except Exception as e:
                error_log.append(f"{p.name}: {str(e)}")

        # Final Summary Dialog
        summary = f"Converted {success_count} file(s) successfully."
        if error_log:
            summary += "\n\nErrors:\n" + "\n".join(error_log)
            self._dialog("Conversion Finished", summary, True)
        else:
            self._dialog("Conversion Finished", summary)

        # Open folder on Windows
        if platform.system() == "Windows": os.startfile(self.target_dir)

if __name__ == "__main__":
    ConverterApp().run()