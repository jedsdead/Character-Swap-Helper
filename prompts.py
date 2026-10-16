"""Prompt templates: the model card's example, and the H3 Character Swap tool's performance prompt."""

STYLE_CARD = "card"
STYLE_TOOL = "tool"
STYLE_CHOICES = [("Model card example (short)", STYLE_CARD), ("Character Swap tool (detailed)", STYLE_TOOL)]

SPEAKER_TARGET = "target"
SPEAKER_OTHER = "other"
SPEAKER_OFFSCREEN = "offscreen"
SPEAKER_NONE = "none"
SPEAKER_CHOICES = [("The replaced person speaks", SPEAKER_TARGET), ("Another person on screen speaks", SPEAKER_OTHER),
                   ("Someone off screen speaks", SPEAKER_OFFSCREEN), ("Nobody speaks", SPEAKER_NONE)]

_SPEECH = {
    SPEAKER_TARGET: "The character speaks the dialogue with mouth movement matching the source performance.",
    SPEAKER_OTHER: "Another person speaks; the character listens and reacts as in the source, without speaking.",
    SPEAKER_OFFSCREEN: "The dialogue is spoken off screen; the character listens and reacts as in the source, without speaking.",
    SPEAKER_NONE: "Nobody speaks; keep the character's mouth as in the source performance.",
}


def build(style, character, dialogue="", speaker=SPEAKER_TARGET):
    character = (character or "").strip().rstrip(".")
    dialogue = (dialogue or "").strip()
    if style == STYLE_TOOL:
        parts = ["Replace only the selected person in <Video 1> with the single character in <Picture 1>"
                 + (f": {character}." if character else "."),
                 "Keep the reference identity and costume throughout.",
                 "Match source posture, gaze, blinks, facial emotion, mouth movement, hand contacts and camera movement.",
                 _SPEECH.get(speaker, "")]
        if dialogue:
            parts.append(f'Current shot dialogue: "{dialogue}"' + ("" if dialogue[-1] in ".!?…" else "."))
        parts += ["The source audio and video determine exact timing.",
                  "Do not repeat earlier dialogue or invent words, gestures, people or camera cuts.",
                  "Retain the scene outside the person region."]
    else:
        parts = ["Replace the selected person in <Video 1> with the character in <Picture 1>"
                 + (f", {character}." if character else "."),
                 "Keep the reference character's face, hair and clothing.",
                 "Follow the source performance's pose, gaze, expression and movement.",
                 "Preserve the scene and the other people."]
        if dialogue and speaker == SPEAKER_TARGET:
            parts.append(f'The character says "{dialogue}" with mouth movement matching the source.')
        elif speaker != SPEAKER_TARGET:
            parts.append(_SPEECH.get(speaker, ""))
    return " ".join(part for part in parts if part)
