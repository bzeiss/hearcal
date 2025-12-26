import os
import pandas as pd
import numpy as np
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, ListItem, ListView
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.screen import Screen

# --- FINER FREQUENCY BANDS (Restored) ---
BANDS = {
    "Sub": (20, 60),
    "Bass": (60, 250),
    "Low-Mid": (250, 500),
    "Mid": (500, 2000),
    "High-Mid": (2000, 4000),
    "High": (4000, 10000),
    "Air": (10000, 20000)
}

class MultiFileBrowser(Screen):
    """Minimal browser to select multiple hearing profiles."""
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Exit"), 
        Binding("enter", "submit", "Confirm Selection"),
        Binding("space", "toggle_selection", "Toggle")
    ]

    def compose(self) -> ComposeResult:
        self.files = sorted([f for f in os.listdir('.') if f.endswith('.csv')])
        self.selected_indices = set()
        
        with Vertical(id="browser_panel"):
            yield Label("[b]HEARCAL SELECTOR[/b]", id="title")
            yield Label("Select at least 2 files to compare and average.", classes="instr")
            yield ListView(*[ListItem(Label(f"[ ] {f}")) for f in self.files], id="file_list")
            with Horizontal(id="browser_buttons"):
                yield Button("Cancel", id="cancel", variant="error")
                yield Button("Process Average", id="confirm", variant="primary")

    def action_toggle_selection(self) -> None:
        list_view = self.query_one(ListView)
        idx = list_view.index
        if idx is not None:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
                list_view.children[idx].query_one(Label).update(f"[ ] {self.files[idx]}")
            else:
                self.selected_indices.add(idx)
                list_view.children[idx].query_one(Label).update(f"[*] {self.files[idx]}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_toggle_selection()

    def action_submit(self) -> None:
        if len(self.selected_indices) < 2:
            self.app.notify("Select at least 2 files.", severity="error")
            return
        self.dismiss([self.files[i] for i in self.selected_indices])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm": self.action_submit()
        else: self.dismiss(None)

class HearCalAverager(App):
    """Standalone DIY tool to average and compare hearing test results."""
    CSS = """
    Screen { align: center middle; }
    #browser_panel { width: 70; height: 20; border: thick $primary; padding: 1; background: $surface; }
    #file_list { border: solid $accent; margin: 1 0; height: 1fr; }
    #title { text-align: center; }
    .instr { text-align: center; color: $text-muted; text-style: italic; margin-bottom: 1; }
    Horizontal { height: auto; align: center middle; }
    Button { margin: 0 1; }
    """

    def on_mount(self) -> None:
        self.handle_flow()

    @work
    async def handle_flow(self):
        files = await self.push_screen_wait(MultiFileBrowser())
        if files:
            self.exit(result=self.compare_and_average(files))
        else:
            self.exit()

    def compare_and_average(self, files: list[str]) -> str:
        # Load and aggregate data
        data_list = []
        for f in files:
            temp_df = pd.read_csv(f)
            temp_df['filename'] = f
            data_list.append(temp_df)
        
        combined = pd.concat(data_list)
        
        # Calculate Detailed Statistics per Frequency
        stats = combined.groupby('frequency')['raw'].agg(['mean', 'min', 'max', 'std', 'var']).reset_index()
        stats.rename(columns={'mean': 'avg', 'var': 'variance'}, inplace=True)
        stats['spread'] = stats['max'] - stats['min']
        
        # Output 1: Standard HearCal Profile
        avg_df = stats[['frequency', 'avg']].rename(columns={'avg': 'raw'})
        avg_df.to_csv("hearcal_avg.csv", index=False)
        
        # Output 2: Detailed Stats CSV
        stats.to_csv("hearcal_avg_details.csv", index=False)
        
        # Build Terminal Report
        report = []
        report.append("\n" + "="*75)
        report.append(" HEARCAL AVERAGER: FILE COMPARISON & AVERAGE")
        report.append("="*75)
        report.append(f"Source Files:    {', '.join(files)}")
        report.append(f"Main Average:    hearcal_avg.csv")
        report.append(f"Detailed Stats:  hearcal_avg_details.csv")
        report.append("-" * 75)
        
        # 1. Global Consistency Metrics
        avg_spread = stats['spread'].mean()
        max_spread_row = stats.loc[stats['spread'].idxmax()]
        
        report.append("[CONSISTENCY SUMMARY]")
        report.append(f"  Average Gap:     {avg_spread:.2f} dB (Typical variance across all bands)")
        report.append(f"  Largest Gap:     {max_spread_row['spread']:.2f} dB at {max_spread_row['frequency']} Hz")
        report.append("-" * 75)
        
        # 2. Detailed Band Comparison Table
        report.append(f"{'BAND':<12} | {'AVG VAL':>8} | {'MAX DIFF':>8} | {'VAR':>8} | {'STATUS'}")
        report.append("-" * 75)
        
        for name, (low, high) in BANDS.items():
            mask = (stats['frequency'] >= low) & (stats['frequency'] < high)
            band_data = stats.loc[mask]
            
            if not band_data.empty:
                b_val = band_data['avg'].mean()
                b_spread = band_data['spread'].max()
                b_var = band_data['variance'].mean()
                
                # Logic for status based on spread (difference between files)
                if b_spread < 2.0:   status = "Stable"
                elif b_spread < 5.0: status = "Variable"
                else:                status = "Unreliable"
                
                report.append(f"{name:<12} | {b_val:>8.1f} | {b_spread:>8.1f} | {b_var:>8.1f} | {status}")
            else:
                report.append(f"{name:<12} | No Data")
        
        # 3. Definitions
        report.append("-" * 75)
        report.append("METRIC EXPLANATIONS:")
        report.append("  AVG VAL:  The final average loudness offset used for your profile.")
        report.append("  MAX DIFF: The largest disagreement between your test runs in this band.")
        report.append("  VAR:      Statistical variance. High numbers mean tests were inconsistent.")
        report.append("  STATUS:   'Stable' means your test runs matched closely in this range.")
        report.append("-" * 75)
        
        # 4. DIY Sanity Check
        report.append("[SETUP RELIABILITY]")
        if avg_spread < 2.5:
            report.append("  Thumbs Up: Your measurements are very consistent.")
        elif avg_spread < 6.0:
            report.append("  Caution: Moderate variation detected. Check for noise or fit issues.")
        else:
            report.append("  Warning: Large differences between files. Results may be unreliable.")
        report.append("="*75 + "\n")
        
        return "\n".join(report)

if __name__ == "__main__":
    result = HearCalAverager().run()
    if result:
        print(result)

