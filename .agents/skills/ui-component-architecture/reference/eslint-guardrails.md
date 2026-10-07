# ESLint guardrails for UI component architecture

Lint can't enforce "this should have been reused," but it can enforce the
boundaries that keep the architecture honest. These rules nudge the behavior
mechanically so it doesn't rely on the model remembering. Add the ones that fit;
the boundary rule (banning app imports inside the UI package) is the most valuable.

Assumes a flat-config (`eslint.config.js`) ESLint 9 setup. Adapt globs to the
repo's actual UI package path.

Apply [codebase-design](../../codebase-design/SKILL.md) when interpreting size
diagnostics. These examples are optional additions to the current toolchain;
they do not authorize downgrading existing checks or fragmenting cohesive UI.

## 1. Ban app imports inside the UI package (the important one)

A shared UI primitive must stay presentational. This rule stops the UI package
from importing app code (`@/...`, routers, stores, API clients), which is the
single clearest signal of a leaky, over-coupled extraction.

```js
// eslint.config.js
import boundaries from "eslint-plugin-boundaries";

export default [
  {
    files: ["packages/ui/**/*.{ts,tsx}"], // replace with this repo's UI package glob
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/*"],
              message:
                "The UI package must not import app code. Keep primitives presentational; pass data as props.",
            },
            {
              group: ["@repo/api", "@repo/db", "**/stores/*", "**/routes/*"],
              message: "No app stores/routes/data layers inside the UI package.",
            },
          ],
        },
      ],
    },
  },
];
```

`eslint-plugin-boundaries` is a heavier but more expressive alternative if you
want to model `app → ui` as a one-way dependency across the whole monorepo.

## 2. Flag raw hex colors in app JSX

Pushes styling onto theme tokens instead of magic hex values scattered through
`className`. This catches `bg-[#0a0a0a]` / `text-[#4ade80]` arbitrary values.

```js
{
  files: ["apps/**/*.{tsx}"],
  rules: {
    "no-restricted-syntax": [
      "warn",
      {
        selector: "Literal[value=/\\[#([0-9a-fA-F]{3,8})\\]/]",
        message: "Avoid raw hex in className; use a theme token (e.g. bg-surface, text-positive).",
      },
    ],
  },
}
```

Tune to taste — some teams allow arbitrary values in the UI package itself (where the
tokens are defined) but ban them in apps.

## 3. Review JSX nesting depth

Depth is a readability signal, not proof that another component is needed.
Simplify redundant layout or conditions first. Extract only when the new
component hides meaningful presentation or behavior. Use a documented, narrow
exception when deeper markup remains the clearest representation.

```js
{
  files: ["apps/**/*.{tsx}"],
  rules: {
    "react/jsx-max-depth": ["warn", { max: 6 }],
  },
}
```

For a new rule, start permissive (6–8) and assess its diagnostics against real
screens. Retain configured file limits; use 300 nonblank, noncomment lines when
introducing a file limit, with documented narrow increases for cohesive
components.

## 4. Tailwind class hygiene (optional)

`eslint-plugin-tailwindcss` (or the newer `eslint-plugin-better-tailwindcss`)
catches contradicting classes, enforces ordering, and flags unknown utilities.
Doesn't enforce reuse, but keeps the inline styling that remains tidy.

```js
import tailwind from "eslint-plugin-tailwindcss";

export default [...tailwind.configs["flat/recommended"]];
```

## Rollout note

Add new rules as `warn` first on existing code, then promote verified scopes.
Keep existing errors and required checks intact. Resolve needless indirection
and actual boundary leaks; do not lower a gate to make an extraction pass.
