"""Pipeline hook: give the control video to MiniMax H3 as <Video 1> during a masked video-to-video generation.

The H3 Character Swap recipe regenerates only the masked person: the source video is the target latent and the
tokens outside the mask stay on it (WanGP's "Denoise Control Video" with a Video Mask, Grouped Rows mask mode).
It also shows the model the untouched source as reference <Video 1>, so the regenerated person follows the
original performance. WanGP never adds a reference video while it denoises a control video, so this hook adds one,
in the place WanGP gives a native Ref2VA reference video: after the reference images (<Picture 1>...), in phase 1
and, for two-phase generations, in phase 2 too.

The reference images are read from inside the pipeline when it adds them, not from the request, so references added
by other plugins on the way count too. RefMods: a picture RefMod can be the character; video RefMods, which WanGP
would drop while it denoises a control video, follow as <Video 2>, <Video 3> (RefMods already numbers them so).

It applies, while "Character Swap" is switched on in the plugin, to Ref2VA generations that use Denoise Control
Video with a Video Mask. No WanGP file is modified.
"""

import functools
import sys

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
    return None


def _generate_locals(limit=4):
    """Local variables of WanGP's MiniMaxH3Pipeline.generate, seen from a method it calls (or None)."""
    frame = sys._getframe(2)
    for _ in range(limit):
        if frame is None:
            return None
        if frame.f_code.co_name == "generate" and "refs" in frame.f_locals and "presentation" in frame.f_locals:
            return frame.f_locals
        frame = frame.f_back
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
        control = kwargs["input_frames"]
        fps = kwargs.get("fps", 24) or 24
        frame_num = int(kwargs.get("frame_num") or 0)
        added = {"phase 1": False, "phase 2": False}
        images = {"phase 1": 0, "phase 2": 0}
        cls_type = type(self)

        def add_videos(where, local, presentation, visual_latents, refs, width, height):
            """<Video 1> (the control video), then the reference videos WanGP leaves out while it denoises a control
            video (video RefMods), right where WanGP puts reference videos."""
            added[where] = True
            video = module._as_video(control)
            count = frames_17n5(min(video.shape[1], frame_num) if frame_num else video.shape[1])
            if count < 5:
                print(f"{LOG_PREFIX} source too short to be a reference video ({video.shape[1]} frames)")
                return
            self._add_video_reference(module._resize_video(video[:, :count], height, width), None, fps, presentation, visual_latents, [], refs)
            extra = 0
            video_prompt_type = str(local.get("video_prompt_type") or "") if local else ""
            for name, letter in (("input_frames2", "+"), ("input_frames3", "*")):
                source = local.get(name) if local else None
                if source is None or letter not in video_prompt_type:
                    continue
                source = module._as_video(source)
                self._add_video_reference(module._resize_video(source, height, width), None, fps, presentation, visual_latents, [], refs)
                extra += 1
            if where == "phase 1":
                more = f", plus {extra} more reference video(s) as <Video 2>..." if extra else ""
                print(f"{LOG_PREFIX} control video added as <Video 1> ({count} frames, {width}x{height}){more}")

        def add_image_reference(image, target_width, target_height, image_refs_relative_size, presentation, visual_latents, refs):
            result = cls_type._add_image_reference(self, image, target_width, target_height, image_refs_relative_size, presentation, visual_latents, refs)
            local = _generate_locals()
            if local is None:
                return result
            where = "phase 1" if refs is local.get("refs") else "phase 2" if refs is local.get("phase_2_refs") else None
            if where is not None and not added[where]:
                images[where] += 1
                if images[where] >= len(local.get("input_ref_images") or []):  # after the last reference image
                    add_videos(where, local, presentation, visual_latents, refs, target_width, target_height)
            return result

        def prepare_audio_references(*call_args, **call_kwargs):
            # Phase 1 without any reference image: still before the audio references, like a native reference video
            local = _generate_locals()
            if local is not None and not added["phase 1"]:
                add_videos("phase 1", local, local["presentation"], local["visual_latents"], local["refs"], local["width"], local["height"])
            return cls_type._prepare_audio_references(self, *call_args, **call_kwargs)

        def encode_prompt(input_prompt, presentation, *call_args, **call_kwargs):
            # Phase 2 without any reference image: its references are already in place, so add at their end
            local = _generate_locals()
            if (local is not None and added["phase 1"] and not added["phase 2"] and local.get("phase_2_refs") is not None
                    and presentation is local.get("phase_2_presentation")):
                add_videos("phase 2", local, presentation, local["phase_2_visual_latents"], local["phase_2_refs"],
                           local["target_width"], local["target_height"])
            return cls_type._encode_prompt(self, input_prompt, presentation, *call_args, **call_kwargs)

        overrides = {"_add_image_reference": add_image_reference}
        if hasattr(cls_type, "_prepare_audio_references"):
            overrides["_prepare_audio_references"] = prepare_audio_references
        if hasattr(cls_type, "_encode_prompt"):
            overrides["_encode_prompt"] = encode_prompt
        self.__dict__.update(overrides)
        try:
            return original(self, *args, **kwargs)
        finally:
            for name in overrides:
                self.__dict__.pop(name, None)
            if not added["phase 1"]:
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
