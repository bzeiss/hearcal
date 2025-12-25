# HearCal: Perceptual Headphone Calibration

HearCal is a Python-based diagnostic and refinement tool designed to bridge the gap between objective acoustic targets and your personal hearing.

## 1. Introduction

The goal of HearCal is to create a **personalized hearing profile** (delta curve) that accounts for the specific characteristics of your ears and your headphones.

Standard headphone targets, like the Harman Target, are based on "standard" listeners with perfect hearing. As hearing sensitivity varies with age or noise exposure, your perception often deviates from these baselines. HearCal uses a two-phase process to identify these deviations:

* **Phase 1 (Calibration)**: Uses **Instantaneous A/B Switching** to find equal-loudness thresholds across 31 ISO frequency bands compared to a 1000Hz reference anchor.
* **Phase 2 (Verification)**: Employs a **Sequential Pulse methodology** (Anchor → Silence → Test) to reset the ear's automatic gain control and prevent your brain from "adapting" to the sound, which can skew results.

By combining your HearCal delta with an objective target, you create a monitoring environment optimized for your specific hearing.

---

## 2. Prerequisites

To implement the HearCal workflow, you will need:

* **Python 3.10+**: The core environment for the script.
* **PIP Packages**: `textual`, `numpy`, and `sounddevice`.
* **REW (Room EQ Wizard)**: Used for trace arithmetic and generating EQ filters.
* **Toneboosters Equalizer Pro**: Recommended for final EQ application. A converter from EqualizerAPO format to TB Equalizer Pro is provided in this repository.
* **Target Curve**: The **Harman Over-Ear 2018** (or preferred Oratory1990/AutoEQ target) in `.csv` or `.txt` format.

---

## 3. Installation

1. **Install Python**: Download from [python.org](https://www.python.org/).
2. **Install Dependencies**: Run the following in your terminal:
```bash
pip install textual numpy sounddevice

```


3. **Download HearCal**: Save `hearcal.py` to your local machine.

---

## 4. Usage

### Step 1: Run HearCal

Launch the application from your terminal:

```bash
python hearcal.py

```

1. **Reference Level**: Set hardware volume so the 1000Hz anchor is at a comfortable mixing level (ideally **85dB SPL** if using a meter).
2. **Calibration**: Use **[UP/DOWN]** to adjust the test tone until it matches the 1000Hz anchor in perceived loudness. Press **[T]** to toggle between them.
3. **Verification**: Press **[V]** for the refinement screen. Use the sequential pulses (auto-played on navigation) to "zero in" on the subjective weight of each band.
4. **Save**: Press **[S]** to save your `hearing_profile.csv`.

### Step 2: Integrate in REW

1. Import your **Harman Target** and **HearCal Delta** CSVs into REW.
2. Go to the **Controls** (gear icon) -> **Arithmetic**.
3. Select **Harman Target (A)** + **HearCal Delta (B)** and click **Generate**.

### Step 3: Create Equalizer Configuration

1. In the REW **EQ Window**, set your headphone measurement as the "Measurement" and your new combined curve as the "Target".
2. Click **Match Response to Target** to generate parametric EQ filters.
3. Export the filters in **EqualizerAPO** format.
4. Use the provided converter in this repo to import your filters into **Toneboosters Equalizer Pro**.
5. **Important**: Set a **Global Negative Pre-amp** in Toneboosters equal to your highest boost to avoid digital clipping.


