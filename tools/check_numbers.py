#!/usr/bin/env python3
"""台本の say（読み上げ）と show（表示）の数字が食い違っていないか照合する。

決まり（docs/script-rules.md）:
- say の数字は1桁ずつひらがな（いち、に、さん、よん、ご、ろく、なな、はち、きゅう、ゼロ）
- 小数点は「てん」、大きな単位は「おく」「まん」を後ろに付ける
- say に位取りの漢数字とアラビア数字は書かない

使い方: python3 tools/check_numbers.py episodes/<日付>-ja.json
警告があれば終了コード 1。警告は「人の目で確認する合図」であり、
言い回しによっては正しい行にも出ることがある。
"""
import json
import re
import sys

FW = str.maketrans("０１２３４５６７８９．，", "0123456789.,")

KANJI_DIGIT = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
SMALL_UNIT = {"十": 10, "百": 100, "千": 1000}
BIG_UNIT_KANJI = {"万": 4, "億": 8, "兆": 12}
KANJI_NUM_RE = re.compile(r"[〇一二三四五六七八九十百千万億兆]+")

SAY_DIGITS = {
    "ゼロ": "0", "れい": "0",
    "いち": "1", "に": "2", "さん": "3", "よん": "4", "し": "4",
    "ご": "5", "ろく": "6", "なな": "7", "しち": "7", "はち": "8", "きゅう": "9",
}
SAY_WORDS = sorted(SAY_DIGITS, key=len, reverse=True)
# say の中で数字ではない言い回し（桁読みと誤認しやすいもの）
SAY_MASKS = ["きゅうに"]  # 急に
# say の数字の直後に来る単位（これが付く1桁の数字も数字として扱う）
SAY_UNITS = (
    "パーセント", "ねん", "がつ", "にち", "じ", "ふん", "びょう",
    "えん", "ドル", "おく", "まん", "けん", "こ", "にん", "ばい",
    "だい", "さつ", "まい", "かい", "ばん", "もん", "しゃ", "くみ",
)


def parse_kanji_num(s):
    """漢数字を値にする。単位のない数字だけの並び（二〇二八）は桁の並びとして読む。"""
    if all(ch in KANJI_DIGIT for ch in s) and len(s) >= 2:
        return int("".join(str(KANJI_DIGIT[ch]) for ch in s))
    total, section, num, seen = 0, 0, 0, False
    big = {"万": 10 ** 4, "億": 10 ** 8, "兆": 10 ** 12}
    for ch in s:
        if ch in KANJI_DIGIT:
            num = KANJI_DIGIT[ch]
            seen = True
        elif ch in SMALL_UNIT:
            section += (num if num else 1) * SMALL_UNIT[ch]
            num = 0
            seen = True
        elif ch in big:
            section += num
            total += (section if section else 1) * big[ch]
            section, num = 0, 0
            seen = True
        else:
            return None
    if not seen:
        return None
    return total + section + num


def show_numbers(text):
    """show から数字トークン（文字列）を順に取り出す。

    アラビア数字＋万・億・兆は1つの数字として展開する（1150億 → 115000000000）。
    漢数字は値に直す（二万四千 → 24000）。
    """
    text = text.translate(FW).replace("万が一", "まんがいち")
    tokens = []
    pattern = re.compile(
        r"\d[\d,]*(?:\.\d+)?[万億兆]?|[〇一二三四五六七八九十百千万億兆]+"
    )
    for m in pattern.finditer(text):
        raw = m.group(0)
        if raw[0].isdigit():
            unit = raw[-1] if raw[-1] in BIG_UNIT_KANJI else None
            num = raw[:-1] if unit else raw
            num = num.replace(",", "")
            if unit and "." not in num:
                tokens.append(num + "0" * BIG_UNIT_KANJI[unit])
            else:
                tokens.append(num)
        else:
            val = parse_kanji_num(raw)
            if val is not None:
                tokens.append(str(val))
    return tokens


def _match_digit_word(text, i):
    for w in SAY_WORDS:
        if text.startswith(w, i):
            return w, SAY_DIGITS[w]
    return None, None


def say_number_tokens(text):
    """say から数字トークンを順に取り出す。

    桁読み（ひらがな）として認めるのは「2語以上の桁読み」か「単位が直後に付く
    桁読み」だけ。これで『だし』の『し』や『おなじ』の『に』の誤認を避ける。
    おく・まんはゼロを足して展開する。
    日付の月日は例外で、漢数字のまま読む決まりなので、月・日の直前の
    漢数字も数字として取り出す。
    """
    for mask in SAY_MASKS:
        text = text.replace(mask, "＠" * len(mask))
    found = []  # (位置, トークン)
    for m in KANJI_NUM_RE.finditer(text):
        if m.end() < len(text) and text[m.end()] in "月日":
            val = parse_kanji_num(m.group(0))
            if val is not None:
                found.append((m.start(), str(val)))
    i, n = 0, len(text)
    while i < n:
        word, digit = _match_digit_word(text, i)
        if word is None:
            i += 1
            continue
        # ここから数字の並びをできるだけ長く読む
        digits = [digit]
        j = i + len(word)
        has_dot = False
        while j < n:
            if text.startswith("てん", j) and not has_dot:
                w2, d2 = _match_digit_word(text, j + 2)
                if w2 is None:
                    break
                digits.append(".")
                has_dot = True
                j += 2
                continue
            # 「にち」「にん」は単位の始まり。数字の「に」と誤って続けない
            if text.startswith("にち", j) or text.startswith("にん", j):
                break
            w2, d2 = _match_digit_word(text, j)
            if w2 is None:
                break
            digits.append(d2)
            j += len(w2)
        tail = text[j:]
        unit = next((u for u in SAY_UNITS if tail.startswith(u)), None)
        word_count = sum(1 for d in digits if d != ".")
        if word_count >= 2 or unit is not None:
            s = "".join(digits)
            if tail.startswith("おく"):
                s += "0" * 8
            elif tail.startswith("まん"):
                s += "0" * 4
            found.append((i, s))
            i = j
        else:
            i += len(word)
    found.sort(key=lambda p: p[0])
    return [tok for _, tok in found]


def kanji_leftovers_in_say(text):
    """say に残っている位取りの漢数字（新しい決まりでは禁止）を拾う。

    日付の月日（直後が月・日の漢数字）は例外として許可する。
    """
    bad = []
    for m in KANJI_NUM_RE.finditer(text):
        if m.end() < len(text) and text[m.end()] in "月日":
            continue
        raw = m.group(0)
        if any(ch in "十百千億" for ch in raw) or len(raw) >= 2:
            bad.append(raw)
    return bad


def iter_lines(ep):
    for part_name in ("opening", "closing"):
        for i, line in enumerate(ep.get(part_name) or []):
            yield f"{part_name}[{i}]", line
    for ni, news in enumerate(ep.get("news") or []):
        for i, line in enumerate(news.get("lines") or []):
            yield f"news[{ni}].lines[{i}]", line


def main():
    if len(sys.argv) != 2:
        print("usage: check_numbers.py <episode.json>")
        return 2
    ep = json.load(open(sys.argv[1]))
    warnings = 0
    checked = 0
    for where, line in iter_lines(ep):
        say, show = line.get("say", ""), line.get("show", "")
        checked += 1
        problems = []
        if re.search(r"[0-9０-９]", say):
            problems.append("say にアラビア数字がある")
        leftovers = kanji_leftovers_in_say(say)
        if leftovers:
            problems.append(f"say に位取りの漢数字が残っている: {'、'.join(leftovers)}")
        s_nums, h_nums = say_number_tokens(say), show_numbers(show)
        if s_nums != h_nums:
            problems.append(f"数字の並びが食い違う: say={s_nums} show={h_nums}")
        if problems:
            warnings += 1
            print(f"[警告] {where}")
            print(f"  say : {say}")
            print(f"  show: {show}")
            for p in problems:
                print(f"  - {p}")
    print(f"\n{checked} 行を確認、警告 {warnings} 件")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
