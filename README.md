# H3 Character Swap for Wan2GP

A Wan2GP plugin for the [H3 Character Swap LoRA](https://huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA):
replace a person in a clip with a character from an image, following the recipe of the LoRA author's
[Character Swap tool](https://github.com/akatz-labs/h3-character-swap-tool).

It adds an **H3 Character Swap** section to the main generation page (MiniMax H3 Ref2VA models) with:

- **Character Swap switch:** in masked video-to-video (*Denoise Control Video* with a Video Mask), also gives the
  untouched clip to H3 as `<Video 1>`, so the regenerated person follows the original performance (pose,
  expressions, lip movement). Wan2GP doesn't normally pass a reference video while it edits a video.
- **Prompt builder** in the wording of the LoRA's model card or of the tool.

The switch is read when each generation starts: switch it off for other masked edits.

## Requirements

- Wan2GP with a MiniMax H3 **Ref2VA** model
- The Character Swap LoRA (V1.5 recommended) in your H3 LoRA folder

## Usage

1. Make a mask of the person from your clip, white where the person is: **Magic Mask** with `person`, or MatAnyone.
2. In the main page, with a Ref2VA model:
   - **Reference Images:** the character image (`<Picture 1>`)
   - **Reference / Control Video:** *Denoise Control Video (Video-to-Video Edit)* with your clip
   - **Video Mask:** your mask, masked area regenerated; **Expand / Shrink Mask Area** about 44 (≈ 64 px)
   - **Audio:** *Generate Video based on Reference / Control Video + its Audio Track (Soundtrack Kept)*
   - **LoRA:** Character Swap V1.5 at 1.0, 1 guidance phase, Mask Denoising Mode *Grouped Rows* (default)
3. Tick **Character Swap** in the H3 Character Swap section, build or write the prompt, and generate.

The console shows `[H3 Character Swap] control video added as <Video 1>` when it applies.
Best with short, continuous clips (up to about 15 s, one window).

## Install

In Wan2GP, open the **Plugins** tab, paste this repository's URL under *Install New Plugin*, install,
enable it and restart Wan2GP.

## Credits

The Character Swap LoRA and the Character Swap tool are by [Akatz Labs](https://github.com/akatz-labs). This plugin
reimplements the tool's recipe in Wan2GP; it contains no code from the tool.

## License

MIT. The Character Swap LoRA and MiniMax H3 have their own licence (MiniMax H3 Community License).
