#!/usr/bin/env python3
"""
HTML Refinement Pipeline

This script refines previously generated HTML by comparing ground truth screenshots
with the HTML-generated visualizations. The VLM receives both images and generates
improved HTML that better matches the ground truth.

Usage:
    1. Configure parameters in the main() function
    2. Run: python refine_html.py
"""

import base64
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from openai import OpenAI


class HTMLRefiner:
    """Refine generated HTML by comparing with ground truth images."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        model: str = "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8",
        episode_base_dir: str = None
    ):
        """
        Initialize the HTML Refiner.

        Args:
            base_url: Base URL for the vllm server
            model: Model name to use
            episode_base_dir: Base directory containing episode subdirectories
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key="EMPTY"  # vllm doesn't require API key
        )
        self.model = model
        self.episode_base_dir = Path(episode_base_dir) if episode_base_dir else None
        self.system_prompt = self._get_refinement_system_prompt()

    def _get_refinement_system_prompt(self) -> str:
        """Get the system prompt for HTML refinement."""
        return """You are an expert mobile UI developer. You will be shown two images:
1. The GROUND TRUTH - the target mobile interface you should match
2. Your PREVIOUS ATTEMPT - a visualization of HTML code you previously generated

Your task is to analyze the differences between these two images and generate improved HTML code that better matches the ground truth interface.

Requirements:
1. Generate complete, valid HTML5 code
2. Include inline CSS for styling (mobile-first design, max-width: 480px)
3. Carefully observe and fix any discrepancies in:
   - Layout and positioning
   - Styling (colors, borders, shadows)
   - Typography (fonts, sizes, weights)
   - Spacing (margins, padding)
   - Element sizes and proportions
   - Icons and images
4. Use modern web standards and best practices
5. The HTML should be self-contained (no external dependencies)
6. Return ONLY the HTML code, no explanations or markdown formatting

Focus on making the visual output as close as possible to the ground truth image."""

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _get_image_mime_type(self, image_path: str) -> str:
        """Get MIME type from image extension."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')

    def _clean_html_response(self, html: str) -> str:
        """Clean HTML response by removing markdown formatting."""
        # Remove markdown code blocks
        if "```html" in html:
            html = html.split("```html")[1].split("```")[0]
        elif "```" in html:
            html = html.split("```")[1].split("```")[0]

        return html.strip()

    def refine_html(
        self,
        ground_truth_path: str,
        generated_screenshot_path: str
    ) -> str:
        """
        Generate refined HTML by comparing ground truth with generated visualization.

        Args:
            ground_truth_path: Path to the ground truth screenshot
            generated_screenshot_path: Path to the generated HTML visualization

        Returns:
            Refined HTML code
        """
        if not os.path.exists(ground_truth_path):
            raise FileNotFoundError(f"Ground truth image not found: {ground_truth_path}")
        if not os.path.exists(generated_screenshot_path):
            raise FileNotFoundError(f"Generated screenshot not found: {generated_screenshot_path}")

        # Encode both images
        ground_truth_b64 = self._encode_image(ground_truth_path)
        generated_b64 = self._encode_image(generated_screenshot_path)

        gt_mime = self._get_image_mime_type(ground_truth_path)
        gen_mime = self._get_image_mime_type(generated_screenshot_path)

        # Construct user message with both images
        user_prompt = """Here are two images:

1. GROUND TRUTH: This is the target interface you need to match.
2. PREVIOUS ATTEMPT: This is what your previous HTML code generated.

Please analyze the differences and generate improved HTML code that better matches the ground truth."""

        # Prepare messages with both images
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{gt_mime};base64,{ground_truth_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{gen_mime};base64,{generated_b64}"
                        }
                    }
                ]
            }
        ]

        # Call VLM
        print("  Refining HTML using ground truth comparison...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0
            )

            html_code = response.choices[0].message.content
            html_code = self._clean_html_response(html_code)

            print("  ✓ Refined HTML generated successfully!")
            return html_code

        except Exception as e:
            print(f"  ✗ Error calling VLM: {e}")
            raise

    def render_html(self, html_code: str, output_path: str) -> Optional[str]:
        """
        Render HTML and capture screenshot using headless Chrome.

        Args:
            html_code: HTML code to render
            output_path: Path where screenshot should be saved

        Returns:
            Path to screenshot if successful, None otherwise
        """
        # Create a temporary HTML file for rendering
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_code)
            temp_html_path = f.name

        try:
            # Try to render with Playwright in headless mode
            try:
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 480, 'height': 800},
                        device_scale_factor=2
                    )
                    page = context.new_page()

                    # Load HTML
                    page.goto(f"file://{Path(temp_html_path).absolute()}")

                    # Wait for page to be fully loaded
                    page.wait_for_load_state('networkidle')

                    # Take screenshot
                    page.screenshot(path=str(output_path), full_page=True)

                    browser.close()

                return str(output_path)

            except ImportError:
                print("  Warning: Playwright not installed. Skipping screenshot rendering.")
                return None

            except Exception as e:
                print(f"  Warning: Error rendering HTML: {e}")
                return None

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_html_path)
            except Exception:
                pass

    def find_latest_generated_file(self, generated_dir: Path, step_name: str, subdir: str) -> Optional[Path]:
        """
        Find the latest generated file for a given step.

        Args:
            generated_dir: Path to the generated directory
            step_name: Step name (e.g., 'episode_27_step_00')
            subdir: Subdirectory name ('html' or 'screenshots')

        Returns:
            Path to the latest file, or None if not found
        """
        target_dir = generated_dir / subdir
        if not target_dir.exists():
            return None

        # Find all files matching the step name
        pattern = f"{step_name}_*.{'html' if subdir == 'html' else 'png'}"
        matching_files = sorted(target_dir.glob(pattern))

        if not matching_files:
            return None

        # Return the most recent (last in sorted list)
        return matching_files[-1]

    def refine_episode(
        self,
        episode_dir: Path,
        episode_id: int
    ) -> dict:
        """
        Refine all generated HTML for a single episode.

        Args:
            episode_dir: Path to the episode directory
            episode_id: Episode ID number

        Returns:
            Dictionary with refinement statistics
        """
        stats = {
            'episode_id': episode_id,
            'steps_processed': 0,
            'steps_skipped': 0,
            'errors': []
        }

        generated_dir = episode_dir / "generated"

        # Check if generated directory exists
        if not generated_dir.exists():
            stats['errors'].append("No 'generated' directory found")
            return stats

        # Create regenerated directory
        regenerated_dir = episode_dir / "regenerated"
        regenerated_dir.mkdir(exist_ok=True)

        # Create subdirectories
        for subdir in ['html', 'screenshots', 'logs']:
            (regenerated_dir / subdir).mkdir(exist_ok=True)

        # Find all ground truth images
        ground_truth_images = sorted(episode_dir.glob(f"episode_{episode_id}_step_*.png"))

        if not ground_truth_images:
            stats['errors'].append("No ground truth images found")
            return stats

        print(f"  Found {len(ground_truth_images)} ground truth images")

        # Process each ground truth image
        for gt_image in ground_truth_images:
            step_name = gt_image.stem  # e.g., 'episode_27_step_00'

            # Find corresponding generated screenshot
            generated_screenshot = self.find_latest_generated_file(
                generated_dir, step_name, 'screenshots'
            )

            if not generated_screenshot:
                print(f"  ⊘ Skipping {step_name}: No generated screenshot found")
                stats['steps_skipped'] += 1
                continue

            # Check if this step has already been refined (resume functionality)
            refined_html_dir = regenerated_dir / "html"
            existing_refined = list(refined_html_dir.glob(f"{step_name}_refined_*.html")) if refined_html_dir.exists() else []

            if existing_refined:
                print(f"  ⊘ Skipping {step_name}: Already refined")
                stats['steps_skipped'] += 1
                continue

            try:
                print(f"  Processing {step_name}...")

                # Refine the HTML
                refined_html = self.refine_html(
                    ground_truth_path=str(gt_image),
                    generated_screenshot_path=str(generated_screenshot)
                )

                # Save refined HTML
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                html_filename = f"{step_name}_refined_{timestamp}.html"
                screenshot_filename = f"{step_name}_refined_{timestamp}.png"

                html_path = regenerated_dir / "html" / html_filename
                screenshot_path = regenerated_dir / "screenshots" / screenshot_filename

                # Save HTML
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(refined_html)
                print(f"    ✓ Saved refined HTML: {html_path.name}")

                # Render and save screenshot
                rendered_path = self.render_html(refined_html, str(screenshot_path))
                if rendered_path:
                    print(f"    ✓ Saved refined screenshot: {screenshot_path.name}")

                # Log refinement
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "step_name": step_name,
                    "ground_truth": str(gt_image),
                    "generated_screenshot": str(generated_screenshot),
                    "refined_html": str(html_path),
                    "refined_screenshot": str(screenshot_path) if rendered_path else None
                }

                log_file = regenerated_dir / "logs" / f"refinement_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')

                stats['steps_processed'] += 1

            except Exception as e:
                error_msg = f"Error processing {step_name}: {e}"
                print(f"  ✗ {error_msg}")
                stats['errors'].append(error_msg)
                stats['steps_skipped'] += 1

        return stats

    def refine_episode_range(
        self,
        start_id: int,
        end_id: int,
        base_dir: Optional[Path] = None
    ) -> dict:
        """
        Refine all episodes in a given ID range.

        Args:
            start_id: Starting episode ID (inclusive)
            end_id: Ending episode ID (inclusive)
            base_dir: Base directory containing episode subdirectories

        Returns:
            Dictionary with overall statistics
        """
        if base_dir is None:
            base_dir = self.episode_base_dir

        if base_dir is None:
            raise ValueError("No episode base directory specified")

        base_dir = Path(base_dir)

        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory not found: {base_dir}")

        print("="*70)
        print("HTML Refinement Pipeline")
        print("="*70)
        print(f"Base directory: {base_dir}")
        print(f"Episode ID range: {start_id} to {end_id}")
        print("="*70)

        overall_stats = {
            'total_episodes': 0,
            'episodes_processed': 0,
            'episodes_skipped': 0,
            'total_steps_processed': 0,
            'total_steps_skipped': 0,
            'episode_details': []
        }

        # Process each episode in range
        for episode_id in range(start_id, end_id + 1):
            episode_dir = base_dir / f"episode_{episode_id}"

            overall_stats['total_episodes'] += 1

            # Check if episode directory exists
            if not episode_dir.exists():
                print(f"\n⊘ Episode {episode_id}: Directory not found, skipping")
                overall_stats['episodes_skipped'] += 1
                continue

            # Check if generated directory exists
            generated_dir = episode_dir / "generated"
            if not generated_dir.exists():
                print(f"\n⊘ Episode {episode_id}: No 'generated' directory, skipping")
                overall_stats['episodes_skipped'] += 1
                continue

            print(f"\n{'='*70}")
            print(f"Processing Episode {episode_id}")
            print('='*70)

            # Refine this episode
            episode_stats = self.refine_episode(episode_dir, episode_id)

            overall_stats['episodes_processed'] += 1
            overall_stats['total_steps_processed'] += episode_stats['steps_processed']
            overall_stats['total_steps_skipped'] += episode_stats['steps_skipped']
            overall_stats['episode_details'].append(episode_stats)

            if episode_stats['steps_skipped'] > 0:
                print(f"✓ Episode {episode_id} complete: {episode_stats['steps_processed']} steps processed, "
                      f"{episode_stats['steps_skipped']} skipped (already refined or missing generated files)")
            else:
                print(f"✓ Episode {episode_id} complete: {episode_stats['steps_processed']} steps processed")

        # Print final summary
        print("\n" + "="*70)
        print("REFINEMENT COMPLETE")
        print("="*70)
        print(f"Episodes processed: {overall_stats['episodes_processed']}/{overall_stats['total_episodes']}")
        print(f"Episodes skipped: {overall_stats['episodes_skipped']}")
        print(f"Total steps processed: {overall_stats['total_steps_processed']}")
        print(f"Total steps skipped: {overall_stats['total_steps_skipped']}")
        print("="*70)

        return overall_stats


def main():
    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Episode ID range to process
    start_id = 1
    end_id = 1111

    # Base directory containing episode subdirectories
    base_dir = "/Users/reisskoh/androidworld/mwm/query/episode_visualizations"

    # VLM server settings
    base_url = "http://localhost:8080/v1"
    model = "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8"

    # ========================================================================
    # END CONFIGURATION
    # ========================================================================

    # Validate parameters
    if start_id < 1:
        print("Error: start_id must be >= 1")
        sys.exit(1)

    if end_id < start_id:
        print("Error: end_id must be >= start_id")
        sys.exit(1)

    # Initialize refiner
    refiner = HTMLRefiner(
        base_url=base_url,
        model=model,
        episode_base_dir=base_dir
    )

    # Run refinement
    try:
        stats = refiner.refine_episode_range(start_id, end_id)

        # Save summary statistics
        summary_path = Path(base_dir) / f"refinement_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        print(f"\nSummary saved to: {summary_path}")

    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
