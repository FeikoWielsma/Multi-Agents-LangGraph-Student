# Testing a game

- Document : DOC-QA-01
- Owner : Tester
- Type : guide
- Date : 2026-09-30

## Rule tests

Each rule has a scripted test : set up a board, step once, compare. A failed test names the rule, what was expected and
what came back, so the Coder can fix it without seeing the harness.

## The bot

The bot plays five games with fixed seeds. It searches for the nearest star past the body and the comets. A game ships
when every rule test passes and the bot eats at least 10 stars on average.

## Bug reports

One bug per failed test : what happens, what the rule says, where the cause probably is. The Tester does not write the
fix. Severity is `blocker` when the game cannot ship, `major` when a rule is broken, `minor` for everything else.

## The fix loop

A failed build goes back to the Coder with the bug report. After three attempts the Producer stops the loop and decides.
