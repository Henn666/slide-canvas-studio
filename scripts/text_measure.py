#!/usr/bin/env python3
"""
text_measure.py
單一職責：CJK/拉丁混排文字寬度估算與智慧斷行引擎，
支援標點避頭尾（禁則處理）、75% 行寬優先於「，。；：」斷句、數字與 % 單位黏合，
確保原生 PPTX 文字框擁有編輯室級的均勻斷行與精準高度預估。
"""
import math
import unicodedata
from typing import List, Tuple

_CLOSING_PUNCTUATION = frozenset(",.;:!?)]}、，。；：！？）》」』】”’")
_OPENING_PUNCTUATION = frozenset("([{（《「『【“‘")
_NO_LINE_START = _CLOSING_PUNCTUATION | frozenset("ー々ゝゞヽヾ・")
_PREFERRED_BREAK_PUNCTUATION = frozenset("，。；：")
_PREFERRED_BREAK_MIN_FILL = 0.75
_LATIN_TOKEN_CONNECTORS = frozenset("'’._:/+%@#-")
_NUMBER_SUFFIXES = frozenset("%‰°")


def measure_text_width_cm(text: str, font_size_pt: float, bold: bool = False) -> float:
    """Estimate rendered width in cm for mixed CJK + Latin text at font_size_pt."""
    if not text:
        return 0.0
    em_cm = font_size_pt * 0.0352778
    bold_factor = 1.05 if bold else 1.0
    total_units = 0.0
    for ch in text:
        if ch == "\n":
            continue
        if ch == " ":
            total_units += 0.28
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            total_units += 1.02
        elif ch.isupper():
            total_units += 0.68
        elif ch.isdigit():
            total_units += 0.56
        elif ch in "ilIjtf.,:;'|!":
            total_units += 0.30
        elif ch in "mwMW@#%&":
            total_units += 0.82
        else:
            total_units += 0.53
    # Add small headroom (4%) to guard against OS font metric variance
    return round(total_units * em_cm * bold_factor * 1.04, 4)


def _is_latin_word_char(ch: str) -> bool:
    return ch.isdigit() or (ch.isalpha() and unicodedata.east_asian_width(ch) not in ("W", "F"))


def _lexical_units(paragraph: str) -> List[str]:
    """Tokenize paragraph keeping English words, numbers+units, and CJK single chars intact."""
    chars = list(" ".join(paragraph.split()))
    units: List[str] = []
    pending_space = False
    i = 0
    n = len(chars)
    while i < n:
        ch = chars[i]
        if ch.isspace():
            pending_space = bool(units)
            i += 1
            continue
        end = i + 1
        if _is_latin_word_char(ch):
            while end < n:
                nxt = chars[end]
                if _is_latin_word_char(nxt):
                    end += 1
                elif nxt in _LATIN_TOKEN_CONNECTORS and end + 1 < n and _is_latin_word_char(chars[end + 1]):
                    end += 2
                elif nxt in _NUMBER_SUFFIXES and chars[end - 1].isdigit():
                    end += 1
                else:
                    break
        prefix = " " if pending_space else ""
        units.append(prefix + "".join(chars[i:end]))
        pending_space = False
        i = end
    return units


def _protected_units(paragraph: str) -> List[str]:
    """Attach禁則 (forbidden line-start/end) punctuation to adjacent units."""
    units = _lexical_units(paragraph)
    protected: List[str] = []
    for unit in units:
        content = unit.lstrip()
        if not content:
            continue
        if protected and (
            content[0] in _NO_LINE_START
            or protected[-1].rstrip()[-1] in _OPENING_PUNCTUATION
        ):
            protected[-1] += unit
        else:
            protected.append(unit)
    return protected


def _preferred_break_after(text: str) -> bool:
    tail = text.rstrip()
    while tail and tail[-1] in _CLOSING_PUNCTUATION and tail[-1] not in _PREFERRED_BREAK_PUNCTUATION:
        tail = tail[:-1]
    return bool(tail) and tail[-1] in _PREFERRED_BREAK_PUNCTUATION


def wrap_paragraph(
    paragraph: str,
    max_width_cm: float,
    font_size_pt: float,
    bold: bool = False,
) -> List[str]:
    """Wrap a single paragraph with CJK punctuation rules and 75% clause-break preference."""
    units = _protected_units(paragraph)
    if not units:
        return [""]

    lines: List[str] = []
    start = 0
    while start < len(units):
        fit_widths = {}
        preferred_end = None
        end = start
        while end < len(units):
            cand_end = end + 1
            cand_str = "".join(units[start:cand_end]).lstrip()
            cand_w = measure_text_width_cm(cand_str, font_size_pt, bold=bold)
            if cand_w > max_width_cm and cand_end > start + 1:
                break
            fit_widths[cand_end] = cand_w
            if _preferred_break_after(cand_str):
                preferred_end = cand_end
            end = cand_end
            if cand_w > max_width_cm:
                break

        if end == len(units):
            lines.append("".join(units[start:end]).lstrip())
            break

        chosen_end = end
        if preferred_end is not None and preferred_end > start:
            pref_w = fit_widths.get(preferred_end, 0.0)
            if pref_w >= max_width_cm * _PREFERRED_BREAK_MIN_FILL:
                chosen_end = preferred_end

        lines.append("".join(units[start:chosen_end]).lstrip())
        start = chosen_end
    return lines


def wrap_and_measure_text(
    text: str,
    box_w_cm: float,
    font_size_pt: float,
    bold: bool = False,
    line_height: float = 1.42,
    pad_h_cm: float = 0.25,
    pad_v_cm: float = 0.16,
) -> Tuple[str, float, int]:
    """Return (wrapped_text, estimated_height_cm, line_count)."""
    if not text:
        h = round(font_size_pt * 0.0352778 * line_height + pad_v_cm, 3)
        return "", h, 1

    usable_w = max(1.0, box_w_cm - pad_h_cm)
    all_lines: List[str] = []
    for para in str(text).split("\n"):
        if not para.strip():
            all_lines.append("")
        else:
            all_lines.extend(wrap_paragraph(para, usable_w, font_size_pt, bold=bold))

    em_cm = font_size_pt * 0.0352778
    total_h = round(max(1, len(all_lines)) * em_cm * line_height + pad_v_cm, 3)
    return "\n".join(all_lines), total_h, len(all_lines)
