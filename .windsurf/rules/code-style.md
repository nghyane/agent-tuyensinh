---
trigger: always_on
---

Always generate clean, modular, and type-safe code that is easy to read, extend, and navigate in IDEs.

✅ MUST:
- Add JSDoc to all public/core functions.
- Use meaningful names and consistent formatting.
- Use static types (TypeScript preferred).
- Structure code for readability and reuse.
- Leverage IDE-friendly patterns (IntelliSense, jump-to-def, etc.).

❌ AVOID:
- Try-catch unless truly needed (e.g., file I/O, network, JSON.parse).
- Deep nesting, magic numbers, commented-out or unused code.
- Hiding logic in catch blocks or returning defaults silently.

Comment, organize, and document like you're handing off code to a team or AI agent.
