# Twist menu

- Document : DOC-TWIST-01
- Game : CS-01
- Owner : Designer
- Type : design doc
- Date : 2026-10-12

## How to use the menu

The Designer picks one twist that answers the brief. Every twist on the menu has its own scripted tests, so the Tester
can prove it works. A twist off the menu has no tests yet.

## Golden stars

Id `golden`. Greedy players chase a rare big prize.

- Every third star eaten (eaten 3, 6, 9 ...) also places one extra of kind 'golden' with spawnExtra.
- When the head lands on a golden extra, score goes up by 3 and the extra is removed. The snake does not grow and eaten does not change.

## Wormholes

Id `wormhole`. Two linked holes let the snake jump across the map.

- init places exactly two extras of kind 'wormhole' with spawnExtra.
- When the head lands on a wormhole it moves in the same step to the other wormhole. Stars, comets and body are then checked at the cell where the head ends up.
- Wormholes stay on the board. The length of the snake does not change.

## Shields

Id `shield`. One second chance against a comet.

- init sets a new field shield to false.
- Every fourth star eaten (eaten 4, 8, 12 ...) also places one extra of kind 'shield' with spawnExtra.
- When the head lands on a shield extra, shield becomes true and the extra is removed.
- A comet hit while shield is true does not end the game : shield becomes false and that comet is removed. A second hit ends the game.

## Frozen time

Id `clock`. A clock stops the comets for a moment.

- init sets a new field frozen to 0.
- Every fourth star eaten (eaten 4, 8, 12 ...) also places one extra of kind 'clock' with spawnExtra.
- When the head lands on a clock extra, frozen becomes 20 and the extra is removed.
- On a step that starts with frozen above 0, comets do not move and frozen goes down by 1.
