# Comet Snake : rules

A game is one HTML file. The kit holds the canvas, the drawing, the keyboard and the bot. The `logic` block holds
every rule as pure JavaScript. Tests and the bot run that block headless, so it has no DOM, no clock and no
`Math.random`. Randomness comes from `nextRandom(state)` and the helpers built on it.

## The state

`init(seed)` returns a plain JSON object with these fields. A twist may add the fields it names.

| field | meaning |
| --- | --- |
| `snake` | list of `{x, y}`, head first |
| `dir` | `up`, `down`, `left` or `right` |
| `stars` | list of `{x, y}`, always one star while the game runs |
| `comets` | list of `{x, y, dx, dy}` |
| `extras` | list of `{x, y, kind}`, the objects a twist adds |
| `score` | points |
| `eaten` | stars eaten |
| `tickMs` | milliseconds between ticks, starts at 200 |
| `ticks` | steps played |
| `over`, `reason` | `over` is true when the game ended ; `reason` is `comet` or `self`, otherwise `null` |
| `seed` | the random seed |

`step(state, input)` returns a new state and must not change the state it received. `input` is a direction or `null`.

## The rules

1. Movement : each step the head moves one cell in `dir`, and the tail follows. The length stays the same
2. Steering : an input sets `dir`. An input opposite to `dir` is ignored
3. Space wraps : leaving one edge enters at the opposite edge
4. Stars : when the head lands on a star, the snake grows by one, `score` and `eaten` go up by one, and a new star appears
5. Comets start : `init` places 2 comets with `spawnComet`
6. Comets move : every step each comet moves by `(dx, dy)`, wrapping at the edges like the snake
7. Comet hit : when a comet and the head are on the same cell after both moved, `over` is true and `reason` is `comet`.
   The same holds when the head and a comet swap cells in one step. A comet that crosses the body does nothing
8. Self hit : when the head lands on a body cell, `over` is true and `reason` is `self`. The cell the tail leaves in this
   step is free, so a snake may follow its own tail
9. Speed : every fifth star (eaten 5, 10, 15 ...) lowers `tickMs` by 20, never below 60
10. More comets : every fifth star adds one comet with `spawnComet`, up to 6 comets
11. Game over is final : `step` on a finished game returns the same state, unchanged, and `ticks` stops
12. `ticks` goes up by one on every step of a running game, also on the step that ends it

## The order of a step

Work in this order. Every one of these steps has broken a build when it moved.

1. Return a finished game unchanged, then copy the state
2. Steer, then work out the new head cell. A twist that moves the head does it here
3. Move the comets, into a new list with the same length as the old one
4. Check for a comet hit, using the old and the new comet positions
5. Check for a self hit against the old snake, before you change it. Compare the new head with every old cell, leaving
   out the last old cell unless the head is on a star this step, because that cell is the tail that moves away
6. Put the moved comets in `state.comets`, then change the snake, the score and the pickups
7. Spawn last : new stars, comets and extras go in after every check, so nothing spawned is lost or read by a check
