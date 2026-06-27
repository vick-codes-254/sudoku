#!/usr/bin/env python3
"""
Sudoku — generate, solve, and play in your terminal.

  python sudoku.py                      play a random medium puzzle
  python sudoku.py --difficulty hard    easy | medium | hard | evil
  python sudoku.py --solve <81 chars>   solve a puzzle ('.' or 0 = blank)

Backtracking solver, uniqueness-checked generator, pure standard library.
"""

import argparse
import os
import random
import sys

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
def render(puzzle, given, current, cursor=None, conflicts=frozenset()):
    os.system("cls" if os.name == "nt" else "clear")
    print(f"\n  {BOLD}{CYAN}S U D O K U{RESET}\n")
    print("      " + "   ".join(str(c + 1) for c in range(N)))
    top = "    +" + "+".join(["-------"] * 3) + "+"
    for r in range(N):
        if r % BOX == 0:
            print(top)
        row = f"  {r + 1} |"
        for c in range(N):
            pos = r * N + c
            v = current[pos]
            if v == 0:
                cell = " ."
            else:
                if given[pos]:
                    cell = f" {BOLD}{v}{RESET}"
                elif pos in conflicts:
                    cell = f" {RED}{v}{RESET}"
                else:
                    cell = f" {BLUE}{v}{RESET}"
            if cursor == pos:
                cell = f"{YELLOW}[{cell.strip()}]{RESET}"[:]
                row += cell.rjust(2)
            else:
                row += cell + " "
            if c % BOX == BOX - 1:
                row += "|"
        print(row)
    print(top)


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
    msg = f"{DIM}place: r c v  (e.g. 3 5 7) · clear: r c 0 · h hint · s solve · n new · q quit{RESET}"

    while True:
        bad = conflicts_in(current)
        render(puzzle, given, current, conflicts=bad)
        filled = sum(1 for v in current if v)
        print(f"\n  {filled}/81 filled   difficulty: {difficulty}")
        if current == solution:
            print(f"\n  {GREEN}{BOLD}Solved! Nicely done.{RESET}\n")
            return
        print("  " + msg)
        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {DIM}bye{RESET}\n")
            return

        if raw in ("q", "quit"):
            print(f"\n  {DIM}bye{RESET}\n")
            return
        if raw in ("n", "new"):
            return play(difficulty)
        if raw in ("s", "solve"):
            current = solution[:]
            render(puzzle, given, current)
            print(f"\n  {YELLOW}Here's the solution.{RESET}\n")
            return
        if raw in ("h", "hint"):
            blanks = [i for i in range(81) if current[i] == 0]
            if blanks:
                pos = random.choice(blanks)
                current[pos] = solution[pos]
                msg = f"{GREEN}hint: filled R{pos // N + 1} C{pos % N + 1}{RESET}"
            continue

        parts = raw.split()
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            r, c, v = (int(p) for p in parts)
            if 1 <= r <= 9 and 1 <= c <= 9 and 0 <= v <= 9:
                pos = (r - 1) * N + (c - 1)
                if given[pos]:
                    msg = f"{RED}R{r} C{c} is a given — can't change it.{RESET}"
                else:
                    current[pos] = v
                    msg = ""
                continue
        msg = f"{RED}didn't understand that. format: row col value{RESET}"


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
            render(grid, given, work)
            print(f"\n  {GREEN}Solved.{RESET}  {''.join(map(str, work))}\n")
        else:
            print(f"\n  {RED}No solution.{RESET}\n")
        return

    play(args.difficulty)


if __name__ == "__main__":
    main()
