# Release checklist

- Document : DOC-REL-01
- Owner : Producer
- Type : checklist
- Date : 2026-10-01

## Before release

All rule tests pass. The bot scores at least 10 stars on average. No open bug of severity `blocker`. The Artist has signed
off contrast on every danger sprite. The file opens in a browser with no console errors.

## Approval

The Publisher is a human. No game goes out without the Publisher's yes. The Producer sends the build number, the test
report and the bot score, and waits.

## After release

The build is tagged in the `builds` table. Playtest results go in `playtests`. A rollback goes to the last build with
status `released`.
