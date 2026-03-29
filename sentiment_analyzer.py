
import re
from dataclasses import dataclass, field

@dataclass
class SentimentResult:
    score: float = 0.0
    label: str = "neutral"
    flags: list = field(default_factory=list)
    brief_note: str = "neutral"


class SentimentAnalyzer:

    POSITIVE = frozenset([
        "happy", "great", "good", "awesome", "wonderful", "excited", "grateful",
        "calm", "peaceful", "hopeful", "proud", "confident", "relaxed", "joyful",
        "motivated", "energetic", "content", "loved", "supported", "accomplished",
    ])

    NEGATIVE = frozenset([
        "sad", "anxious", "stressed", "overwhelmed", "tired", "frustrated",
        "lonely", "angry", "worried", "exhausted", "depressed", "hopeless",
        "nervous", "afraid", "hurt", "lost", "empty", "numb", "burned",
    ])

    CONCERNING = frozenset([
        "hopeless", "worthless", "give up", "can't go on", "ending it",
        "no point", "burden", "disappear", "harm", "hurt myself",
        "don't want to be here", "no way out",
    ])

    def analyze(self, text: str) -> SentimentResult:
        if not text or not isinstance(text, str):
            return SentimentResult()

        words = re.split(r"\W+", text.lower())
        pos = []
        neg = []

        NEGATIONS = {"not", "no", "never", "don't", "doesn't",
                     "didn't", "won't", "can't", "cannot"}

        for i, word in enumerate(words):
            window  = words[max(0, i-3):i]
            negated = any(n in window for n in NEGATIONS)

            if word in self.POSITIVE:
                if negated:
                    neg.append(f"not {word}")
                else:
                    pos.append(word)

            elif word in self.NEGATIVE:
                if negated:
                    pos.append(f"not {word}")
                else:
                    neg.append(word)

        flags = [p for p in self.CONCERNING if p in text.lower()]
        total = len(pos) + len(neg)
        score = 0.0 if total == 0 else round((len(pos) - len(neg)) / total, 2)
        brief = ", ".join((pos + neg)[:3]) or "neutral"
        label = "positive" if score > 0.3 else ("negative" if score < -0.3 else "neutral")

        return SentimentResult(score=score, label=label, flags=flags, brief_note=brief)

    @staticmethod
    def should_escalate(scores: list, flags: list = None) -> bool:
        if flags:
            return True
        return sum(1 for s in scores if s <= 1) >= 3
