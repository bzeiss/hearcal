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
   > Start with your headphone's Harman EQ *without* personal hearing correction. Only use HearCal if you experience consistent translation problems. Then A/B test to verify the correction actually helps your mixes.

Be aware that real hearing loss cannot be compensated with this tool.

HearCal is a cross-platform command-line application with a Terminal User Interface (TUI). It is designed to be lightweight, easy to adapt, and low-maintenance. While it requires basic technical knowledge to run, the calibration process itself is intuitive.

<img width="815" height="637" alt="image" src="https://github.com/user-attachments/assets/86848267-ee4c-4589-9d91-d939629ae82b" />
<img width="802" height="638" alt="image" src="https://github.com/user-attachments/assets/0a9869ad-6cb0-4bad-80dc-78b06c2ce572" />

### Project Status & Disclaimers

* Experimental Tool: This project is a functional implementation of psychoacoustic principles, but I am not an acoustics professional or physicist. It is a "community-driven" attempt to improve monitoring accuracy.
* Contributions: If you have expertise in psychoacoustics or Python and see room for improvement, merge requests are welcome! The goal is to keep the tool effective yet simple and maintainable.
* AI Integration: Parts of this documentation and code were developed or refined with the assistance of AI to ensure clarity and provide a starting point for development.

### Credits

This general EQ workflow was inspired by the research and methods shared by [MixphonesUK](https://www.youtube.com/@MixPhonesUK). The correction workflow is inspired by a well known closed headphone system for mixing.

---

## 2. Prerequisites

To implement the HearCal workflow, you will need:

* **SPL Meter:** Capable of **A-weighting** and **C-weighting** (a smartphone app can work, though a dedicated meter is more accurate).
* **Headphone Amplifier:** A clean, high-quality amp is recommended to ensure your headphones have sufficient headroom.
* **Python 3.10+**: The core environment for the script.
* **PIP Packages**: `textual`, `numpy`, and `sounddevice`.
* **REW (Room EQ Wizard)**: Used for arithmetic.
* **Target Curve:** The Harman Over-Ear 2018 (or your preferred AutoEQ target) in .csv or .txt format.
* **Equalizer Software**: **[Toneboosters Equalizer Pro](https://www.toneboosters.com/tb_equalizer_pro.html)**: Recommended for cross-platform support. A converter from EqualizerAPO to TB format is included in this repo. *Alternatives*: Apulsoft **[ApQualizer2](https://www.apulsoft.ch/apqualizr2/)** supports import of EqualizerAPO equalizer profiles directly. Fabfilter **Pro-Q3/4** requires the multiplication of the Q factor by 1.41!

---

## 3. Installation

1. **Install Python**: Download from [python.org](https://www.python.org/).
2. **Install Dependencies**: Open your terminal or command prompt and run:
```bash
pip install textual numpy sounddevice
```

3. **Download HearCal**: Clone this repository or download the hearcal.py script to a dedicated folder on your machine.

---

## 4. Usage

### Step 1: Adjust your headphones to the calibration loudness

Perceived loudness is not consistent across all frequencies at all volume levels. This phenomenon is described by the **Fletcher-Munson curves** (and the modern ISO 226 standard). What is important: there is a theoretical "sweet spot" level for mixing where our hearing is most linear, meaning frequency-dependent adjustments are less drastic than at others. 

The ideal level, according to this often cited work, for mixing with the most balanced perception of all frequencies—while remaining safe and bearable—is generally considered to be **83 dB to 85 dB SPL** as a room calibration convention. To my knowledge, there is no universal standard like this for headphones currently. So these values may or may not apply.

#### Why 85 dB?
Human hearing is naturally non-linear. At low volumes (around 40–60 dB), your ears are much less sensitive to low and high frequencies, causing the midrange (especially 3–4 kHz) to sound disproportionately loud. As volume increases, these curves "flatten out," allowing you to perceive the bass and treble more accurately in relation to the mids.

* **The "Flattest" Level:** The curves continue to flatten as volume increases toward the threshold of pain (120+ dB). However, mixing at 100+ dB is not bearable for more than a few minutes and will cause rapid ear fatigue and permanent hearing damage.
* **The Industry Standard:** The 85 dB SPL figure is the recognized standard for cinema and large professional studios. At this level, the frequency response is flat enough to make accurate EQ decisions without endangering your hearing.

#### Practical Considerations for "Bearability"
While 85 dB is the theoretical sweet spot for room calibration, it can be fatiguing over a long 8-hour session. Many engineers follow these practical guidelines:

* **Small Rooms/Headphones:** Due to ear fatigue, many professionals prefer monitoring at **76 dB to 80 dB SPL** for the bulk of a session.
* **The "Check" Method:** It is common practice to do the majority of the work at a moderate level (75–80 dB) and then turn the volume up to **85 dB** specifically for "checking" the low-end and high-end balance before turning it back down. Bear also in mind that some headphones may show more clarity and bass punch at higher levels 80-85 dB. It's unclear whether there is real scientific work on this.

The most important point is: choose one SPL loudness and calibrate to the loudness you mix at. If you mix at different levels, like 76 to 80 dB for long session and 85 dB for checking, you should likely perform the test multiple times at exactly these differing levels as the test assumes one specific loudness and adjusts to it.

#### Headphone Calibration with an SPL Meter
To achieve the most accurate results based on the Fletcher-Munson principles, you should set your SPL meter to **A-weighting** or **C-weighting** and a **Slow** response time. Be aware that the approach shown below will not yield exact results and may easily be off by a few dBs.

While C-weighting is often used for room calibration, **A-weighting** is sometimes recommended by experienced mixers here for a specific reason:
* **Sub-bass filtering:** Sub-bass produces a massive amount of physical energy that registers high on a meter, but for many people, it is much less "present" in their actual hearing than the mids and highs. 
* **Focusing the Measurement:** By using A-weighting (which rolls off the extreme lows), you effectively filter out that sub-bass energy from the measurement. This ensures you are calibrating the loudness based on the frequencies where your hearing is most sensitive, preventing the sub-bass from "tricking" the meter into thinking the volume is louder than it feels.

C-weighting may be used if you prefer aligning physical energy rather than perceptual loudness, but consistency is more important than choice. The jury is still out on this.

**Calibration Procedure:**
1.  **Set Meter:** Select **A-Weighting** and **Slow** response (this averages the "peaks" and "valleys" of the noise over 1 second for a steady reading).
2.  **Signal:** Play **Pink Noise** (some mixers prefer brown noise or variations of brown noise) through one side of your headphones.
3.  **Target:** Position your SPL meter (or phone app) against the headphone driver and adjust your hardware volume until you hit your chosen level (**79–85 dB**).
4.  **Hardware Marker:** Ideally, connect your amp to a fixed line-out (so levels aren't tied to an interface knob) and put a physical marker on your headphone amp volume knob. **This is now your reference level for the entire calibration.**

Do not perform long calibration sessions at 85 dB. Take breaks every 10–15 minutes.

### Step 2: Run HearCal

Launch the application from your terminal:

```bash
python hearcal.py
```
#### Phase 1: Calibration (A/B Comparison)

The objective of this phase is to establish a baseline by matching the perceived volume of various frequencies to a constant 1000Hz anchor. 31 ISO bands are used as a compromise between perceptual resolution, calibration time, and listener fatigue.

1. **Reference Level**: Ensure your hardware is set to your marked calibration level (e.g., **85dB SPL**).
2. **Start Audio**: Press **`[SPACE]`** to begin generating sound.
3. **Toggle Mode [T]**: Press **`[T]`** to switch between the **Reference Tone** (1000Hz, which never changes volume) and the **Test Tone** (the frequency you are currently adjusting).
4. **Adjust Volume**: Use the **`[UP/DOWN]`** cursor keys to change the level of the test tone until it sounds exactly as loud as the 1000Hz reference.
5. **Navigate Bands**: Use **`[LEFT/RIGHT]`** cursor keys to move to the next frequency band. Perform this adjustment for all 31 ISO bands.

#### Phase 2: Verification (The "Reality Check")

Phase 1 establishes an initial estimate. Phase 2 is where perceptual bias is actively challenged, and results should not be considered reliable unless they hold up under shuffle and pulse-only testing.

Press **`[V]`** to enter the refinement screen. This phase uses a more advanced methodology to eliminate "loudness adaptation"—the phenomenon where your brain adjusts to a sound, making it seem quieter than it actually is.

* **Sequential Pulse (Anchor → Gap → Test)**: By default, moving to a frequency in this mode plays the 1000Hz anchor, followed by a one-second silence, and then the test tone.
* If the second tone sounds louder than the first, press **`[DOWN]`**.
* If the second tone sounds quieter, press **`[UP]`**.

* **Pulse-Only Mode [P]**: Press **`[P]`** to disable the anchor and play only the level-adjusted pulse of the current frequency. This helps you hear how a frequency sits in isolation. In this mode, step through the frequency bands by pressing **`[LEFT]`** and **`[RIGHT]`** and compare whether they are the perceived same loudness next to each other. If not, adjust them.
* **Shuffle Mode [R]**: Press **`[R]`** to randomize the order of the frequency bands. This is the most critical step; it prevents your brain from "expecting" the next sound and forces an honest comparison between unrelated frequencies (e.g., comparing 60Hz directly after 8kHz).
* **Ascending Mode [A]**: Press **`[A]`** to restore the standard frequency order for a final sweep to ensure the loudness feels smooth and linear from bottom to top.

It is possibly a good idea to use the ascending mode in the end, by starting at 1000Hz and going to the left, and then again starting at 1000Hz going to the right. That way, the final pass verifies the loudness of the neighboring frequencies from the reference point. In my (so far short) experience, the shuffled loudness comparisons when the frequency jumps between the frequencies are high, are hard to judge.

#### Phase 3: Save and Exit

Once you are confident that every frequency band is perceived at an equal loudness:

1. Press **`[S]`** to save your `hearing_profile.csv`.
2. Press **`[ESC]`** to return to the main menu.

*Note: You do not need to finish the calibration in one sitting. You can press **`[L]`** at any time to load your last saved state and continue refining your profile later.*

### Step 3: Integrate in REW

The curve saved by HearCal can be loaded as a measurement in [REW (Room EQ Wizard)](https://www.roomeqwizard.com/). This process allows us to combine your personal hearing delta with objective headphone measurements and target curves.

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
   * Select the **"A + B"** operation and hit **"Generate"**.

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
   * Always use **minimal-phase filters** in your equalizer.

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

## 5. Verifying Translation & Making Adjustments

This is only a starting point. If you figure out, that a boost in a specific area due the corrected target curve leads to dull mixes in a specific frequency area when listening on different monitoring system, you need to adjust the equalization or the target curve down in that area and vice-versa for better translation. This tool and the target curve will not give you the ideal solution, but just *maybe* a better starting point. It may also throw you off totally. Every person compensates differently for what he/she hears. It might be enough to look at the adjustment graph and just take the results as hint what to check out by manually EQing the normal Harman Over-Ear 2018 correction curve for your headphone to try something new. 

It may also be worthwhile to repeat the tests spaced apart on multiple days, compare the results and then calculate an average delta. Always check your mix translations on multiple monitoring systems and adjust your EQ accordingly for what you have found out. Large differences between sessions suggest measurement noise rather than true hearing characteristics. 

For tuning further, maybe try also [Owliophile](https://owliophile.com/) with and without corrective EQ.

The whole approach should be considered experimental. Feel free to share your experiences in the discussion area and possibly your knowledge from experience or research.

---

## 6. Ideas
* Allow the option to use band-limited noise (e.g., 1/3-oct noise) (or maybe even band-limited music?) for a test tone. Sine tones can exaggerate narrow resonances and standing-wave effects in the ear canal and are not how broadband music is perceived.

