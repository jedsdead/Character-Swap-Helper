"""H3 Character Swap: an inline section of the main generation page for MiniMax H3 Ref2VA models.

It only adds what the normal generator can't provide for the Character Swap LoRA's recipe:
* a switch that gives the control video to H3 as reference <Video 1> during masked video-to-video (see swap_hook);
* a prompt builder in the wording of the LoRA's model card or of its author's tool.
"""

import gradio as gr

from shared.utils.plugins import WAN2GPPlugin

from . import prompts
from . import settings
from . import swap_hook
from .swap_hook import LOG_PREFIX

REF2VA_ARCHITECTURES = ("minimax_h3_ref2va_pruned", "minimax_h3_ref2va")
INSERT_TARGETS = ("mask_expand", "video_mask", "guidance_phases_row")  # first one found in the page

SETUP = """**Character Swap recipe** (the LoRA author's tool), in the settings above and below:
- **Reference Images:** the character image (it is `<Picture 1>`)
- **Reference / Control Video:** *Denoise Control Video (Video-to-Video Edit)* with your clip
- **Video Mask:** the person to replace, white, *masked area* regenerated (Magic Mask with `person`, or MatAnyone); **Mask Expand** about 44 (≈ 64 px)
- **Audio:** *Generate Video based on Reference / Control Video + its Audio Track (Soundtrack Kept)*
- **LoRA:** the Character Swap LoRA (V1.5) at 1.0, with 1 guidance phase
- Mask Denoising Mode: *Grouped Rows* (the default). Up to about 15 s, one window."""


def _wgp():
    import sys
    main = sys.modules.get("__main__")
    if main is not None and isinstance(getattr(main, "models_def", None), dict) and callable(getattr(main, "get_model_def", None)):
        return main
    for module in list(sys.modules.values()):
        if module is not None and isinstance(getattr(module, "models_def", None), dict) and callable(getattr(module, "get_model_def", None)):
            return module
    return None


def _call(name, *args):
    function = getattr(_wgp(), name, None)
    try:
        return function(*args) if callable(function) else None
    except Exception:
        return None


def _is_ref2va(model_type):
    if not model_type:
        return False
    base = _call("get_base_model_type", model_type) or ""
    model_def = _call("get_model_def", model_type) or {}
    return str(base) in REF2VA_ARCHITECTURES or str(model_def.get("architecture", "")) in REF2VA_ARCHITECTURES


class H3CharacterSwapPlugin(WAN2GPPlugin):
    def __init__(self):
        super().__init__()
        self.name = "H3 Character Swap"
        self.version = "0.1"
        self.description = "Character Swap LoRA recipe in the main page: the control video as <Video 1> in masked video-to-video, and a prompt builder."
        self._ui_built = False
        settings.load()

    def setup_ui(self):
        for component_id in ("state", "model_choice_target", "refresh_form_trigger", "prompt", *INSERT_TARGETS):
            self.request_component(component_id)
        self._install()

    @staticmethod
    def _install():
        try:
            swap_hook.install()
        except Exception as error:
            print(f"{LOG_PREFIX} could not hook MiniMax H3: {error!r}")

    def on_model_change(self, state, model_type):
        self._install()

    def post_ui_setup(self, components):
        if self._ui_built:  # post_ui_setup also runs for the hidden Edit tab: the section lives in the main page only
            return {}
        target = next((name for name in INSERT_TARGETS if components.get(name) is not None), None)
        state = components.get("state")
        if target is None or state is None:
            print(f"{LOG_PREFIX} main page components not found, Character Swap section not added")
            return {}
        self._ui_built = True
        self._install()
        prompt_box = components.get("prompt")
        model_choice_target = components.get("model_choice_target")
        refresh_form_trigger = components.get("refresh_form_trigger")
        initial_state = state.value if isinstance(state.value, dict) else {}
        initial_visible = _is_ref2va(initial_state.get("model_type"))

        def build_section():
            with gr.Accordion("H3 Character Swap", open=settings.get()["enabled"], visible=initial_visible,
                              elem_id="h3_character_swap_section") as section:
                enabled = gr.Checkbox(value=settings.get()["enabled"],
                                      label="Character Swap: also give the control video to H3 as <Video 1>",
                                      info="With Denoise Control Video, a Video Mask and the character as Reference Image, the untouched "
                                           "clip is shown to H3 as <Video 1> so the regenerated person follows the original performance. "
                                           "Read when each generation starts; switch it off for other masked edits.")
                gr.Markdown(SETUP)
                with gr.Accordion("Prompt builder", open=False, visible=prompt_box is not None):
                    with gr.Row():
                        description = gr.Textbox(label="Character description", scale=3,
                                                 placeholder="e.g. a woman with short red hair, freckles and a green wool coat")
                        speaker = gr.Dropdown(choices=prompts.SPEAKER_CHOICES, value=prompts.SPEAKER_TARGET, label="Who speaks", scale=2)
                    dialogue = gr.Textbox(label="Dialogue in the clip (optional)")
                    with gr.Row():
                        style = gr.Dropdown(choices=prompts.STYLE_CHOICES, value=prompts.STYLE_TOOL, label="Prompt style", scale=3)
                        insert = gr.Button("Replace the prompt", scale=1)

            def store(value):
                settings.set_value("enabled", bool(value))
                self._install()
                print(f"{LOG_PREFIX} Character Swap {'on' if value else 'off'}")

            enabled.change(store, inputs=enabled, outputs=None, show_progress="hidden", queue=False)
            if prompt_box is not None:
                insert.click(prompts.build, inputs=[style, description, dialogue, speaker], outputs=prompt_box, show_progress="hidden")
            if model_choice_target is not None:
                model_choice_target.change(
                    lambda target_value: gr.update(visible=_is_ref2va(_call("_model_choice_target_model_type", target_value) if target_value else None)),
                    inputs=model_choice_target, outputs=section, show_progress="hidden")
            if refresh_form_trigger is not None:
                refresh_form_trigger.change(
                    lambda state_value: gr.update(visible=_is_ref2va(_call("get_state_model_type", state_value) if isinstance(state_value, dict) else None)),
                    inputs=state, outputs=section, show_progress="hidden")
            return section

        self.insert_after(target, build_section)
        print(f"{LOG_PREFIX} section added after '{target}' (Character Swap {'on' if settings.get()['enabled'] else 'off'})")
        return {}
