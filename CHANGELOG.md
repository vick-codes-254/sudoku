# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-07-04

### Added
- Pencil notes: `n r c v` toggles a candidate note in an empty cell. Notes
  render small and dim in a 3x3 layout and clear automatically when the cell
  is filled.
- Game timer and mistake counter shown in the status line. A mistake is
  counted whenever a placed value conflicts with or differs from the solution.
- Undo: `u` reverts the last placement or clear from a move history.
- `check` command highlights any current entries that differ from the unique
  solution.
- `peers` command toggles highlighting of the last-edited cell's row, column,
  and box peers.

### Changed
- Polished grid drawing with box-drawing borders and column/row labels.
- The last-edited cell and its peers are now highlighted for easier scanning.

## [1.0.0] - 2026-07-04

Initial release.
- Generate unique puzzles at easy, medium, hard, and evil difficulty.
- Backtracking solver with a minimum-remaining-values heuristic.
- Playable board with place, clear, hint, solve, new, and quit commands.
- Live row/column/box conflict highlighting.
- `--solve` and `--difficulty` command-line flags.
