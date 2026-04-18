# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the prototype

- No package manager, build step, tests, or linter. There is no `package.json` — do not look for `npm run ...`.
- Open `index.html` directly in a browser, or serve the folder with any static server (e.g. `python -m http.server`) and visit `http://localhost:8000/`.
- React 18 + ReactDOM 18 + Babel Standalone 7 are loaded from unpkg via `<script>` tags in [index.html](index.html); all `.jsx` files are transpiled in-browser by `type="text/babel"` script tags. Syntax errors only surface at runtime in the browser console.
- Runtime expects a host-injected `window.claude.complete(prompt: string) => Promise<string>` — used by the king, plaza, gen, and game screens for AI chat, comment suggestions, meme copy, and judge scoring. Every call site is wrapped in `try/catch` with a hardcoded Chinese fallback, so the UI still works offline, just without AI output.

## Architecture

Everything is global. There is no ES-module system — each JSX file ends with `Object.assign(window, { ... })` to publish its exports, and downstream files reference them by name.

**Script load order is fixed in [index.html](index.html) and matters:**

1. [ios-frame.jsx](ios-frame.jsx) — simulated iOS 26 device chrome: `IOSDevice`, `IOSStatusBar`, `IOSNavBar`, `IOSGlassPill`, `IOSList`, `IOSListRow`, `IOSKeyboard`.
2. [data.jsx](data.jsx) — seed content: `SEED_POSTS` (广场 feed), `PERSONAS` (`default` / `dialect` / `classical` 梗王 variants), `GEN_TEMPLATES`, `GEN_STYLES`, `GAME_LEVELS`.
3. [ui-primitives.jsx](ui-primitives.jsx) — shared widgets: `DogeAvatar`, `RotatingCTA`, `Badge`, `LevelTag`, `MemePlaceholder`, `PointFloat`.
4. Four tab screens: [screen-king.jsx](screen-king.jsx) (梗王 chat home), [screen-plaza.jsx](screen-plaza.jsx) (feed + comment detail sheet), [screen-gen.jsx](screen-gen.jsx) (meme generator), [screen-game.jsx](screen-game.jsx) (fill-the-meme game).
5. The `App` component (tab router) and `ReactDOM.createRoot(...).render(...)` are inline in [index.html](index.html). Adding a new screen = new `.jsx` file + new `<script type="text/babel" src="...">` entry + new item in the `tabs` array in `App`.

All app state lives in `App` in [index.html](index.html): `tab`, `persona`, `points`, `pointFloat`, `editMode`. Screens receive callbacks (`onPointGain`, `setPersona`, `onOpenGen`, `goBack`) as props — there is no store.

Design tokens are CSS variables in [styles.css](styles.css) (`--purple`, `--red`, `--green`, `--blue`, `--amber`, `--font-cn`, `--shadow-card`, `--shadow-purple`, ease curves) plus reusable animation classes: `.pop-in`, `.slide-up`, `.fade-in`, `.bob`, `.skeleton`, `.typing-dot`, `.float-up`, `.no-scroll`, and `.grad-border` with `.red / .blue / .green / .amber` color variants. Prefer these over inventing new inline styles.

**Edit-mode bridge** ([index.html](index.html)): the app listens for `__activate_edit_mode` / `__deactivate_edit_mode` `postMessage`s from `window.parent`, sends `__edit_mode_available` on mount and `__edit_mode_set_keys` when persona changes. The persisted tweak lives between `/*EDITMODE-BEGIN*/ { ... } /*EDITMODE-END*/` markers in [index.html](index.html) — an external tool round-trips that object. Do not rename the markers or change the object's shape without checking what reads it.

## Content & language conventions

- UI copy is Simplified Chinese. Meme vocabulary (`那咋了`, `class is class`, `city不city`, `哈基米`, `吗喽`, `主理人`, `发疯文学`, `班味`, `孤勇者`) is load-bearing for the AI prompts in [screen-king.jsx](screen-king.jsx) and [screen-gen.jsx](screen-gen.jsx) — preserve the Chinese tone and meme terms when editing prompts.
- Personas have a fixed shape: `{ key, name, subtitle, greeting, style, samples: [{ user, bot }] }`. Both `TweaksPanel` in [index.html](index.html) and `PersonaSheet` in [screen-king.jsx](screen-king.jsx) iterate `Object.values(PERSONAS)`, so adding a persona is a data-only change.

## Verification after changes

1. Open `index.html` in a browser and check the console for Babel parse errors.
2. Click through all four tabs (梗王 / 广场 / 造梗 / 游戏). Confirm the AI-driven actions (梗王 chat, 广场 "AI帮我想" in the comment sheet, 造梗 generate, 游戏 scoring) either return AI output or degrade cleanly to the fallback without breaking the UI.
3. Toggle the persona (🎭 button on the 梗王 screen, or the Tweaks panel when edit mode is active) and confirm the chat resets with the new `greeting` and the reply style matches the new persona.
