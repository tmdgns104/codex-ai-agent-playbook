# Readability Review Checklist

## Intent

- [ ] Can a developer explain what the changed code is for?
- [ ] Do names communicate intent?
- [ ] Is the main flow easy to trace?

## Functions

- [ ] Each function has one understandable responsibility.
- [ ] Functions are not excessively long without a good reason.
- [ ] Parameters are meaningful and limited.
- [ ] Return values are predictable.
- [ ] Side effects are visible.

## Control Flow

- [ ] Nesting is not unnecessarily deep.
- [ ] Error handling is explicit.
- [ ] No broad exception swallowing.
- [ ] No clever compressed expression that obscures behavior.

## Abstraction

- [ ] No speculative framework/pattern.
- [ ] No unnecessary manager/factory/adapter/registry layer.
- [ ] Reuse is real, not hypothetical.
- [ ] Dependency direction is understandable.

## Documentation

- [ ] Comments explain why, not obvious syntax.
- [ ] Important public APIs are documented when useful.
- [ ] README/code-reading order still matches the code.

## Verification

- [ ] Tests pass.
- [ ] Lint/type checks run when configured.
- [ ] Readability audit findings were reviewed, not blindly obeyed.
