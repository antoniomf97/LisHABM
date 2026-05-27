## Summary

<!-- One or two sentences describing what this PR does. -->

## Motivation

<!-- Why is this change needed? Link related issues: Closes #123 -->

## Changes

<!-- Bullet list of notable changes. Skip if the summary covers it. -->
-
-

## Testing

<!-- How did you verify this works? -->
- [ ] Unit tests added or updated
- [ ] Integration tests added or updated (if behavior spans modules)
- [ ] Ran `pytest` locally and it passes
- [ ] Tried a sample run / sweep if simulator behavior changed

## Module impact

<!-- Tick any that apply. Helps reviewers know what to focus on. -->
- [ ] `core/` (engine internals — extra scrutiny)
- [ ] Domain module(s): _________
- [ ] `io/` (loaders / writers)
- [ ] `parallel/` (intra-run executor)
- [ ] `orchestration/` (sweeps, scheduler)
- [ ] Configs / data layout
- [ ] Tooling / CI / docs only

## Checklist

- [ ] Code follows the project's structure (module boundaries respected)
- [ ] No `print()` debug calls or `breakpoint()` left behind
- [ ] Docs / README updated if behavior or interface changed
- [ ] Commits are signed