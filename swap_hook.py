"""Pipeline hook: give the control video to MiniMax H3 as <Video 1> during a masked video-to-video generation.

The H3 Character Swap recipe regenerates only the masked person: the source video is the target latent and the
tokens outside the mask stay on it (WanGP's "Denoise Control Video" with a Video Mask, Grouped Rows mask mode).
It also shows the model the untouched source as reference <Video 1>, so the regenerated person follows the
original performance. WanGP never adds a reference video while it denoises a control video, so this hook adds one:
right after the reference images (<Picture 1>...), the control video frames of the window are added as a reference
video, exactly as WanGP adds a native Ref2VA reference video.

It applies, while "Character Swap" is switched on in the plugin, to Ref2VA generations that use Denoise Control
Video with a Video Mask and at least one reference image. No WanGP file is modified.
"""

import functools

from . import settings

LOG_PREFIX = "[H3 Character Swap]"
_WRAPPED_FLAG = "_h3_character_swap_wrapped"


def frames_17n5(count):
    """Largest H3 frame count (5 + 17n) not above count, or 0."""
    count = int(count)
    return 0 if count < 5 else 5 + 17 * ((count - 5) // 17)


def _chain_contains_wrapper(function, limit=64):
    pending, seen = [function], set()
    while pending and len(seen) < limit:
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        value = getattr(value, "__func__", value)
        if getattr(value, _WRAPPED_FLAG, False):
            return True
        pending.append(getattr(value, "__wrapped__", None))
    return False


def _missing(pipe, kwargs):
    """What prevents adding <Video 1> to this generation, or None."""
    if not getattr(pipe, "reference_mode", False) or getattr(pipe, "fixed_prompt", None) is not None:
        return "a MiniMax H3 Ref2VA model"
    if "G" not in (kwargs.get("video_prompt_type") or "") or kwargs.get("input_frames") is None:
        return "Denoise Control Video with a control video"
    if kwargs.get("input_masks") is None:
        return "a Video Mask"
    if not kwargs.get("input_ref_images"):
        return "a reference image (the character)"
    return None


def _wrap_generate(cls, module):
    current = cls.__dict__.get("generate")
    if current is None or _chain_contains_wrapper(current):
        return False
    original = current

    @functools.wraps(original)
    def generate(self, *args, **kwargs):
        if not settings.get()["enabled"] or kwargs.get("refinement_mode") or getattr(self, "audio_only", False):
            return original(self, *args, **kwargs)
        missing = _missing(self, kwargs)
        if missing is not None:
            if "G" in (kwargs.get("video_prompt_type") or ""):
                print(f"{LOG_PREFIX} Character Swap is on, but <Video 1> was not added: this generation needs {missing}")
            return original(self, *args, **kwargs)
        frames = kwargs["input_frames"]
        fps = kwargs.get("fps", 24) or 24
        frame_num = int(kwargs.get("frame_num") or 0)
        state = {"pending": len(kwargs["input_ref_images"]), "added": False}
        class_method = type(self)._add_image_reference

        def add_image_reference(image, target_width, target_height, image_refs_relative_size, presentation, visual_latents, refs):
            result = class_method(self, image, target_width, target_height, image_refs_relative_size, presentation, visual_latents, refs)
            state["pending"] -= 1
            if state["pending"] == 0 and not state["added"]:
                state["added"] = True
                video = module._as_video(frames)
                count = frames_17n5(min(video.shape[1], frame_num) if frame_num else video.shape[1])
                if count < 5:
                    print(f"{LOG_PREFIX} source too short to be a reference video ({video.shape[1]} frames)")
                    return result
                source = module._resize_video(video[:, :count], target_height, target_width)
                self._add_video_reference(source, None, fps, presentation, visual_latents, [], refs)
                print(f"{LOG_PREFIX} control video added as <Video 1> ({count} frames, {target_width}x{target_height})")
            return result

        self._add_image_reference = add_image_reference
        try:
            return original(self, *args, **kwargs)
        finally:
            self.__dict__.pop("_add_image_reference", None)
            if not state["added"]:
                print(f"{LOG_PREFIX} WARNING: the control video could not be added as <Video 1>")

    setattr(generate, _WRAPPED_FLAG, True)
    cls.generate = generate
    return True


def install():
    """Wrap WanGP's MiniMax H3 pipeline. Safe to call any number of times."""
    from models.minimax_h3 import pipeline as native
    if _wrap_generate(native.MiniMaxH3Pipeline, native):
        print(f"{LOG_PREFIX} hooked MiniMax H3 pipeline")
    return True
