# Comet Arcade style guide

- Document : DOC-STYLE-01
- Owner : Artist
- Type : studio guide
- Date : 2026-09-14

## Palette

Every game has a dark background and one warm danger colour. Danger is a warm colour : a comet is red or orange, never
blue or grey. Friendly objects are cool or gold : the snake is green, a star is gold.

## Contrast

Anything that can end the game needs a contrast of at least 4.5 to 1 against the background. A comet below that ratio is
a release blocker, because players lose to something they could not see. To fix a low-contrast sprite, keep the shape and
change the colour to the studio danger colour `#ff6b5e`.

## Sprites

A sprite is 7 rows of 7 characters, `#` for a filled pixel and `.` for an empty one. A sprite reads at 30 pixels per cell.
Danger sprites have an uneven outline. Friendly sprites are symmetric.

## Tone

Short words on screen. `GAME OVER`, never `Oops!`. No exclamation marks.

## Names

Game ids are two letters and a number, such as `CS-01`. Asset ids add the kind and a number, such as `CS-SPR-03`.
