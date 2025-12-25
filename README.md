# HearCal: Perceptual Headphone Calibration for Mixing

HearCal is a Python-based diagnostic and refinement tool designed to bridge the gap between objective acoustic targets and your personal hearing when calibrating headphones for mixing music on headphones.

## 1. Introduction

The goal of HearCal is to create a **personalized hearing profile** (delta curve) that accounts for the specific characteristics of your ears and your headphones for the purpose of creating an equalizer profile that adjusts a headphone-specific measure to a specific target curve like the Harman Over-Ear 2018 curve **as well as your individual hearing profile on these headphones**, for the purpose of mixing music, for example.

Standard headphone targets, like the Harman Ove-Ear 2018 target, are based on "standard" listeners with good hearing. As hearing sensitivity varies with age, noise exposure or health, your perception often deviates from these baselines. HearCal uses a two-phase process to identify these deviations:

* **Phase 1 (Calibration)**: Uses **Instantaneous A/B Switching** to find equal-loudness thresholds across 31 ISO frequency bands compared to a reference anchor tone (1000Hz by default).
* **Phase 2 (Verification)**: Employs a **Sequential Pulse methodology** (Anchor → Silence → Test) to reset the ear's automatic gain control and prevent your brain from "adapting" to the sound, which can skew results. In this verification step, there multiple toggle modes that let you also disable the sequential pulsing and let you compare the adjusted levels side by side, shuffle the frequencies around so that you don't always compare the same two frequency bands next to each other and an ascending order toggle in order to deliberately compare frequency bands next to each other.

By combining your HearCal delta with an objective target, you create a monitoring environment optimized for your specific hearing.

HearCal is a Python based cross-platform command line application with a terminal user interface. It is designed that way to stay simple, be easy to adapt and low maintenance. You'll need some basic technical knowledge to run it and perform the overall calibration process for your headphones. It's not too hard though.

<img width="815" height="637" alt="image" src="https://github.com/user-attachments/assets/86848267-ee4c-4589-9d91-d939629ae82b" />
<img width="802" height="638" alt="image" src="https://github.com/user-attachments/assets/0a9869ad-6cb0-4bad-80dc-78b06c2ce572" />

## Disclaimers

* I'm not an acoustics expert, not an psychoacoustics expert and not a physicist. I hope the calibration method used here is reasonably sound. If not, you're welcome to let me know how to improve it.
* I generally don't know what I'm doing. Don't complain about it.
* A lot of the stuff here is vibe-coded and AI generated as a starting point or AI improved. If you don't like it, you may keep it to yourself. If you find real errors, please let me know.
* If you have improvements to the script, feel free to create merge requests. Be aware that I want this repo and script to stay simple and maintainable. This is not the place for scope creep. However, I want the calibration to be as effective as possible with the least amount of work.

## Credits

A lot of the content here was shared first by [MixphonesUK](https://www.youtube.com/@MixPhonesUK). I have just tried to add the hearing correction on top and documented the approach for the hearing correction. Be sure to check out the playlists on that channel and support them if it brings value to you.

---

## 2. Prerequisites

To implement the HearCal workflow, you will need:

* An SPL meter that allows adjustment to A-weighting and C-weighting
* Headphone amp (don't bother with all this without a good one)
* **Python 3.10+**: The core environment for the script.
* **PIP Packages**: `textual`, `numpy`, and `sounddevice`.
* **REW (Room EQ Wizard)**: Used for trace arithmetic and generating EQ filters.
* **[Toneboosters Equalizer Pro](https://www.toneboosters.com/tb_equalizer_pro.html)**: My personal preference for final EQ application as it works on all platforms including Linux, it is pretty powerful and doesn't cost a lot. A converter from EqualizerAPO format to TB Equalizer Pro is provided in this repository. You may also use other equalizers though. Apulsoft [ApQualizer2](https://www.apulsoft.ch/apqualizr2/) supports EqualizerAPO equalizer profiles directly, but I don't have any experience with it. Pro-Q requires the multication of the Q factor by 1.41!
* **Target Curve**: The **Harman Over-Ear 2018** (or any other preferred Oratory1990/AutoEQ target) in `.csv` or `.txt` format.

---

## 3. Installation

1. **Install Python**: Download from [python.org](https://www.python.org/).
2. **Install Dependencies**: Run the following in your terminal:
```bash
pip install textual numpy sounddevice
```

3. **Download HearCal**: Save `hearcal.py` to your local machine or clone/download the git repository.

---

## 4. Usage

### Step 1: Adjust your headphones to the calibration loudness

The loudness perceived by our ears does is not the same in all frequencies at all levels. This effect is described by the Fletcher-Munson curve (and the modern ISO 226 standard). You can read up on this [here](https://en.wikipedia.org/wiki/Equal-loudness_contour). What is important: there is a rough "best" level to mix music at, where frequency-dependant adjustments are not too drastic. The best level for mixing music with the most balanced (flattest) perception of all frequencies while remaining safe and bearable is generally considered to be 83 dB to 85 dB SPL.

#### Why 85 dB?

Human hearing is naturally non-linear. At low volumes (around 40–60 dB), your ears are much less sensitive to low and high frequencies, causing the midrange (especially 3–4 kHz) to sound much louder. As the volume increases, these curves "flatten out," meaning you perceive the bass and treble more accurately in relation to the mids.

* The "Flattest" Theoretical Level: The curves continue to flatten as volume increases toward the threshold of pain (120+ dB). However, mixing at 100+ dB is not "bearable" for more than a few minutes and will cause rapid ear fatigue and permanent hearing damage.
* The Industry Standard: The 85 dB SPL figure is the recognized standard for cinema and large professional studios (often calibrated using the "K-System" developed by Bob Katz). At this level, the frequency response is flat enough to make accurate EQ decisions without needing to blast the speakers to dangerous levels.

#### Practical Considerations for "Bearability"

While 85 dB is the technical sweet spot for flatness, it can still be fatiguing over a long 8-hour session. Many engineers follow these practical guidelines:

* Because of ear fatigue, many professionals prefering headphone monitoring  at 76 dB to 80 dB SPL for the majority of the session.
* The "Check": It is common practice to do the bulk of the mixing at a moderate level (75–80 dB) and then turn the volume up to 85 dB specifically for "checking" the low-end and high-end balance, before turning it back down to save your ears.

#### Headphone calibration with an SPL meter

To achieve the most accurate results based on the Fletcher-Munson principles, you should set your SPL meter to A-weighting and a slow response time. While both weightings are designed to mimic human hearing, they are based on how we hear at very different volume levels.

* C-weighting follows the "Loud" curve. It provides an honest representation of the total energy in the room, including the sub-bass.
* A-weighting follows the "Quiet" curve. If you used A-weighting to calibrate your headphones to 85 dB, the meter would "ignore" much of the bass. 

Your mileage may vary, but the sub-bass area produces a lot of energy and, for many, is much less present in hearing than lows, low-mids, mids and highs. As a result, it may be a good idea to filter them out in the loudness measurement for the calibration.

When you are ready to calibrate your headphones, set your meter (or phone app) to the following:
* Weighting: A 
* Response/Speed: Slow (this averages the "peaks" and "valleys" of the sound over 1 second, giving you a steady number rather than a jumping needle).
* Target: Aim for your chosen level (79–85 dB) while playing Pink Noise through one speaker at a time.

Ideally, you'll make sure that you have connected your headphone amp to the line out or digitally to your audio interface (so that the levels are not tied to a knob on the audio interface) and the put a marker on your headphone amp.

### Step 1: Run HearCal

Launch the application from your terminal:

```bash
python hearcal.py
```

1. **Reference Level**: Set hardware volume so the 1000Hz anchor is at a comfortable mixing level (ideally **85dB SPL** using an SPL meter, see above).
2. **Calibration**: Use **[SPACE]** to play a continues sound. Press **[T]** to toggle between the reference tone (which always stays at the same level) and the test to (the tone of which you adjust the level). Use **[UP/DOWN]** cursor keys to adjust the level of the test tone (MODE: TESTING) until it matches the 1000Hz anchor in perceived loudness. The reference tone will always stay at the same level/loudness. Don't adjust the level of 1000 Hz, it is the reference tone. Use **[LEFT/RIGHT]** cursor keys to test the next band. Perform the level adjustment for all bands comparing the reference tone to the testing tone (by hitting T) and adjusting the level of the testing  tone until it matches for your ears.
3. **Verification**: Press **[V]** for the refinement screen. It offers multiple ways to verify your level adjustments. The sequential pulses (auto-played on navigation) or "Anchor-Gap-Test" is used to "zero in" on the subjective weight of each band. In this mode, the 1000Hz base tone is played at the calibration level, then after one second pause, the test tone at the corresponding frequency is played level adjusted. If the second tone is louder than the first one, adjust the level down by pressing the **[DOWN]** cursor key. If the second tone is quieter than the first one, adjust the level up using the **[UP]** cursor key. Otherwise leave it as it is. Step through all frequencies using **[LEFT/RIGHT]**. When done Switch to the Pulse-Only moder by pressing **[P]**. In this mode, just the level adjusted pulse at the currently selected frequency band is played. Now step through all shuffled frequencies using **[LEFT/RIGHT]** and see whether you perceive the frequencies at equal loudness. If not, adjust with the **[UP/DOWN]** cursor keys. Then, press **[R]** to reshuffle the frequency order. Now, different frequencies are next to each other in this list. Again, step through the list from left to right to see whether you perceive them at equal loudness. You may repeat this step multiple times, ideally, with some hours inbetween each test. Don't overstress it and do too much in one sitting, your ears will hear differently at different times and days. Finally, press **[A]** to order the frequencies in ascending order for a final test whether the perceived loudness is even. When done, press **[ESC]** to go back to the main screen.
4. **Save**: Press **[S]** to save your `hearing_profile.csv`.

You don't have to leave the app open for multiple sessions. with **[L]** you can load the state of the last saved calibration back into the app.

### Step 2: Integrate in REW

The curve saved can be loaded as a measurement in [REW](https://www.roomeqwizard.com/). This is what we use to create the adjusted target curves and headphone correction profile now that we have the hearing correction delta data.

1. Import your **Harman Target**, **HearCal Delta** and **Headphone Measurement** CSVs into REW (I'm using REW V5.40 Beta 111). You can do that by File->Import->Import Frequency Response.
   * Import your **HearCal Delta** (the file you have saved with hearcal).
   * Import your curve target, for over-ear headphones and mixing, try Harman Over-Ear 2018. You can get these at the [AutoEQ git repo](https://github.com/jaakkopasanen/AutoEq/tree/master/targets).
   * Import a headphone measurement for your specific headphone model. Use a source you trust. For example, the ones from [oratory1990](https://github.com/jaakkopasanen/AutoEq/tree/master/results/oratory1990).
  
   This is what it should look like:
   <img width="1299" height="661" alt="image" src="https://github.com/user-attachments/assets/5afd89da-990f-4439-b284-df8af6e13384" />

3. Now we add the hearcal correction delta to the target curve. To do that, hit "Arithmetic". As A, select your target curve that you want to adjust. As B, select your correction curve from hearcal. Select the "A + B" operation and hit "Generate".

   <img width="1288" height="201" alt="image" src="https://github.com/user-attachments/assets/06fb8ca9-8baf-48e1-9945-9e073a42e87a" />
   <img width="341" height="308" alt="image" src="https://github.com/user-attachments/assets/4487277e-bc29-4d18-9879-7f4f9c1bd611" />

4. We now have a delta target curve that we can work with. Let's rename this by right-clicking it and changing the name to something like "HOE2018_corrected_username_headphones". Be aware, that this calibration is headphone-specific **and** user-specific. It will only work in this exact combination.
   <img width="1297" height="658" alt="image" src="https://github.com/user-attachments/assets/048a0688-9a8b-43b2-ae9f-374c81318a5d" />

5. Let's save the delta target curve. Left-click it to select it. Then go to the menus: File->Export->Export Measurement as Text. Make sure that you export the whole frequency range. I have no idea what a good smoothing is. Make sure the export units are dBFS and Space is used as delimiter. Click OK and save as TXT file.

<img width="737" height="851" alt="image" src="https://github.com/user-attachments/assets/a2183809-a98b-4e8e-bf43-dd9695cd7397" />

6. Let's now create an equalization for our headphones. Left-click your headphone measurement (like the ones from oratory1990). Open the EQ tools using the menus Tools->EQ. Open the Target Settings expansion panel on the right, select Target Type to None. Open the hearing corrected target curve we have jsut saved as the House curve. Click "Calculate target level from response" to align the target curve to the measurement.

<img width="1254" height="664" alt="image" src="https://github.com/user-attachments/assets/70d06be5-4511-4e55-b2d0-b7502b58b2c0" />

7. Let's now create a filter. REW also has equalization capabilities, but I haven't had too much good results with it. This may be due to lack of knowledge how to use it properly. Personally, I use [squig.lit](https://squig.link/) to create the filters. Open it, one the lower-right, remove all curves from the initialization using the X button on the right. Then hit the Equalizer tab on the left. On the left, remove the bands so that there are only like 4 or 5 bands left. Adjust the AutoEQ range to 20 to 20000.

<img width="1911" height="879" alt="image" src="https://github.com/user-attachments/assets/c7894203-5848-4c3d-a346-f130db647c84" />

8. Click "Upload FR" and upload the headphone measurement, for example from oratory1990, here. You may also browse for headphones directly available on squig.link. The quality of the measurements may vary.

9. Click "Upload Target" and upload your corrected target curve here. It should now show both the headphone measurement and the target curve.
<img width="1902" height="884" alt="image" src="https://github.com/user-attachments/assets/c82d519e-b7e5-4493-803a-92d1a1a1a24e" />

10. Ideally, you'll now create a really well optimized EQ curve on the left to match the headphone measurement to the hearcal corrected target curve. You may also try to hit the AutoEQ button and see whether the filtering fulfils the quality criteria above, i.e. broad Q, low gain changes, little number of bands. Don't try to be to exact here and create a lot of filter bands, but use headphones that don't need a lot of correction and that have a good frequency response.

11. When you are happy with the equalization, hit "Export" on the left".
    
<img width="1912" height="887" alt="image" src="https://github.com/user-attachments/assets/0ba860b1-2071-48f8-958f-a97c1258bd6f" />

12. You now have a TXT file containing so called EqualizerAPO filters. We need to bring this into an Equalizer now to use it. You may use a converter for your favorite equalizer, use the Toneboosters Equalizer Pro converter provided here (see below) or type in the values manually. In Pro-Q, you'll need an adjustment factor of 1.41 for the Q. Results between equalizers may vary. Always use minimal-phase filters.

### Step 3: Create Equalizer Configuration

1. Open the HTML file in the apo_to_tbeqpro directory "apo_to_tbeqpro.html"
2. Browse for the file you have just exported from squig.link
3. Adjust the name
4. Hit "Download XML"
<img width="1299" height="622" alt="image" src="https://github.com/user-attachments/assets/114e40d3-5001-4543-a958-4b57426e8138" />
5. Place the XML file in the Toneboosters directory. For Windows, this is %APPDATA%\Toneboosters\TB Equalizer Pro_programs\User\Presets or however you want it organized there. On Linux, this is ~/.config/Toneboosters/TB Equalizer Pro_programs/User/Presets. On Mac probably something like ~/Library/Audio/Presets/ToneBoosters/TB Equalizer Pro_programs/User/Presets or /Library/Application Support/ToneBoosters/TB Equalizer Pro_programs/User/Presets or something similar. I don't have a Mac, so I won't know.
6. That's it. Load of the VST plugin, please it last in the master chain, listen to some music with it and see whether your mixes get better or not.

