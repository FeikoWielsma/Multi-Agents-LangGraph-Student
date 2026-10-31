# Comet Snake design

- Document : DOC-CS-01
- Game : CS-01
- Owner : Designer
- Type : design doc
- Date : 2026-10-05

## Overview

Comet Snake is snake in space. Eat stars, dodge comets, every fifth star speeds the game up. A game is one HTML file with
a canvas. Space wraps at the edges, so there are no walls to hit.

## Stars and growth

A star makes the snake one cell longer and scores one point. One star is on the board at all times. A new star never
appears on the snake.

## Comets

The game starts with 2 comets. Each comet flies in a straight line, one cell per tick, and wraps at the edges. Hitting a
comet with the head ends the game. A comet that crosses the body does nothing. A head and a comet that swap cells in
one tick count as a hit.

## Speed

Every fifth star lowers the tick from 200 ms by 20 ms, never below 60 ms, and adds one comet, up to 6. Five stars take
about a minute for a new player.

## Twists

Each new version of Comet Snake adds one twist from the twist menu. A twist answers a complaint from a playtest.
