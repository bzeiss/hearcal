import os
import sys
import re
import platform
import subprocess
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

# --- 2. TONEBOOSTERS XML MODEL ---

class TBBand:
    def __init__(self, idx, cmd: APOFilter, hue):
        self.idx = str(idx)
        self.attrs = {
            f"Visibl{self.idx}": "1",
            f"Enable{self.idx}": "1" if cmd.is_on else "0",
            f"Hue{self.idx}": str(hue),
            f"Freq{self.idx}": str(int(round(cmd.fc - 5))),
            f"Gain{self.idx}": str(int(round(3000 + (cmd.gain * 100)))),
            f"Q{self.idx}": str(int(round((cmd.q * 1000) - 20)))
        }
        if cmd.kind in ["LS", "LSC"]: self.attrs.update({f"Type{self.idx}": "1", f"Order{self.idx}": "1"})
        elif cmd.kind in ["HS", "HSC"]: self.attrs.update({f"Type{self.idx}": "2", f"Order{self.idx}": "1"})

class TBProgram:
    def __init__(self, name, preamp=0.0):
        self.name = name
        self.out_gain = str(int(round((preamp * 10) + 200)))
        self.bands = []
        self._hues = [52, 36, 0, 180, 260, 300]

    def add_filter(self, cmd: APOFilter):
        if len(self.bands) < 32:
            hue = self._hues[len(self.bands) % len(self._hues)]
            self.bands.append(TBBand(len(self.bands)+1, cmd, hue))

    def to_xml_string(self):
        tpb = ET.Element("tpb", manufacturerCode="1414483522", pluginCode="1412515152")
        attr = {"Name": self.name, "Category": "Presets", "OutGain": self.out_gain, "ScnIdx": str(len(self.bands))}
        for b in self.bands: attr.update(b.attrs)
        ET.SubElement(tpb, "Program", attr)
        return minidom.parseString(ET.tostring(tpb)).toprettyxml(indent="  ")

# --- 3. APPLICATION CONTROLLER ---

class ConverterApp:
    def __init__(self):
        self.target_dir = self._resolve_dir()
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_dir(self):
        os_name = platform.system()
        if os_name == "Windows": return Path(os.environ['APPDATA']) / "Toneboosters/TB Equalizer Pro_programs/User/Converted"
        if os_name == "Linux": return Path.home() / ".config/Toneboosters/TB Equalizer Pro_programs/User/Converted"
        self._dialog("macOS Path Error", "The correct preset path for macOS is unknown.", True); sys.exit()

    def _dialog(self, title, msg, is_err=False):
        root = tk.Tk(); root.withdraw()
        if is_err: messagebox.showerror(title, msg)
        else: messagebox.showinfo(title, msg)
        root.destroy()

    def _get_unique_dest(self, dest: Path):
        if not dest.exists(): return dest
        root = tk.Tk(); root.withdraw()
        new_name = simpledialog.askstring("File Conflict", f"Rename '{dest.name}':", initialvalue=dest.stem+"_new.xml")
        root.destroy()
        return self.target_dir / (new_name if new_name.endswith(".xml") else new_name + ".xml") if new_name else None

    def run(self):
        file_paths = [Path(arg) for arg in sys.argv[1:] if arg.lower().endswith(".txt")]
        if not file_paths: return

        success_count = 0
        error_log = []

        for p in file_paths:
            try:
                apo = APOModel(p)
                preamp_val = sum(c.db for c in apo.commands if isinstance(c, APOPreamp))
                prog = TBProgram(p.stem, preamp_val)
                for cmd in apo.commands:
                    if isinstance(cmd, APOFilter): prog.add_filter(cmd)
                
                dest = self._get_unique_dest(self.target_dir / f"{p.stem}.xml")
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