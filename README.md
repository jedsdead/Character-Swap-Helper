# H3 Character Swap for Wan2GP

A Wan2GP plugin for character swap LoRAs on MiniMax H3 Ref2VA: replace a person in a clip with a character from an
image. It follows the recipe of the [H3 Character Swap LoRA](https://huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA)
and its author's [Character Swap tool](https://github.com/akatz-labs/h3-character-swap-tool), and isn't tied to that
LoRA: it works with any swap LoRA trained on the same idea (masked regeneration, with the source clip as `<Video 1>`).

It adds an **H3 Character Swap** section to the main generation page (MiniMax H3 Ref2VA models) with:

- **Character Swap switch:** in masked video-to-video (*Denoise Control Video* with a Video Mask), also gives the
  untouched clip to H3 as `<Video 1>`, so the regenerated person follows the original performance (pose,
  expressions, lip movement). Wan2GP doesn't normally pass a reference video while it edits a video.
- **Prompt builder** in the wording of the LoRA's model card or of the tool.

The switch is read when each generation starts: switch it off for other masked edits.

## Requirements

- Wan2GP with a MiniMax H3 **Ref2VA** model
- A character swap LoRA in your H3 LoRA folder (Akatz Labs' Character Swap V1.5, or another one)

## Usage

1. Make a mask of the person from your clip, white where the person is: **Magic Mask** with `person`, or MatAnyone.
2. In the main page, with a Ref2VA model:
   - **Reference Images:** the character image (`<Picture 1>`), or a picture RefMod of the character
   - **Reference / Control Video:** *Denoise Control Video (Video-to-Video Edit)* with your clip
   - **Video Mask:** your mask, masked area regenerated; **Expand / Shrink Mask Area** about 44 (≈ 64 px)
   - **Audio:** *Generate Video based on Reference / Control Video + its Audio Track (Soundtrack Kept)*
   - **LoRA:** your swap LoRA (Character Swap V1.5 at 1.0), 1 guidance phase, Mask Denoising Mode *Grouped Rows* (default)
3. Tick **Character Swap** in the H3 Character Swap section, build or write the prompt, and generate.

The console shows `[H3 Character Swap] control video added as <Video 1>` when it applies. With another LoRA, use the
strength, trigger word and prompt wording from its own model card.
Best with short, continuous clips (up to about 15 s, one window).

### With RefMods

Works with the [RefMods](https://github.com/jedsdead/Refmod-Fork) plugin: a picture RefMod can be the character
(with or without a reference image), and video RefMods follow the control video as `<Video 2>`, `<Video 3>`.

## Install

In Wan2GP, open the **Plugins** tab, paste this repository's URL under *Install New Plugin*, install,
enable it and restart Wan2GP.

## Credits

The Character Swap LoRA and the Character Swap tool are by [Akatz Labs](https://github.com/akatz-labs). This plugin
reimplements the tool's recipe in Wan2GP; it contains no code from the tool.

## License

MIT. The Character Swap LoRA and MiniMax H3 have their own licence (MiniMax H3 Community License).
