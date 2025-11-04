# HTML Refinement Pipeline

## Overview

The `refine_html.py` script implements a refinement pipeline that improves previously generated HTML by comparing:
1. **Ground truth images** - Original screenshots (e.g., `episode_27/episode_27_step_00.png`)
2. **Generated visualizations** - Screenshots from your first HTML generation (e.g., `episode_27/generated/screenshots/episode_27_step_00_*.png`)

The VLM receives both images and generates improved HTML that better matches the ground truth.

## Directory Structure

### Before Refinement
```
episode_visualizations/
├── episode_27/
│   ├── episode_27_step_00.png          # Ground truth
│   ├── episode_27_step_01.png          # Ground truth
│   ├── ...
│   ├── image/                          # Original input images
│   └── generated/                      # First-pass generated outputs
│       ├── html/                       # Generated HTML files
│       ├── screenshots/                # Visualizations of generated HTML
│       └── logs/                       # Generation logs
```

### After Refinement
```
episode_visualizations/
├── episode_27/
│   ├── ...
│   ├── generated/                      # First-pass outputs
│   └── regenerated/                    # ✨ NEW: Refined outputs
│       ├── html/                       # Refined HTML files
│       ├── screenshots/                # Visualizations of refined HTML
│       └── logs/                       # Refinement logs
```

## Features

- ✅ **Selective Processing**: Only processes episodes that already have a `generated/` directory
- ✅ **Batch Processing**: Process multiple episodes by specifying an ID range
- ✅ **Smart File Matching**: Automatically finds the latest generated files for each step
- ✅ **Dual-Image Comparison**: VLM receives both ground truth and previous attempt
- ✅ **Organized Output**: Creates clean `regenerated/` subdirectory structure
- ✅ **Detailed Logging**: Tracks all refinements with JSONL logs and summary statistics
- ✅ **Resume Support**: Automatically skips already-refined steps, allowing you to resume interrupted sessions

## Usage

### Configuration

Edit the parameters in the `main()` function of `refine_html.py`:

```python
# ========================================================================
# CONFIGURE THESE PARAMETERS
# ========================================================================

# Episode ID range to process
start_id = 1           # Starting episode ID (inclusive)
end_id = 1111          # Ending episode ID (inclusive)

# Base directory containing episode subdirectories
base_dir = "/Users/reisskoh/androidworld/mwm/query/episode_visualizations"

# VLM server settings
base_url = "http://localhost:8080/v1"
model = "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8"

# ========================================================================
# END CONFIGURATION
# ========================================================================
```

### Running the Script

After configuring the parameters:

```bash
python refine_html.py
```

### Configuration Examples

**Refine episodes 1 through 100:**
```python
start_id = 1
end_id = 100
```

**Refine a single episode:**
```python
start_id = 27
end_id = 27
```

**Refine all episodes up to 1111:**
```python
start_id = 1
end_id = 1111
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|----------|------|---------|-------------|
| `start_id` | int | 1 | Starting episode ID (inclusive) |
| `end_id` | int | 1111 | Ending episode ID (inclusive) |
| `base_dir` | str | `../episode_visualizations` | Base directory containing episodes |
| `base_url` | str | `http://localhost:8080/v1` | VLM server URL |
| `model` | str | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` | Model name |

## Resume Functionality

Both `ss2html.py` and `refine_html.py` support **automatic resume** - you can interrupt the scripts at any time and resume later without reprocessing already-completed files.

### How It Works

**For `ss2html.py` (initial generation):**
- Before processing each image, checks if HTML already exists in `episode_X/generated/html/`
- Looks for files matching pattern: `episode_X_step_Y_*.html`
- If found, skips processing and moves to next image
- Shows message: `Skipping <filename> (already processed)`

**For `refine_html.py` (refinement):**
- Before refining each step, checks if refined HTML already exists in `episode_X/regenerated/html/`
- Looks for files matching pattern: `episode_X_step_Y_refined_*.html`
- If found, skips refinement and moves to next step
- Shows message: `Skipping <step_name>: Already refined`

### Example Usage

```bash
# Start processing
python refine_html.py

# ... interrupt with Ctrl+C after episode 50 ...

# Resume later - automatically continues from episode 51
python refine_html.py
```

### Benefits

- 🔄 **Safe interruption**: Can stop at any time (Ctrl+C, server issues, etc.)
- ⚡ **Fast restart**: Immediately skips already-completed work
- 💾 **No wasted compute**: Never reprocesses existing files
- 🎯 **Precise resume**: Handles partial episode completion

## Processing Logic

For each episode in the specified range:

1. **Check if episode exists**: Skip if `episode_X/` directory not found
2. **Check if generated**: Skip if no `episode_X/generated/` directory
3. **Find ground truth images**: Look for `episode_X_step_*.png` files
4. **Match generated screenshots**: Find corresponding files in `generated/screenshots/`
5. **Check if already refined**: Skip if refined HTML already exists (resume functionality)
6. **Refine with VLM**:
   - Send both images (ground truth + generated) to VLM
   - VLM compares and generates improved HTML
7. **Save results**: Store in `episode_X/regenerated/`
8. **Log details**: Record all refinements in JSONL logs

## Example Output

### First Run

When you run `python refine_html.py` for the first time:

```
======================================================================
HTML Refinement Pipeline
======================================================================
Base directory: /Users/reisskoh/androidworld/mwm/query/episode_visualizations
Episode ID range: 1 to 1111
======================================================================

⊘ Episode 1: No 'generated' directory, skipping

======================================================================
Processing Episode 27
======================================================================
  Found 6 ground truth images
  Processing episode_27_step_00...
  Refining HTML using ground truth comparison...
  ✓ Refined HTML generated successfully!
    ✓ Saved refined HTML: episode_27_step_00_refined_20251103_184523.html
    ✓ Saved refined screenshot: episode_27_step_00_refined_20251103_184523.png
  Processing episode_27_step_01...
  ...
✓ Episode 27 complete: 6 steps processed

======================================================================
REFINEMENT COMPLETE
======================================================================
Episodes processed: 1/1111
Episodes skipped: 1110
Total steps processed: 6
Total steps skipped: 0
======================================================================

Summary saved to: refinement_summary_20251103_184530.json
```

### Resuming After Interruption

If you interrupt and restart, already-refined steps are automatically skipped:

```
======================================================================
Processing Episode 27
======================================================================
  Found 6 ground truth images
  ⊘ Skipping episode_27_step_00: Already refined
  ⊘ Skipping episode_27_step_01: Already refined
  ⊘ Skipping episode_27_step_02: Already refined
  Processing episode_27_step_03...
  Refining HTML using ground truth comparison...
  ✓ Refined HTML generated successfully!
  ...
✓ Episode 27 complete: 3 steps processed, 3 skipped (already refined or missing generated files)
```

## Output Files

### Refined HTML Files
- Location: `episode_X/regenerated/html/`
- Naming: `episode_X_step_Y_refined_TIMESTAMP.html`
- Content: Improved HTML that better matches ground truth

### Refined Screenshots
- Location: `episode_X/regenerated/screenshots/`
- Naming: `episode_X_step_Y_refined_TIMESTAMP.png`
- Content: Visualization of refined HTML

### Logs
- **Per-episode logs**: `episode_X/regenerated/logs/refinement_log_YYYYMMDD.jsonl`
- **Summary statistics**: `episode_visualizations/refinement_summary_TIMESTAMP.json`

### Log Format

Each refinement entry in the JSONL log:
```json
{
  "timestamp": "2025-11-03T18:45:23.123456",
  "step_name": "episode_27_step_00",
  "ground_truth": "/path/to/episode_27_step_00.png",
  "generated_screenshot": "/path/to/generated/screenshots/episode_27_step_00_20251103_181925.png",
  "refined_html": "/path/to/regenerated/html/episode_27_step_00_refined_20251103_184523.html",
  "refined_screenshot": "/path/to/regenerated/screenshots/episode_27_step_00_refined_20251103_184523.png"
}
```

## Requirements

- Python 3.7+
- `openai` library (for VLM client)
- `playwright` (for HTML rendering)
- Running vllm server with vision model

### Installation

```bash
# Install dependencies
pip install openai playwright

# Install Playwright browsers
playwright install chromium
```

## Tips

1. **Start small**: Test with a single episode first (set `start_id = 27` and `end_id = 27`)
2. **Check VLM server**: Ensure your vllm server is running before starting
3. **Monitor progress**: The script provides detailed progress updates
4. **Review logs**: Check JSONL logs for detailed processing information
5. **Compare results**: Use the generated screenshots to visually compare improvements

## Troubleshooting

### "No 'generated' directory, skipping"
- This is expected for episodes that haven't been processed by `ss2html.py` yet
- Only episodes with existing generated HTML will be refined

### "No ground truth images found"
- Check that episode directory contains `episode_X_step_*.png` files
- Verify the episode ID is correct

### "No generated screenshot found"
- The `generated/screenshots/` directory might be empty
- Re-run the initial generation with `ss2html.py` first

### Playwright errors
- Install Playwright: `pip install playwright && playwright install chromium`
- The script will continue without screenshots if Playwright fails

## Integration with Existing Workflow

1. **Initial Generation** (using `ss2html.py`):
   ```bash
   # Configure parameters in ss2html.py, then run:
   python ss2html.py  # Generates episode_X/generated/
   ```

2. **Refinement** (using `refine_html.py`):
   ```bash
   # Configure parameters in refine_html.py (e.g., start_id=1, end_id=1111), then run:
   python refine_html.py  # Generates episode_X/regenerated/
   ```

3. **Further Iterations** (optional):
   - You can run refinement multiple times
   - Each run creates new timestamped files
   - The latest files are automatically used as input

## Architecture

The refinement pipeline uses a dual-image prompting strategy:

```
┌─────────────────┐     ┌──────────────────────┐
│ Ground Truth    │────▶│                      │
│ Image           │     │   Vision Language    │
└─────────────────┘     │   Model (VLM)        │
                        │                      │
┌─────────────────┐     │   "Compare these     │    ┌──────────────┐
│ Generated       │────▶│    images and        │───▶│ Refined HTML │
│ Screenshot      │     │    improve HTML"     │    └──────────────┘
└─────────────────┘     │                      │
                        └──────────────────────┘
```

The VLM can directly compare visual differences and adjust:
- Layout and positioning
- Colors and styling
- Typography
- Element sizes
- Spacing and alignment
- Icons and images

This is more effective than single-image generation because the model has explicit visual feedback about what needs improvement.
