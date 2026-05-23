#!/usr/bin/env python3
"""Generate interlocking crossword puzzles for the Brooklyn Borough History game.

Output matches the data format consumed by crossword.html:
  PUZZLES = [ {title, size (rows), size_c (cols), grid[[{letter,num}]], across[...], down[...]} ]
Each across/down entry: {num, word, clue, row, col, len, dir}.
Black squares use letter "#".
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "brooklyn_history_questions.json")


def load_words():
    with open(SRC) as f:
        data = json.load(f)
    out = []
    for q in data["questions"]:
        out.append({
            "word": q["answer"].upper(),
            "clue": q["crossword_clue"],
            "cb": q["cb"],
        })
    return out


class Grid:
    """Simple crossword layout engine: greedy interlock on shared letters."""

    def __init__(self):
        self.cells = {}  # (r,c) -> letter
        self.placements = []  # (word, r, c, dir)

    def bounds(self):
        rs = [r for (r, c) in self.cells]
        cs = [c for (r, c) in self.cells]
        return min(rs), max(rs), min(cs), max(cs)

    def can_place(self, word, r, c, d):
        dr, dc = (0, 1) if d == "A" else (1, 0)
        # cell before start and after end must be empty (word boundaries)
        before = (r - dr, c - dc)
        after = (r + dr * len(word), c + dc * len(word))
        if before in self.cells:
            return False
        if after in self.cells:
            return False
        crossed = False
        for i, ch in enumerate(word):
            rr, cc = r + dr * i, c + dc * i
            cur = self.cells.get((rr, cc))
            if cur is not None:
                if cur != ch:
                    return False
                crossed = True
            else:
                # perpendicular neighbors must be empty unless this is the crossing cell
                if d == "A":
                    if (rr - 1, cc) in self.cells or (rr + 1, cc) in self.cells:
                        return False
                else:
                    if (rr, cc - 1) in self.cells or (rr, cc + 1) in self.cells:
                        return False
        return crossed if self.placements else True

    def place(self, word, r, c, d):
        dr, dc = (0, 1) if d == "A" else (1, 0)
        for i, ch in enumerate(word):
            self.cells[(r + dr * i, c + dc * i)] = ch
        self.placements.append((word, r, c, d))

    def try_add(self, word):
        if not self.placements:
            self.place(word, 0, 0, "A")
            return True
        best = None
        for i, ch in enumerate(word):
            for (rr, cc), letter in list(self.cells.items()):
                if letter != ch:
                    continue
                # place vertically so it crosses an across letter, or horizontally
                for d in ("D", "A"):
                    dr, dc = (0, 1) if d == "A" else (1, 0)
                    r0, c0 = rr - dr * i, cc - dc * i
                    if self.can_place(word, r0, c0, d):
                        # score: prefer compact grids
                        minr, maxr, minc, maxc = self.bounds()
                        score = (maxr - minr) + (maxc - minc)
                        if best is None or score < best[0]:
                            best = (score, word, r0, c0, d)
        if best:
            _, w, r0, c0, d = best
            self.place(w, r0, c0, d)
            return True
        return False


def _layout(words, order):
    g = Grid()
    placed = []
    remaining = [words[i] for i in order]
    progress = True
    while remaining and progress:
        progress = False
        for w in list(remaining):
            if g.try_add(w["word"]):
                placed.append(w)
                remaining.remove(w)
                progress = True
    minr, maxr, minc, maxc = g.bounds()
    span = (maxr - minr) + (maxc - minc)
    return g, placed, span


def build_puzzle(words, title):
    import itertools
    import random
    # Try the longest-first seed plus many random permutations; keep the
    # layout that places every word in the most compact bounding box.
    best = None
    seeds = [sorted(range(len(words)), key=lambda i: -len(words[i]["word"]))]
    rng = random.Random(20260523)
    for _ in range(400):
        perm = list(range(len(words)))
        rng.shuffle(perm)
        seeds.append(perm)
    for order in seeds:
        g, placed, span = _layout(words, order)
        if len(placed) == len(words):
            if best is None or span < best[2]:
                best = (g, placed, span)
    if best is None:
        # fall back to whatever placed the most words
        for order in seeds:
            g, placed, span = _layout(words, order)
            if best is None or len(placed) > len(best[1]):
                best = (g, placed, span)
    g, placed, _ = best
    # normalize coordinates to 0-based positive grid
    minr, maxr, minc, maxc = g.bounds()
    rows = maxr - minr + 1
    cols = maxc - minc + 1
    grid = [[{"letter": "#", "num": None} for _ in range(cols)] for _ in range(rows)]
    for (rc, ch) in g.cells.items():
        r, c = rc[0] - minr, rc[1] - minc
        grid[r][c]["letter"] = ch
    # build across/down entries
    norm = []
    clue_for = {w["word"]: w["clue"] for w in words}
    for (word, r, c, d) in g.placements:
        norm.append((word, r - minr, c - minc, d))
    # assign numbers based on cell order (top-to-bottom, left-to-right)
    starts = {}
    for (word, r, c, d) in norm:
        starts[(r, c)] = True
    ordered = sorted(starts.keys())
    num_at = {}
    n = 1
    for (r, c) in ordered:
        num_at[(r, c)] = n
        grid[r][c]["num"] = n
        n += 1
    across, down = [], []
    for (word, r, c, d) in norm:
        entry = {
            "num": num_at[(r, c)],
            "word": word,
            "clue": clue_for[word],
            "row": r, "col": c, "len": len(word), "dir": d,
        }
        (across if d == "A" else down).append(entry)
    across.sort(key=lambda e: e["num"])
    down.sort(key=lambda e: e["num"])
    return {
        "title": title,
        "size": rows,
        "size_c": cols,
        "grid": grid,
        "across": across,
        "down": down,
    }, placed


def main():
    words = load_words()
    by_word = {w["word"]: w for w in words}
    # Hand-grouped so each puzzle's words share crossing letters and interlock.
    groups = [
        ["WILLIAMSBURG", "GOWANUS", "BREWING", "CONNECTICUT", "EBBETS", "BENSON"],
        ["BUSHTERMINAL", "OCEANPARKWAY", "HEIGHTS", "STUYVESANT", "LEFFERTS", "KINGS"],
        ["VERRAZZANO", "BROWNSVILLE", "SHEEPSHEAD", "CANARSIE", "CYCLONE", "FLATBUSH"],
    ]
    titles = [
        "Puzzle 1 \u2014 North & Central Brooklyn",
        "Puzzle 2 \u2014 The Waterfront & Heights",
        "Puzzle 3 \u2014 South Brooklyn & the Shore",
    ]
    puzzles = []
    for names, title in zip(groups, titles):
        chunk = [by_word[n] for n in names]
        pz, placed = build_puzzle(chunk, title)
        if len(placed) != len(chunk):
            missing = [w["word"] for w in chunk if w not in placed]
            raise SystemExit(f"Failed to place words in {title}: {missing}")
        puzzles.append(pz)
    out = json.dumps(puzzles, ensure_ascii=False)
    out_path = os.path.join(HERE, "brooklyn_crossword_puzzles.json")
    with open(out_path, "w") as f:
        f.write(out)
    print(f"Wrote {out_path} ({len(out)} bytes), {len(puzzles)} puzzles")
    for pz in puzzles:
        print(f"  {pz['title']}: {pz['size']}x{pz['size_c']}, "
              f"{len(pz['across'])}A {len(pz['down'])}D")


if __name__ == "__main__":
    main()
