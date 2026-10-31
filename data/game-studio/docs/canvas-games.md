# Writing a canvas game

- Document : DOC-KIT-01
- Owner : Coder
- Type : skill pack
- Date : 2026-09-02

## One file

A game is one HTML file with no outside scripts, so anyone can open it by double-clicking. The file has four script
blocks : theme, logic, bot and view.

## Pure logic

All rules live in the logic block as two functions, `init(seed)` and `step(state, input)`. The logic has no DOM, no clock
and no `Math.random`. That is what lets the Tester run the game headless through QuickJS, thousands of ticks in a second.

## State

The state is a plain JSON object. `step` returns a new state and leaves the old one untouched, so a replay is exact and a
build can be rolled back to any tick.

## Common mistakes

Changing the state that came in, which breaks replay. Removing the tail twice before the self hit check, which lets the
head pass through the last body cell. Replacing the comet list after a spawn, which throws away the comet that just
spawned. Checking for a hit only after both moved, which lets a head and a comet swap cells unharmed.
