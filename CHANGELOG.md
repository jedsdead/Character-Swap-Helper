# Changelog

## 0.2 (2026-10-18)

- Works with the RefMods plugin: a picture RefMod can be the character, and video RefMods follow the control video
  as `<Video 2>`, `<Video 3>`. Reference images are now read inside the pipeline, so the order the plugins load in
  doesn't matter.
- Two-phase generations also get `<Video 1>` in phase 2.
- Wording no longer tied to one LoRA: works with any character swap LoRA trained on the same recipe.

## 0.1 (2026-10-16)

- First release: H3 Character Swap section in the main generation page, with the Character Swap switch (control
  video given to H3 as `<Video 1>` in masked video-to-video) and a prompt builder.
