# Sandtris

[![Play in Browser](https://img.shields.io/badge/Play_in_Browser-blue?style=for-the-badge&logo=web)](https://Drewienko.github.io/sandtris/)

Sandtris clone built with pygame.

## Features
- **Web Version:** Play directly in your browser via pygbag.
- **Local Version:** Play locally using pygame.
- **AI Version:** (Planned) Headless environment and API for AI agents to play the game.

> **Known issue:** Browser performance needs improvement. The sand simulation runs in Python and is not yet optimized for WebAssembly. The desktop version is unaffected.

## Controls
*   **Move Left / Right:** `Left Arrow` / `A` / `D`
*   **Rotate:** `Up Arrow` / `W`
*   **Fast Drop:** `Down Arrow` / `S` / `Space` / `Enter`
*   **Pause:** `Esc` / `P`

## Installation

To run Sandtris locally, you need Python 3.12+ and `uv`.

```bash
# Clone the repository
git clone https://github.com/Drewienko/sandtris.git
cd sandtris

# Run the game using uv
uv run sandtris
```