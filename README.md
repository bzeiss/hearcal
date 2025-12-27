# HearCal: Perceptual Subjective DIY Loudness Matching for Headphone Mixing

HearCal is a Python-based tool built to experimentally identify possible gaps between objective acoustic targets and your individual hearing by DIY loudness matching. It allows you to create a personalized calibration profile for mixing music on headphones that may (or may not) help to personalize the mixing experience to your hearing (caveats below).

---

## 1. Introduction

The goal of HearCal is to generate a **personalized hearing profile** (a "delta curve"). The delta is a subjective equal‑loudness matching curve at one playback level, not an audiogram. This curve accounts for the unique characteristics of your ears and your specific headphones. When combined with industry-standard targets—such as the **Harman Over-Ear 2018** curve, it creates an equalization profile tailored specifically to how you perceive sound. It’s specific to your headphone fit at the time of testing.

Standard headphone targets are based on "standard" listeners with healthy hearing. However, because sensitivity varies with age, noise exposure, and physiology, your perception often deviates from these averages. HearCal identifies these deviations through a two-phase process:

* **Phase 1 (Calibration)**: Uses **Instantaneous A/B Switching** to find equal-loudness thresholds across 31 ISO frequency bands, compared against a 1000Hz reference anchor.
* **Phase 2 (Verification)**: Employs a **Sequential Pulse methodology** (Anchor → Silence → Test). This helps reduce short-term loudness adaptation and prevents the brain from "adapting" to the sound, which can otherwise skew results. This phase includes toggle modes to shuffle frequencies or test in ascending order to ensure a truly "flat" subjective response.

The tool is designed to give an indication of where perceptual deviations might exist when the default target curves consistently lead to bad mix translation. I suggest to start with the default target curves first before using this tool. It's purely a DIY approach and does not replace an audiogram from an audiologist in a controlled environment. The pure sine test tones do not represent actual music and the frequency spectrum of music. It might just as well lead to curves that overcompensate and make things worse. Please be aware of this fact.

   > **⚠️ Recommended Workflow for Mixing**  
   > Start with your headphone's Harman EQ *without* personal hearing correction. Only try to use HearCal if you experience consistent translation problems. Then A/B test to verify the correction actually helps your mixes.

*Note on the 1 kHz Reference:* This tool assumes your hearing at 1 kHz is "neutral" relative to adjacent frequencies. If you have a significant peak or dip at exactly 1 kHz, your entire curve will be tilted. A future version may include anchor verification (see Ideas section).

Be aware that real hearing loss cannot be compensated with this tool.

HearCal is a cross-platform command-line application with a Terminal User Interface (TUI). It is designed to be lightweight, easy to adapt, and low-maintenance. While it requires basic technical knowledge to run, the calibration process itself is intuitive.

<img width="836" height="673" alt="image" src="https://github.com/user-attachments/assets/4af636a1-5fda-4d48-86e0-2a7a867aa580" />
<img width="828" height="668" alt="image" src="https://github.com/user-attachments/assets/77499283-44fc-4111-80ba-1fba7ceed764" />

### Project Status & Disclaimers

* Experimental Tool: This project is a functional implementation of psychoacoustic principles, but I am not an acoustics professional or physicist. It is a "community-driven" attempt to add another tool in the toolbox that may help to improve headphone monitoring accuracy.
* Contributions: If you have expertise in psychoacoustics or Python and see room for improvement, merge requests are welcome! The goal is to keep the tool effective yet simple and maintainable.
* AI Integration: Parts of this documentation and code were developed or refined with the assistance of AI to ensure clarity and provide a starting point for development.

### When HearCal Is NOT Appropriate
* If you suspect significant hearing loss (see an audiologist first)
* If your headphones have severe frequency response problems (>10 dB deviations)—fix the hardware first
* If your mixes translate well already—don't fix what isn't broken
* If you cannot maintain a consistent headphone fit between sessions

### Credits

This general EQ workflow was inspired by the research and methods shared by [MixphonesUK](https://www.youtube.com/@MixPhonesUK). The correction workflow is inspired by a well known closed headphone system for mixing.

---

## 2. Prerequisites

To implement the HearCal workflow, you will need:

* **SPL Meter:** Capable of **A-weighting** and **C-weighting** (a smartphone app can work, though a dedicated meter is more accurate).
* **Headphone Amplifier:** A clean, high-quality amp is recommended to ensure your headphones have sufficient headroom.
* **Python 3.10+**: The core environment for the script.
* **PIP Packages**: `textual`, `numpy`, `pandas`, `scipy` and `sounddevice`.
* **REW (Room EQ Wizard)**: Used for arithmetic.
* **Target Curve:** The Harman Over-Ear 2018 (or your preferred AutoEQ target) in .csv or .txt format.
* **Equalizer Software**: **[Toneboosters Equalizer Pro](https://www.toneboosters.com/tb_equalizer_pro.html)**: Recommended for cross-platform support. A converter from EqualizerAPO to TB format is included in this repo. *Alternatives*: Apulsoft **[ApQualizer2](https://www.apulsoft.ch/apqualizr2/)** supports import of EqualizerAPO equalizer profiles directly. Fabfilter **Pro-Q3/4** requires the multiplication of the Q factor by 1.41!

---

## 3. Installation

1. **Install Python**: Download from [python.org](https://www.python.org/) for Windows. On macOS, Python 3 may need to be installed separately—check by running `python3 --version` in Terminal, or install via python.org or Homebrew. You may have to look this up. On Linux, install Python with the package manager of your distribution.
2. **Install Dependencies**: Open your terminal or command prompt and run:
```bash
pip install textual numpy pandas scipy sounddevice
```

3. **Download HearCal**: Clone this repository or download the hearcal.py script to a dedicated folder on your machine.

---

## 4. Methodologies for Applying Calibration Deltas

Before we dive into how to use HearCal, we must decide which correction approach we want to take as it may affect how we play back audio through HearCal. Once you have derived your personalized delta curves using HearCal, the critical task is integrating this data into your monitoring chain. The following methodologies outline the different paths you can take. We must acknowledge that none of these approaches perfectly separate "your hearing" from "your headphones" and "your fit." Each method reduces certain sources of error while accepting others. The goal is useful approximation, not clinical precision.

### Approach 1: The "Direct" Method

In this approach, you run HearCal on the raw, unequalized output of your headphones. 

* **The Logic:** This treats the entire monitoring chain as one single system. The resulting curve represents the "total system error"—the combined frequency response deviations of the headphone drivers, the physical enclosure, and your unique hearing physiology all baked into one delta.
* **The Risk of Double-Correction:** The biggest danger here is "Double Compensation." If you later apply a standard calibration preset using a headphone measurement (be it generalized or specific for your headphone), you will be fixing the same hardware flaws twice. 
* **The Problem with Raw Resonances:** Even though HearCal uses noise and warble tones to help you hear through peaks, running a test on uncorrected headphones means you are often pushing the driver into its non-linear range. If your headphones have a massive +8dB resonance at 6kHz, your brain has to work much harder to judge loudness accurately in that area. This can lead to a "tilted" delta curve that is more about fighting the headphone's character than mapping your actual hearing.

### Approach 2: The "Neutralized" Method

This method attempts to isolate your unique hearing profile by first "zeroing out" the hardware variables of the headphone.

* **The Logic:** You apply a baseline EQ to make the headphones "flat" (Diffuse Field) before starting the HearCal test. It is vital that this baseline is "rig-specific." If the measurements for your headphones were taken on a **GRAS 43AG/45BC** (the industry standard for years), you must use a GRAS Diffuse Field target. If they were taken on the newer **B&K 5128**, use that specific 5128 diffuse field target. These rigs simulate the human ear differently, and mixing them up will introduce mathematical errors.
* **The Benefit:** By neutralizing the headphones first, you ensure that HearCal is only measuring the **Transfer Function Delta**—the difference between a "standardized average ear" and your actual anatomy. This minimizes the influence of manufacturing tolerances and prevents the headphones' specific "flavor" from biasing your loudness matching.

### Approach 3: The "Hybrid Integration" Method (Recommended)

To achieve a better level of monitoring transparency, we use a multi-stage process that accounts for both hardware variance and the natural "mood swings" of human hearing.

1.  **Baseline Normalization:** Apply a rig-accurate Diffuse Field (DF) correction first. This "levels the playing field" by removing the headphone's built-in peaks and dips.
2.  **Psychophysical Isolation:** Run the HearCal test *through* this correction. You are now mapping your personal **Equal-Loudness Contour** against a neutral acoustic reference, rather than fighting the headphone's character.
3.  **Statistical Averaging:** Human perception is volatile, influenced by blood pressure, caffeine, and fatigue. Perform at least three sessions at different times of the day (e.g., morning, mid-day, and after a break). Use the provided averaging tool to derive a "Master Delta," which significantly reduces the margin of error.
4.  **Verification (The Sanity Check):** Once your combined curve is active, listen to **correlated pink noise.** It should sound like a smooth, colorless "waterfall." If you hear distinct "whistling" (resonant peaks) or "hollow" sounds (phase cancellations), your EQ filters may be too sharp or you have over-corrected a physical limitation.

### Implementation Fundamentals

* **Temporal Stability:** Never trust a single measurement session. Because our ears change throughout the day, a single "snapshot" can lead to a mix that sounds great at 10 PM but thin and harsh at 10 AM. Averaging is your best defense against this.
* **Filter Topology:** Your personal hearing profile should generally be applied with **low-Q (broad) filters.** Human hearing response doesn't typically have razor-sharp notches. Using "surgical" EQ for your personal delta can cause phase smearing and "ringing," which destroys the transient detail you need for mixing drums and percussion. Stick to **Minimum-Phase filters**. While Linear-Phase filters keep the phase "straight," they introduce pre-ringing, which smears the transients of your drums. Minimum-phase filters keep the ringing after the hit (where it is masked by the sound), preserving the "snap" of your mix.

---

## 5. Usage

### Step 1: Adjust your headphones to the calibration loudness

Perceived loudness is not consistent across all frequencies at all volume levels. This phenomenon is described by the **Fletcher-Munson curves** (and the modern ISO 226 standard). What is important: there is a theoretical "sweet spot" level for mixing where our hearing is most linear, meaning frequency-dependent adjustments are less drastic than at others. 

The ideal level, according to this often cited work, for mixing with the most balanced perception of all frequencies—while remaining safe and bearable—is generally considered to be **83 dB to 85 dB SPL** as a room calibration convention. To my knowledge, there is no universal standard like this for headphones currently. So these values may or may not apply.

#### Why 83-85 dB?
Human hearing is naturally non-linear. At low volumes (around 40–60 dB), your ears are much less sensitive to low and high frequencies, causing the midrange (especially 3–4 kHz) to sound disproportionately loud. As volume increases, these curves "flatten out," allowing you to perceive the bass and treble more accurately in relation to the mids.

* **The "Flattest" Level:** The curves continue to flatten as volume increases toward the threshold of pain (120+ dB). However, mixing at 100+ dB is not bearable for more than a few minutes and will cause rapid ear fatigue and permanent hearing damage.
* **The Industry Standard:** The 83-85 dB SPL figure is a recognized standard for cinema and large professional studios. At this level, the frequency response is flat enough to make accurate EQ decisions without endangering your hearing.

#### Practical Considerations for "Bearability"
While 83-85 dB is the theoretical sweet spot for room calibration, it can be fatiguing over a long 8-hour session. Many engineers follow these practical guidelines:

* **Small Rooms/Headphones:** Due to ear fatigue, many professionals prefer monitoring at **76 dB to 80 dB SPL** for the bulk of a session.
* **The "Check" Method:** It is common practice to do the majority of the work at a moderate level (75–80 dB) and then turn the volume up to **85 dB** specifically for "checking" the low-end and high-end balance before turning it back down. Also bear in mind that some headphones may show more clarity and bass punch at higher levels 80-85 dB. It's unclear whether there is real scientific work on this.

The most important point is: choose one SPL loudness and calibrate to the loudness you mix at. If you mix at different levels, like 76 to 80 dB for long session and 85 dB for checking, you should likely perform the test multiple times at exactly these differing levels as the test assumes one specific loudness and adjusts to it.

#### Headphone Calibration with an SPL Meter
To achieve the most accurate results based on the Fletcher-Munson principles, you should set your SPL meter to **A-weighting** or **C-weighting** and a **Slow** response time. Be aware that the approach shown below will not yield exact results and may easily be off by a few dBs.

**NOTE**: HearCal includes a built-in calibration screen (press **`[C]`**) where you can select from four standard reference levels:
* **-18 dBFS RMS (L/R AVG)**: EBU R128, Common Home Studio
* **-20 dBFS RMS (L/R AVG)**: K-20, ATSC A/85, SMPTE RP 200
* **-14 dBFS RMS (L/R AVG)**: K-14
* **-12 dBFS RMS**: K-12

Use the calibration screen to play pink, white, or brown noise at your selected reference level and adjust your hardware volume to match your target SPL (e.g., 79-85 dB). The selected reference level will be used globally for all tone generation during testing. 

While C-weighting is often used for room calibration, **A-weighting** is sometimes recommended by experienced mixers here for a specific reason:
* **Sub-bass filtering:** Sub-bass produces a massive amount of physical energy that registers high on a meter, but for many people, it is much less "present" in their actual hearing than the mids and highs. 
* **Focusing the Measurement:** By using A-weighting (which rolls off the extreme lows), you effectively filter out that sub-bass energy from the measurement. This ensures you are calibrating the loudness based on the frequencies where your hearing is most sensitive, preventing the sub-bass from "tricking" the meter into thinking the volume is louder than it feels.

C-weighting may be used if you prefer aligning physical energy rather than perceptual loudness, but consistency is more important than choice. The jury is still out on this.

**Calibration Procedure:**
1.  **Launch HearCal:** Start the application and press **`[C]`** to enter the SPL calibration screen.
2.  **Select Reference Level:** Use **`[LEFT/RIGHT]`** to select the left column and **`[UP/DOWN]`** to choose your preferred reference level (e.g., -18 dBFS RMS for EBU R128). 
3.  **Select Noise Type:** Use **`[LEFT/RIGHT]`** to switch to the right column and **`[UP/DOWN]`** to choose white, pink, or brown noise.
4.  **Set Meter:** Configure your SPL meter to your chosen weighting (**A** or **C**) and **Slow** response.
5.  **Target:** Position your SPL meter against the headphone driver and adjust your hardware volume until you reach your target level (**79–85 dB**).
6.  **Hardware Marker:** Put a physical marker on your headphone amp volume knob. **This is now your reference level for the entire calibration.**
7.  **Exit:** Press **`[ESC]`** to return to the main screen. The selected reference level will be used for all tone generation.

You now have calibrated your headphones to your target SPL. The selected reference level determines the RMS amplitude of all test tones during the calibration process. Make sure to use this same SPL target (e.g., 85 dB) when mixing outside of HearCal. This hardware volume setting should be used consistently for all your mixing work.

### Step 2: Run HearCal

Launch the application from your terminal:

```bash
python hearcal.py
```
#### Phase 1: Calibration (A/B Comparison)

The objective of this phase is to establish a baseline by matching the perceived volume of various frequencies to a constant 1000Hz anchor. 31 ISO bands are used as a compromise between perceptual resolution, calibration time, and listener fatigue.

If you follow Approach 1, you don't need to do anything beforehand. For Approach 2-3, you'll need to make sure you equalize your headphones towards the correct diffuse field target curve of the measurement rig of your headphone measurement first and then playback the HearCal audio through it. 

1. **Reference Level**: Ensure your hardware is set to your marked calibration level (e.g., **85dB SPL**).
2. **Start Audio**: Press **`[SPACE]`** to begin generating sound.
3. **Toggle Mode [T]**: Press **`[T]`** to switch between the **Reference Tone** (1000Hz, which never changes volume) and the **Test Tone** (the frequency you are currently adjusting).
4. **Adjust Volume**: Use the **`[UP/DOWN]`** cursor keys to change the level of the test tone until it sounds exactly as loud as the 1000Hz reference.
5. **Navigate Bands**: Use **`[LEFT/RIGHT]`** cursor keys to move to the next frequency band. Perform this adjustment for all 31 ISO bands.

You can adjust the tone between sine/band-passed noise by pressing **`[F1]`**.

**Important: Respect the Physical Limits of your Hardware**

1. **Avoid "Ghost Chasing":** Many professional headphones (e.g., Sennheiser HD6XX series) have a natural low-end roll-off. If you cannot hear a sub-bass frequency clearly, **do not attempt to force it** by applying massive gains. Limit your adjustments to a maximum of **±6 dB**. If a frequency is still inaudible at +6 dB, leave it at 0 dB (no correction) to avoid damaging your drivers or your hearing.
2. **Distortion is a Hard Ceiling:** If a test tone begins to sound "grainy," "buzzing," or changes in character (timbre) as you increase the level, you have hit the driver’s **Total Harmonic Distortion (THD)** limit. Any EQ correction beyond this point will degrade your audio quality rather than improve it.
3. **Know your Tool:** If your headphone's technical specifications show a steep drop-off at a certain frequency, accept that as a "blind spot." It is better to have a known roll-off than a distorted, phase-smeared correction.
4. **Document your Constraints:** Make detailed notes of your decisions (e.g., "At 30 Hz, tone was inaudible even at +6 dB; correction left at 0 dB"). You will need these notes when you repeat the tests in the future to ensure that your calibration delta remains consistent and is not influenced by varying "guesses" in these blind spots.

#### Phase 2: Verification (The "Reality Check")

Phase 1 establishes an initial estimate. Phase 2 is where perceptual bias is actively challenged, and results should not be considered reliable unless they hold up under shuffle and level-adjusted testing.

Press **`[V]`** to enter the refinement screen. This phase uses a more advanced methodology to eliminate "loudness adaptation"—the phenomenon where your brain adjusts to a sound, making it seem quieter than it actually is.

* **Sequential Pulse (Anchor → Gap → Test)**: By default, moving to a frequency in this mode plays the 1000Hz anchor, followed by a one-second silence, and then the test tone.
* If the second tone sounds louder than the first, press **`[DOWN]`**.
* If the second tone sounds quieter, press **`[UP]`**.

* **Level Adjusted Only Mode [P]**: Press **`[P]`** to disable the anchor and play only the level-adjusted pulse of the current frequency. This helps you hear how a frequency sits in isolation. In this mode, step through the frequency bands by pressing **`[LEFT]`** and **`[RIGHT]`** and compare whether they are the perceived same loudness next to each other. If not, adjust them.
* **Shuffle Mode [R]**: Press **`[R]`** to randomize the order of the frequency bands. This is the most critical step; it prevents your brain from "expecting" the next sound and forces an honest comparison between unrelated frequencies (e.g., comparing 60Hz directly after 8kHz).
* **Ascending Mode [A]**: Press **`[A]`** to restore the standard frequency order for a final sweep to ensure the loudness feels smooth and linear from bottom to top.

It is possibly a good idea to use the ascending mode in the end, by starting at 1000Hz and going to the left, and then again starting at 1000Hz going to the right. That way, the final pass verifies the loudness of the neighboring frequencies from the reference point. In my (so far short) experience, the shuffled loudness comparisons when the frequency jumps between the frequencies are high, are hard to judge.

#### Phase 3: Save and Exit

Once you are confident that every frequency band is perceived at an equal loudness:

1. Press **`[S]`** to save your `hearing_profile.csv`.
2. Press **`[ESC]`** to return to the main menu.

*Note: You do not need to finish the calibration in one sitting. You can press **`[L]`** at any time to load your last saved state and continue refining your profile later.*

### Step 3: Integrate the Delta Curves

The curve saved by HearCal can be loaded as a measurement in [REW (Room EQ Wizard)](https://www.roomeqwizard.com/). This process allows us to combine your personal hearing delta with objective headphone measurements and target curves.

If we follow Approach 1, we possibly have double compensations. For Approaches 2-3, if we have played back the audio in a "neutralized" way, the delta is (hopefully) closer to the actual listener delta. In any case, the integration of the curves in REW is the same.

1. **Import Data**: Open REW (instructions based on V5.40 Beta 111). Go to **File -> Import -> Import Frequency Response** and load your three core CSV files:
   * **HearCal Delta**: The file you just saved from the HearCal app.
   * **Target Curve**: For over-ear headphones and mixing, the **Harman Over-Ear 2018** is recommended. You can find these at the [AutoEQ git repo](https://github.com/jaakkopasanen/AutoEq/tree/master/targets).
   * **Headphone Measurement**: Import a measurement for your specific headphone model from a trusted source, such as [oratory1990](https://github.com/jaakkopasanen/AutoEq/tree/master/results/oratory1990). Note that getting an external measurement is pretty debatable and doubts about this are very reasonable. External measurements can easily be wrong. Ideally, you have the measurement of your individual headphone.
  
   Your REW main window should now look like this:
   <img width="1299" height="661" alt="image" src="https://github.com/user-attachments/assets/5afd89da-990f-4439-b284-df8af6e13384" />

2. **Generate the Corrected Target**: We now add your hearing correction delta to the industry target curve. 
   * Click the **"Arithmetic"** button in the All SPL tab.
   * For **A**, select your target curve (e.g., Harman Over-Ear 2018).
   * For **B**, select your HearCal delta curve.
   * Select the **"A + B"** operation in the logarithmic domain and hit **"Generate"**.

   <img width="980" height="197" alt="image" src="https://github.com/user-attachments/assets/a69a7290-bf8f-4d18-b856-5bb17842a261" />
   <img width="341" height="308" alt="image" src="https://github.com/user-attachments/assets/4487277e-bc29-4d18-9879-7f4f9c1bd611" />
   
   The resulting curve is a *hypothesis* for a personalized target.
   
   Important:
   - The HearCal delta is tied to *this listener + this headphone + this fit/seal*, at the chosen playback level.
   - Because the delta can include parts of the headphone’s own frequency response, combining it with a separate headphone measurement can double-count some features (i.e., you may correct the same deviation twice).
   
   Practical implications:
   - Treat the “Target + Delta” approach as experimental and validate by A/B testing and mix translation.
   - In some cases, applying the delta as a small, smoothed “preference / monitoring correction” on top of an existing headphone EQ may work better than using “Target + Delta” to derive a new measurement-based EQ.
   - If you want the delta to represent *mostly the listener residual*, first EQ the headphone close to the chosen target (e.g., with an oratory1990/AutoEQ profile), then run HearCal with that EQ active.

   (see section above, "Methodologies for Applying Calibration Deltas" for a discussion)

   Safety / sanity check: If your delta (or resulting EQ) suggests large or narrow corrections (e.g., >6 dB in any band or very high-Q “spikes”), treat it as unreliable—retest on another day, smooth/average results, and limit EQ to a few broad bands (prefer ≤3–6 dB total adjustment).

3. **Rename & Categorize**: You now have a personalized target curve. Right-click it and rename it to something like `HOE2018_corrected_username_headphones`. 
   > **Important:** This calibration is unique to the specific combination of **your ears** and **these specific headphones**. It will not work for other users or other headphone models.
   
   <img width="1297" height="658" alt="image" src="https://github.com/user-attachments/assets/048a0688-9a8b-43b2-ae9f-374c81318a5d" />

4. **Export the Corrected Target**: 
   * Left-click your new corrected target to select it.
   * Go to **File -> Export -> Export Measurement as Text**.
   * Ensure you export the **whole frequency range**. (Standard smoothing is usually fine).
   * Set **Export Units** to **dBFS** and **Delimiter** to **Space**. 
   * Click OK and save it as a `.txt` file.

   <img width="737" height="851" alt="image" src="https://github.com/user-attachments/assets/a2183809-a98b-4e8e-bf43-dd9695cd7397" />

5. **Aligning in REW EQ Tool** (Only needed if you want to play around with the filters in the REQ EQ, skip otherwise): 
   * Left-click your original headphone measurement (e.g., the oratory1990 file).
   * Open the EQ tools via **Tools -> EQ**.
   * In the **Target Settings** panel on the right, set **Target Type** to **None**.
   * Open the **House Curve** panel and load the `.txt` file you just exported.
   * Click **"Calculate target level from response"** to visually align the target curve to the measurement.

   <img width="1254" height="664" alt="image" src="https://github.com/user-attachments/assets/70d06be5-4511-4e55-b2d0-b7502b58b2c0" />

6. **Filter Generation via Squig.link**: 
   While REW has internal EQ capabilities, many find [squig.link](https://squig.link/) more intuitive for creating final filters.
   * Open Squig.link. In the lower-right, clear any default curves using the **X** button.
   * Hit the **Equalizer** tab on the left. Remove bands so only 4 or 5 remain to start.
   * Set the **AutoEQ range** to **20 to 20,000Hz**.
   * Click **"Upload FR"** and upload your headphone measurement.
   * Click **"Upload Target"** and upload your corrected target curve.

   <img width="1911" height="879" alt="image" src="https://github.com/user-attachments/assets/c7894203-5848-4c3d-a346-f130db647c84" />

7. **Optimize the EQ**: 
   * Ideally, manually adjust the filters on the left to match the headphone measurement to your corrected target. 
   * If you use the **AutoEQ** button, ensure the results meet quality criteria: **broad Q factors**, **minimal gain changes**, and a **low number of bands**. Avoid over-correcting; use headphones that already have a relatively good frequency response.
  
   > ️⚠️ Note that large deviations in any band (.e.g, >6 dB) might indicate the need for professional audiometry rather than DIY correction. Do not attempt to boost or cut by large margins.

   * When satisfied, hit **"Export"** on the left to save the **EqualizerAPO** `.txt` file.

   <img width="1912" height="887" alt="image" src="https://github.com/user-attachments/assets/0ba860b1-2071-48f8-958f-a97c1258bd6f" />


8. **Final Considerations**: 
   * You now have a TXT file containing EqualizerAPO filters.
   * If using **FabFilter Pro-Q 3**, you must multiply the Q factor by **1.41** for the filters to behave correctly.
   * Always use **minimum-phase filters** in your equalizer.

### Step 4: Create Equalizer Configuration

Once you have your EqualizerAPO filters from Squig.link, you need to load them into your equalizer. While you can type values manually, this repository includes a tool to convert them directly for **Toneboosters Equalizer Pro**.

1. **Open the Converter**: Navigate to the `apo_to_tbeqpro` directory in this repository and open the `apo_to_tbeqpro.html` file in any web browser.
2. **Load Your Filters**: Click "Browse" and select the `.txt` file you exported from Squig.link.
3. **Name Your Preset**: Adjust the "Name" field to identify your specific calibration (e.g., `HD600_HearCal_2025`).
4. **Export**: Hit **"Download XML"**.

<img width="1299" height="622" alt="image" src="https://github.com/user-attachments/assets/114e40d3-5001-4543-a958-4b57426e8138" />

5. **Install the Preset**: Place the downloaded XML file into the Toneboosters user preset directory for your operating system:

| Operating System | Directory Path |
| :--- | :--- |
| **Windows** | `%APPDATA%\Toneboosters\TB Equalizer Pro_programs\User\Presets` |
| **Linux** | `~/.config/Toneboosters/TB Equalizer Pro_programs/User/Presets` |
| **macOS** | `~/Library/Audio/Presets/ToneBoosters/TB Equalizer Pro_programs/User/Presets` (or similar Library path, not known exactly) |

6. **Final Implementation**: 
   * Load the **TB Equalizer Pro** VST/AU plugin.
   * **Crucial:** Place the plugin at the **very end** of your master monitoring chain (after any other processing).
   * Select your new preset. 
   * Listen to high-quality reference tracks and begin mixing. Continue with step 7 and validate and refine.

---

## 6. Verifying Translation & Making Adjustments

This is only a starting point. If you figure out, that a boost in a specific area due the corrected target curve leads to dull mixes in a specific frequency area when listening on different monitoring system, you need to adjust the equalization or the target curve down in that area and vice-versa for better translation. This tool and the target curve will not give you the ideal solution, but just *maybe* a better starting point. It may also throw you off totally. Every person compensates differently for what he/she hears. It might be enough to look at the adjustment graph and just take the results as hint what to check out by manually EQing the normal Harman Over-Ear 2018 correction curve for your headphone to try something new. 

It may also be worthwhile to repeat the tests spaced apart on multiple days, compare the results and then calculate an average delta. Always check your mix translations on multiple monitoring systems and adjust your EQ accordingly for what you have found out. Large differences between sessions suggest measurement noise rather than true hearing characteristics. 

  >**⚠️ Adaptation Period Required**
  >
  >If you mix using a corrected profile, you should first spend significant time listening to music and reference tracks through this correction. Your brain needs to recalibrate what "normal" sounds like. 
  >
  >*Example:* Suppose you're less sensitive at 4 kHz, and the correction applies a boost there. Initially, familiar music may sound harsh or bright—not because the correction is wrong, but because you're unaccustomed to hearing that frequency at its "true" level. If you immediately start mixing, you may instinctively cut 4 kHz to reduce the perceived harshness, resulting in mixes that sound dull to others. The correction only works if you internalize the new tonal balance first. 
  >
  > Give yourself at least several hours of critical listening to reference material before making mix decisions.

The whole approach should be considered experimental. Feel free to share your experiences in the discussion area and possibly your knowledge from experience or research.

### Averaging multiple tests

You can (and actually **SHOULD**) use the tool hearcal_avg.py to calculate an average profile across multiple tests. If you start it, you can selected multiple files and simply generate an average. Don't average across multiple tests done in one sitting, but across multiple days, maybe even days spaced apart. The tool will write two files:
* hearcal_avg.csv containing the average calibrated profiles
* hearcal_avg_details.csv containing average, minimum measurement, maximum measure, standard deviation, variance and spread for each frequency measure across multiple tests

It will also display a brief report with the statistics across multiple tests. It looks something like this:

```
===========================================================================
 HEARCAL AVERAGER: FILE COMPARISON & AVERAGE
===========================================================================
Source Files:    test1.csv, test2.csv
Main Average:    hearcal_avg.csv
Detailed Stats:  hearcal_avg_details.csv
---------------------------------------------------------------------------
[CONSISTENCY SUMMARY]
  Average Gap:     0.23 dB (Typical variance across all bands)
  Largest Gap:     0.50 dB at 20.0 Hz
---------------------------------------------------------------------------
BAND         |  AVG VAL | MAX DIFF |      VAR | STATUS
---------------------------------------------------------------------------
Sub          |     -0.5 |      0.5 |      0.1 | Stable
Bass         |      0.1 |      0.5 |      0.0 | Stable
Low-Mid      |      0.5 |      0.0 |      0.0 | Stable
Mid          |     -0.3 |      0.5 |      0.1 | Stable
High-Mid     |      0.1 |      0.5 |      0.0 | Stable
High         |      0.1 |      0.5 |      0.0 | Stable
Air          |     -0.3 |      0.5 |      0.1 | Stable
---------------------------------------------------------------------------
METRIC EXPLANATIONS:
  AVG VAL:  The final average loudness offset used for your profile.
  MAX DIFF: The largest disagreement between your test runs in this band.
  VAR:      Statistical variance. High numbers mean tests were inconsistent.
  STATUS:   'Stable' means your test runs matched closely in this range.
---------------------------------------------------------------------------
[SETUP RELIABILITY]
  Thumbs Up: Your measurements are very consistent.
===========================================================================
```

---

## 7. Ideas
* Limit the shuffling in verification mode to specific band widths in order to have neighboring frequencies that compare better.
* Option to discard outliers in the averaging. If one trial shows a +10 dB boost at 8 kHz and the others show +2 dB, don't average it, but delete it. That was likely a measurement error (e.g., the headphone moved on your head).
* 1000Hz anchor may tilt everything if the user has a dip or peak at exactly this frequency. It might make sense to verify the anchor: the user compares 1kHz vs. 500Hz and 1kHz vs. 2kHz at the very beginning to ensure their "Zero Point" is actually stable
