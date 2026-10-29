# Nireti — AI Photo Copilot

Nireti is an AI-powered photo editing assistant built for brand photographers and creative teams. You give it your brand brief or website URL, and it analyses your photos and suggests editing adjustments — exposure, shadows, highlights, contrast, temperature, and saturation — tuned specifically to your brand's visual identity.

Built with [Reflex](https://reflex.dev) and powered by Nebius AI (Nemotron models) and Tavily.

---

## Features

- **Brand direction** — Paste a brief or drop in a URL. Nireti extracts your brand's visual genre and traits using Nemotron and Tavily.
- **Per-photo AI analysis** — Each photo is analysed in the background against your brand direction. Suggestions are ready by the time you reach them.
- **Manual editing** — Six adjustment sliders (exposure, shadows, highlights, contrast, temperature, saturation) with live preview. Type values directly or drag.
- **Crop & pan** — Crop to 4:3, 4:5, or 1:1 with horizontal and vertical pan controls.
- **Undo / Redo / Reset** — Full edit history per photo.
- **Before / After toggle** — Instantly compare the original and edited image.
- **Filmstrip** — Multi-photo workflow. Import additional photos at any time without losing existing edits. Remove individual photos if you have no use for them.
- **Export** — Download the edited photo at full resolution, or export all at once.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | [Reflex](https://reflex.dev) (Python full-stack) |
| Image processing | Pillow, NumPy |
| Text model | Nebius — `nvidia/nemotron-3-super-120b` and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` |
| Vision model | Nebius — `nvidia/Nemotron-3.5-Super-VL` |
| Web search | [Tavily](https://tavily.com) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A [Nebius AI](https://nebius.com) API key
- A [Tavily](https://tavily.com) API key

### Installation

```bash
git clone https://github.com/your-username/nireti.git
cd nireti

uv sync
```

### Environment Variables

Create a `.env` file in the project root:

```env
EDITOR_KEY=your_nebius_api_key
TAVILY_KEY=your_tavily_api_key
```

### Run Locally

```bash
uv run reflex run
```

Open [http://localhost:3000](http://localhost:3000).

---

## Usage

1. **Settings page** — Enter your brand brief (a sentence or two about your brand - Be intentional and clear, it helps the models) and/or your website URL. Click **Get Direction**. Nireti will extract your visual genre and traits.
2. **Editor page** — Import your photos. Nireti analyses each one in the background.
3. Once a photo shows **Ready**, click **Apply AI Suggestions** to apply the recommended adjustments.
4. Fine-tune with the sliders, crop if needed, then **Export**.

---

## Project Structure

```
.
├── reModels/
│   └── models.py         # Nebius + Tavily API calls, Pydantic schemas
├── src/
│   ├── state.py          # Full Reflex app state
│   └── pages/
│       ├── home.py       # Landing page UI
│       ├── editor.py     # Editor UI
│       └── settings.py   # Settings UI
├── render.py             # Image processing pipeline
├── rxconfig.py           # Reflex config
└── pyproject.toml
```

---

## License

MIT