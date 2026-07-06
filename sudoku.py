#!/usr/bin/env python3
"""
Sudoku — generate, solve, and play in your terminal.

  python sudoku.py                      play a random medium puzzle
  python sudoku.py --difficulty hard    easy | medium | hard | evil
  python sudoku.py --solve <81 chars>   solve a puzzle ('.' or 0 = blank)

Backtracking solver, uniqueness-checked generator, pure standard library.
"""

__version__ = "1.1.0"

import argparse
import os
import random
import sys
import time

N = 9
BOX = 3
GIVENS = {"easy": 40, "medium": 32, "hard": 27, "evil": 23}

# ANSI
RESET = "\033[0m"
DIM = "\033[90m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"

# Highlight backgrounds (256-color, subtle greys)
BG_FOCUS = "\033[48;5;238m"
BG_PEER = "\033[48;5;235m"


def enable_ansi():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if os.name == "nt":
        os.system("")


# ---------------------------------------------------------------------------
# Core solver / generator (grid = list of 81 ints, 0 = empty)
# ---------------------------------------------------------------------------
def candidates(grid, pos):
    r, c = divmod(pos, N)
    used = set()
    for i in range(N):
        used.add(grid[r * N + i])
        used.add(grid[i * N + c])
    br, bc = (r // BOX) * BOX, (c // BOX) * BOX
    for dr in range(BOX):
        for dc in range(BOX):
            used.add(grid[(br + dr) * N + (bc + dc)])
    return [v for v in range(1, 10) if v not in used]


def find_empty(grid):
    """Return the empty cell with the fewest candidates (MRV heuristic), or None."""
    best, best_pos = 10, None
    for pos in range(81):
        if grid[pos] == 0:
            n = len(candidates(grid, pos))
            if n < best:
                best, best_pos = n, pos
                if n <= 1:
                    break
    return best_pos


def solve(grid):
    """Solve in place; return True if solved."""
    pos = find_empty(grid)
    if pos is None:
        return True
    for v in candidates(grid, pos):
        grid[pos] = v
        if solve(grid):
            return True
        grid[pos] = 0
    return False


def count_solutions(grid, limit=2):
    """Count solutions up to `limit` (used to verify uniqueness)."""
    pos = find_empty(grid)
    if pos is None:
        return 1
    total = 0
    for v in candidates(grid, pos):
        grid[pos] = v
        total += count_solutions(grid, limit)
        grid[pos] = 0
        if total >= limit:
            break
    return total


def full_grid():
    """Generate a random complete solution."""
    grid = [0] * 81
    # seed the three diagonal boxes (independent) for fast randomized fill
    for b in range(0, 9, BOX + 1):
        nums = random.sample(range(1, 10), 9)
        k = 0
        br, bc = (b // BOX) * BOX, (b % BOX) * BOX
        for dr in range(BOX):
            for dc in range(BOX):
                grid[(br + dr) * N + (bc + dc)] = nums[k]
                k += 1
    solve(grid)
    return grid


def make_puzzle(difficulty="medium"):
    """Return (puzzle, solution) with a unique solution."""
    solution = full_grid()
    puzzle = solution[:]
    target_blanks = 81 - GIVENS.get(difficulty, 32)
    cells = list(range(81))
    random.shuffle(cells)
    blanks = 0
    for pos in cells:
        if blanks >= target_blanks:
            break
        saved = puzzle[pos]
        puzzle[pos] = 0
        trial = puzzle[:]
        if count_solutions(trial) != 1:
            puzzle[pos] = saved          # removing it breaks uniqueness; keep it
        else:
            blanks += 1
    return puzzle, solution


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def is_peer(a, b):
    """True if cell `a` shares a row, column, or box with cell `b` (a != b)."""
    if a == b:
        return False
    ra, ca = divmod(a, N)
    rb, cb = divmod(b, N)
    if ra == rb or ca == cb:
        return True
    return (ra // BOX == rb // BOX) and (ca // BOX == cb // BOX)


def _cell_lines(pos, given, current, notes, red, bg):
    """Return three colored strings (visual width 5) for one cell."""
    v = current[pos]
    fg = ""
    contents = ["   ", "   ", "   "]
    if v:
        if given[pos]:
            fg = BOLD
        elif pos in red:
            fg = RED
        else:
            fg = BLUE
        contents[1] = f" {v} "
    elif notes and notes[pos]:
        fg = DIM
        s = notes[pos]
        for mr in range(3):
            contents[mr] = "".join(
                str(d) if d in s else " " for d in (mr * 3 + 1, mr * 3 + 2, mr * 3 + 3)
            )
    lines = []
    for content in contents:
        lines.append(f"{bg}{fg} {content} {RESET}")
    return lines


def render(given, current, notes=None, conflicts=frozenset(), wrong=frozenset(),
           last=None, peers_on=True):
    os.system("cls" if os.name == "nt" else "clear")
    print(f"\n  {BOLD}{CYAN}S U D O K U{RESET}\n")
    red = set(conflicts) | set(wrong)

    seg_w = 5
    box_w = seg_w * BOX  # 15
    top = "    ┌" + "┬".join(["─" * box_w] * 3) + "┐"
    mid = "    ├" + "┼".join(["─" * box_w] * 3) + "┤"
    bot = "    └" + "┴".join(["─" * box_w] * 3) + "┘"

    header = list(" " * len(top))
    for c in range(N):
        start = 5 + (c // BOX) * (box_w + 1) + (c % BOX) * seg_w
        header[start + 2] = str(c + 1)
    print("".join(header))
    print(top)

    for r in range(N):
        three = ["", "", ""]
        for c in range(N):
            pos = r * N + c
            bg = ""
            if last is not None:
                if pos == last:
                    bg = BG_FOCUS
                elif peers_on and is_peer(pos, last):
                    bg = BG_PEER
            lines = _cell_lines(pos, given, current, notes, red, bg)
            for k in range(3):
                three[k] += lines[k]
            if c % BOX == BOX - 1 and c != N - 1:
                for k in range(3):
                    three[k] += "│"
        for k in range(3):
            prefix = f"  {r + 1} " if k == 1 else "    "
            print(prefix + "│" + three[k] + "│")
        if r % BOX == BOX - 1 and r != N - 1:
            print(mid)
    print(bot)


def conflicts_in(grid):
    """Positions that violate a row/col/box constraint."""
    bad = set()
    for r in range(N):
        seen = {}
        for c in range(N):
            v = grid[r * N + c]
            if v:
                seen.setdefault(v, []).append(r * N + c)
        for v, ps in seen.items():
            if len(ps) > 1:
                bad.update(ps)
    for c in range(N):
        seen = {}
        for r in range(N):
            v = grid[r * N + c]
            if v:
                seen.setdefault(v, []).append(r * N + c)
        for v, ps in seen.items():
            if len(ps) > 1:
                bad.update(ps)
    for br in range(0, N, BOX):
        for bc in range(0, N, BOX):
            seen = {}
            for dr in range(BOX):
                for dc in range(BOX):
                    pos = (br + dr) * N + (bc + dc)
                    v = grid[pos]
                    if v:
                        seen.setdefault(v, []).append(pos)
            for v, ps in seen.items():
                if len(ps) > 1:
                    bad.update(ps)
    return bad


def parse_grid(text):
    text = text.strip().replace(".", "0")
    digits = [int(ch) for ch in text if ch.isdigit()]
    if len(digits) != 81:
        raise ValueError(f"expected 81 cells, got {len(digits)}")
    return digits


# ---------------------------------------------------------------------------
# Interactive play
# ---------------------------------------------------------------------------
def play(difficulty):
    puzzle, solution = make_puzzle(difficulty)
    given = [1 if v else 0 for v in puzzle]
    current = puzzle[:]
    notes = [set() for _ in range(81)]
    history = []          # stack of (pos, prev_value, prev_notes) for undo
    wrong = set()         # positions flagged by the last `check`
    mistakes = 0
    last = None           # last-edited cell, highlighted
    peers_on = True
    start = time.monotonic()
    help_msg = (
        f"{DIM}place r c v · clear r c 0 · note n r c v · u undo · "
        f"check · peers · h hint · s solve · new · q quit{RESET}"
    )
    msg = help_msg

    while True:
        bad = conflicts_in(current)
        render(given, current, notes=notes, conflicts=bad, wrong=wrong,
               last=last, peers_on=peers_on)
        filled = sum(1 for v in current if v)
        mm, ss = divmod(int(time.monotonic() - start), 60)
        pstate = "on" if peers_on else "off"
        print(f"\n  time {mm:02d}:{ss:02d}   mistakes {mistakes}   "
              f"{filled}/81 filled   difficulty: {difficulty}   peers {pstate}")
        if current == solution:
            print(f"\n  {GREEN}{BOLD}Solved in {mm:02d}:{ss:02d} with "
                  f"{mistakes} mistake(s). Nicely done.{RESET}\n")
            return
        print("  " + msg)
        msg = help_msg
        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {DIM}bye{RESET}\n")
            return

        if not raw:
            continue
        if raw in ("q", "quit"):
            print(f"\n  {DIM}bye{RESET}\n")
            return
        if raw in ("n", "new"):
            return play(difficulty)
        if raw in ("s", "solve"):
            current = solution[:]
            render(given, current, notes=notes, last=last, peers_on=peers_on)
            print(f"\n  {YELLOW}Here's the solution.{RESET}\n")
            return
        if raw in ("u", "undo"):
            if history:
                pos, prev_v, prev_n = history.pop()
                current[pos] = prev_v
                notes[pos] = prev_n
                wrong = set()
                last = pos
                msg = f"{DIM}undid R{pos // N + 1} C{pos % N + 1}{RESET}"
            else:
                msg = f"{DIM}nothing to undo{RESET}"
            continue
        if raw == "check":
            wrong = {i for i in range(81)
                     if current[i] and not given[i] and current[i] != solution[i]}
            if wrong:
                word = "entry" if len(wrong) == 1 else "entries"
                msg = f"{RED}{len(wrong)} wrong {word} highlighted.{RESET}"
            else:
                msg = f"{GREEN}no wrong entries so far.{RESET}"
            continue
        if raw in ("p", "peers"):
            peers_on = not peers_on
            continue
        if raw in ("h", "hint"):
            blanks = [i for i in range(81) if current[i] == 0]
            if blanks:
                pos = random.choice(blanks)
                history.append((pos, current[pos], set(notes[pos])))
                current[pos] = solution[pos]
                notes[pos] = set()
                wrong = set()
                last = pos
                msg = f"{GREEN}hint: filled R{pos // N + 1} C{pos % N + 1}{RESET}"
            continue

        parts = raw.split()

        # note toggle: n r c v
        if len(parts) == 4 and parts[0] == "n" and all(p.isdigit() for p in parts[1:]):
            r, c, v = (int(p) for p in parts[1:])
            if 1 <= r <= 9 and 1 <= c <= 9 and 1 <= v <= 9:
                pos = (r - 1) * N + (c - 1)
                if given[pos] or current[pos]:
                    msg = f"{RED}R{r} C{c} is filled — clear it before noting.{RESET}"
                else:
                    if v in notes[pos]:
                        notes[pos].discard(v)
                    else:
                        notes[pos].add(v)
                    last = pos
                continue

        # place / clear: r c v
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            r, c, v = (int(p) for p in parts)
            if 1 <= r <= 9 and 1 <= c <= 9 and 0 <= v <= 9:
                pos = (r - 1) * N + (c - 1)
                if given[pos]:
                    msg = f"{RED}R{r} C{c} is a given — can't change it.{RESET}"
                else:
                    history.append((pos, current[pos], set(notes[pos])))
                    current[pos] = v
                    notes[pos] = set()
                    wrong = set()
                    last = pos
                    if v and v != solution[pos]:
                        mistakes += 1
                        msg = f"{RED}R{r} C{c} = {v} looks wrong.{RESET}"
                    else:
                        msg = ""
                continue

        msg = f"{RED}didn't understand that. try: r c v  or  n r c v{RESET}"


def main():
    enable_ansi()
    ap = argparse.ArgumentParser(description="Generate, solve, and play Sudoku.")
    ap.add_argument("--difficulty", choices=list(GIVENS), default="medium")
    ap.add_argument("--solve", metavar="PUZZLE", help="solve an 81-char puzzle and exit")
    args = ap.parse_args()

    if args.solve:
        grid = parse_grid(args.solve)
        given = [1 if v else 0 for v in grid]
        work = grid[:]
        if solve(work):
            render(given, work)
            print(f"\n  {GREEN}Solved.{RESET}  {''.join(map(str, work))}\n")
        else:
            print(f"\n  {RED}No solution.{RESET}\n")
        return

    play(args.difficulty)


if __name__ == "__main__":
    main()
