# Star Slide design

- Document : DOC-SS-02
- Game : SS-02
- Owner : Designer
- Type : design doc
- Date : 2026-08-21

## Overview

Star Slide is the puzzle team's game. The ship slides in a straight line until a rock or an edge stops it. Collect every
star in as few slides as possible. There is one fixed level and no randomness, so a good answer can be computed.

## Scoring

The score is the number of stars. The real result is the number of slides. The puzzle bot searches for the shortest list
of slides, and that number is the par of the level.
