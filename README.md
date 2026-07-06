# Sudoku

Generate, solve, and play Sudoku in the terminal. A backtracking solver, a
uniqueness-checked puzzle generator, and a playable board with hints and live
conflict highlighting. Pure Python 3, standard library only.

![version](https://img.shields.io/badge/version-1.1.0-blue) ![lang](https://img.shields.io/badge/Python-3.8%2B-3776ab) ![deps](https://img.shields.io/badge/dependencies-none-ffd343) ![license](https://img.shields.io/badge/license-MIT-yellow)

## Play
```bash
python sudoku.py                    # random medium puzzle
python sudoku.py --difficulty hard  # easy | medium | hard | evil
```
At the prompt:

| Command | Action |
|---------|--------|
| `r c v` | Place value `v` at row `r`, column `c` (e.g. `3 5 7`) |
| `r c 0` | Clear that cell |
| `n r c v` | Toggle a pencil note (candidate `v`) in an empty cell |
| `u` | Undo the last placement or clear |
| `check` | Highlight any entries that differ from the solution |
| `peers` | Toggle highlighting of the last cell's row/column/box peers |
| `h` | Hint (fills one correct cell) |
| `s` | Reveal the full solution |
| `new` | New puzzle |
| `q` | Quit |

Givens are shown bold, your entries in blue, and any cell that breaks a
row/column/box rule turns red. Pencil notes render small and dim inside empty
cells and clear automatically when the cell is filled. The last-edited cell is
highlighted along with its row, column, and box peers, and the status line
tracks a game timer and a running mistake count.

## Solve a specific puzzle
Pass an 81-character grid (`.` or `0` for blanks):
```bash
python sudoku.py --solve "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
```

## How it works
- The solver uses backtracking with a minimum-remaining-values heuristic: it
  always fills the empty cell with the fewest legal candidates first, which
  prunes the search hard.
- The generator builds a full solution (the three diagonal boxes are filled at
  random first since they are independent, then the rest is solved), then
  removes cells one at a time, keeping a removal only if the puzzle still has
  exactly one solution. That uniqueness check is the same solver, stopped as
  soon as it finds a second solution.

## License
MIT.
