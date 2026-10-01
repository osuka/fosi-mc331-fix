
# Fix for low level volume cutting in FOSI MC-331 amplifier

From [this thread](https://community.fosiaudio.com/threads/mc331-low-volume-cut-off.42905) that contains a Windows version and a lot more details

For an [Android version go to here](https://github.com/CaseresMaxi/fosi_MC331_fix)

- Just created a version for linux and macos
- None of these are services, you need to start them from the console yourself

The intented usage is basically:

```sh
# open a terminal, run

uv run macos/fosimc331-macos.py

# or

uv run linux/fosimc331.py

# and just leave it running
```

If this gets annoying for you, it is easy enough to run them as a service, but that is not covered in this repo.


## What exactly is this?

The Fosi MC331 is small amplifier with 2 vaccuum tubes, relatively cheap and powerful but with a fatal flow: when volume is low, it _intentionally_ cuts it, apparently due to some noise prevention effort.

The problem is that this makes the device completely unusable at lower level, and that lower level is not "extremely low" but just listening in the evening for instance without waking up the whole family.

Some very clever people have found a workaround: send a command via USB to the device to change the noise level at which it cuts.

This doesn't appear to actually increase the amount of noise and fixes it completely. I don't really know why Fosi refuses to do this change, I believe it is because the device can't receive firmware upgrades.

## Details

For the actual details look into the code, but essentially the Fosi:

- Presents itself as two devices depending on the mode it is in (OPT/AUX, USB mode), ie which input is selected.
- The code works for both, but the way it communicates with the device changes depending on that
- We use pyusb and pyhid for sending the command

Caveat (from the original thread):
 
> While the official ACPWorkbench software allows you to turn this off, I ran into the classic OEM hardware limitation: the amplifier's MCU acts as the master. Even if you save the configuration to the DSP's Flash memory (via Save Parameter to Flash), the MCU violently overwrites the DSP with the factory defaults (Noise Gate ON at -68dB) upon every reboot or power cycle.
 

