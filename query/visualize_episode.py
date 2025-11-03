"""
Script to visualize a specific episode from the android-control dataset.

This script loads an episode and displays each screenshot with its corresponding
action and instruction step-by-step.
"""

import json
import base64
import io
import os
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datasets import load_dataset


def load_episode_from_dataset(dataset_name, episode_id, split='train'):
    """
    Load a specific episode from the HuggingFace dataset.

    Args:
        dataset_name: Name of the HuggingFace dataset
        episode_id: ID of the episode to load
        split: Dataset split to load from (default: 'train')

    Returns:
        Episode dictionary or None if not found
    """
    print(f"Loading dataset '{dataset_name}' from HuggingFace cache...")

    try:
        dataset = load_dataset(dataset_name, split=split)
        print(f"Dataset loaded successfully. Total episodes: {len(dataset)}")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

    # Search for episode by episode_id
    for idx, episode in enumerate(dataset):
        if episode.get('episode_id') == episode_id:
            print(f"Found episode {episode_id} at index {idx}")
            return episode

    # Episode not found - show some available IDs
    print(f"\nEpisode {episode_id} not found in dataset")
    print("Note: Episode IDs are not sequential and have gaps.")

    # Collect first 30 episode IDs to show examples
    available_ids = []
    for idx, episode in enumerate(dataset):
        if idx >= 30:
            break
        available_ids.append(episode.get('episode_id'))

    print(f"\nFirst 30 available episode IDs:")
    print(sorted(available_ids))

    return None


def decode_screenshot(b64_string):
    """
    Decode base64 screenshot string to PIL Image.

    Args:
        b64_string: Base64 encoded image string

    Returns:
        PIL Image object
    """
    if not b64_string:
        return None

    img_data = base64.b64decode(b64_string)
    img = Image.open(io.BytesIO(img_data))
    return img


def format_action(action):
    """
    Format action dictionary into readable string.

    Args:
        action: Action dictionary

    Returns:
        Formatted action string
    """
    action_type = action.get('action_type', 'unknown')

    if action_type == 'open_app':
        return f"OPEN APP: {action.get('app_name', 'N/A')}"
    elif action_type == 'click':
        x = action.get('x', 'N/A')
        y = action.get('y', 'N/A')
        return f"CLICK: ({x}, {y})"
    elif action_type == 'scroll':
        direction = action.get('direction', 'N/A')
        return f"SCROLL: {direction}"
    elif action_type == 'type':
        text = action.get('text', 'N/A')
        return f"TYPE: '{text}'"
    else:
        return f"{action_type.upper()}: {action}"


def visualize_episode_step(episode, step_idx, save_dir=None):
    """
    Visualize a single step of an episode.

    Args:
        episode: Episode dictionary
        step_idx: Index of the step to visualize
        save_dir: Optional directory to save the visualization
    """
    screenshots = episode.get('screenshots_b64', [])
    actions = episode.get('actions', [])
    instructions = episode.get('step_instructions', [])
    goal = episode.get('goal', 'No goal specified')
    episode_id = episode.get('episode_id', 'unknown')

    # Check if step index is valid
    if step_idx >= len(actions):
        print(f"Step {step_idx} is out of range. Episode has {len(actions)} steps.")
        return

    # Get data for this step
    action = actions[step_idx]
    instruction = instructions[step_idx] if step_idx < len(instructions) else 'No instruction'
    screenshot = decode_screenshot(screenshots[step_idx]) if step_idx < len(screenshots) else None

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 16))

    if screenshot:
        ax.imshow(screenshot)

        # Draw click location if it's a click action
        if action.get('action_type') == 'click' and action.get('x') and action.get('y'):
            x, y = action['x'], action['y']
            circle = patches.Circle((x, y), 30, linewidth=3, edgecolor='red', facecolor='none')
            ax.add_patch(circle)
            # Add crosshair
            ax.plot([x-40, x+40], [y, y], 'r-', linewidth=2)
            ax.plot([x, x], [y-40, y+40], 'r-', linewidth=2)
    else:
        ax.text(0.5, 0.5, 'No screenshot available',
                ha='center', va='center', fontsize=20)

    ax.axis('off')

    # Add title with step information
    title = f"Episode {episode_id} - Step {step_idx + 1}/{len(actions)}\n\n"
    title += f"Goal: {goal}\n\n"
    title += f"Instruction: {instruction}\n"
    title += f"Action: {format_action(action)}"

    plt.title(title, fontsize=12, pad=20, wrap=True)
    plt.tight_layout()

    # Save or show
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, f"episode_{episode_id}_step_{step_idx:02d}.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to: {output_path}")

        # Save raw screenshot to 'image' subdirectory
        if screenshot:
            image_dir = os.path.join(save_dir, "image")
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"episode_{episode_id}_step_{step_idx:02d}.png")
            screenshot.save(image_path)
            print(f"Saved raw image to: {image_path}")
    else:
        plt.show()

    plt.close()


def visualize_episode_interactive(episode):
    """
    Visualize episode with interactive step-by-step navigation.

    Args:
        episode: Episode dictionary
    """
    screenshots = episode.get('screenshots_b64', [])
    actions = episode.get('actions', [])
    instructions = episode.get('step_instructions', [])
    goal = episode.get('goal', 'No goal specified')
    episode_id = episode.get('episode_id', 'unknown')

    num_steps = len(actions)

    print("="*80)
    print(f"EPISODE {episode_id} VISUALIZATION")
    print("="*80)
    print(f"Goal: {goal}")
    print(f"Total steps: {num_steps}")
    print("="*80)
    print()

    # Create interactive plot
    current_step = [0]  # Use list to allow modification in nested function

    fig, ax = plt.subplots(figsize=(10, 16))
    plt.subplots_adjust(bottom=0.15)

    def update_display(step_idx):
        """Update the display for the given step."""
        ax.clear()

        action = actions[step_idx]
        instruction = instructions[step_idx] if step_idx < len(instructions) else 'No instruction'
        screenshot = decode_screenshot(screenshots[step_idx]) if step_idx < len(screenshots) else None

        if screenshot:
            ax.imshow(screenshot)

            # Draw click location if it's a click action
            if action.get('action_type') == 'click' and action.get('x') and action.get('y'):
                x, y = action['x'], action['y']
                circle = patches.Circle((x, y), 30, linewidth=3, edgecolor='red', facecolor='none')
                ax.add_patch(circle)
                # Add crosshair
                ax.plot([x-40, x+40], [y, y], 'r-', linewidth=2)
                ax.plot([x, x], [y-40, y+40], 'r-', linewidth=2)
        else:
            ax.text(0.5, 0.5, 'No screenshot available',
                    ha='center', va='center', fontsize=20)

        ax.axis('off')

        # Add title with step information
        title = f"Episode {episode_id} - Step {step_idx + 1}/{num_steps}\n\n"
        title += f"Goal: {goal}\n\n"
        title += f"Instruction: {instruction}\n"
        title += f"Action: {format_action(action)}"

        ax.set_title(title, fontsize=12, pad=20, wrap=True)
        fig.canvas.draw_idle()

    def on_key(event):
        """Handle keyboard events for navigation."""
        if event.key == 'right' or event.key == 'n':
            current_step[0] = min(current_step[0] + 1, num_steps - 1)
            update_display(current_step[0])
        elif event.key == 'left' or event.key == 'p':
            current_step[0] = max(current_step[0] - 1, 0)
            update_display(current_step[0])
        elif event.key == 'q':
            plt.close()

    # Connect keyboard handler
    fig.canvas.mpl_connect('key_press_event', on_key)

    # Initial display
    update_display(0)

    # Add navigation instructions
    fig.text(0.5, 0.05,
             'Navigation: [←/p] Previous  [→/n] Next  [q] Quit',
             ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.show()


def visualize_all_steps(episode, save_dir=None):
    """
    Visualize all steps of an episode.

    Args:
        episode: Episode dictionary
        save_dir: Optional directory to save visualizations
    """
    actions = episode.get('actions', [])
    num_steps = len(actions)

    print(f"Visualizing all {num_steps} steps...")

    for step_idx in range(num_steps):
        visualize_episode_step(episode, step_idx, save_dir)
        print(f"Completed step {step_idx + 1}/{num_steps}")


def main():
    """Main function to visualize episodes."""

    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Episode ID range to visualize (start, end) - set to None to use single EPISODE_ID
    EPISODE_ID_RANGE = (11, 1111)  # Will process all available IDs in this range

    # Single Episode ID (only used if EPISODE_ID_RANGE is None)
    EPISODE_ID = 1111

    # HuggingFace dataset name
    DATASET_NAME = 'smolagents/android-control'

    # Dataset split to load from
    SPLIT = 'train'

    # Visualization mode:
    # 'interactive' - Navigate through steps with keyboard
    # 'all' - Generate and save all steps as images
    # 'single' - Show a single step
    MODE = 'all'

    # If MODE is 'single', which step to show (0-indexed)
    SINGLE_STEP_INDEX = 0

    # If MODE is 'all', directory to save images
    SAVE_DIR = 'episode_visualizations'

    # ========================================================================
    # END CONFIGURATION
    # ========================================================================

    # Determine which episode IDs to process
    if EPISODE_ID_RANGE is not None:
        start_id, end_id = EPISODE_ID_RANGE
        target_episode_ids = set(range(start_id, end_id + 1))
        print(f"Processing episode ID range: {start_id} to {end_id}")
        print(f"Searching for episodes in this range...")
        print("="*60)
    else:
        target_episode_ids = {EPISODE_ID}

    # Load dataset and process episodes one by one (memory efficient)
    from datasets import load_dataset
    print(f"Loading dataset '{DATASET_NAME}' from HuggingFace cache...")
    try:
        dataset = load_dataset(DATASET_NAME, split=SPLIT)
        print(f"Dataset loaded successfully. Total episodes: {len(dataset)}")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Process episodes as we iterate (don't load all into memory)
    processed_count = 0
    for idx, episode in enumerate(dataset):
        ep_id = episode.get('episode_id')

        # Skip if not in our target range
        if ep_id not in target_episode_ids:
            continue

        processed_count += 1

        print(f"\n{'='*60}")
        print(f"Processing Episode {ep_id} ({processed_count} found)")
        print(f"Goal: {episode.get('goal', 'No goal specified')}")
        print(f"Number of steps: {len(episode.get('actions', []))}")
        print('='*60)

        # Visualize based on mode
        if MODE == 'interactive':
            if EPISODE_ID_RANGE is not None:
                print(f"Warning: Interactive mode with range will show episodes one by one")
            print("Starting interactive visualization...")
            print("Use arrow keys or n/p to navigate, q to quit")
            visualize_episode_interactive(episode)
        elif MODE == 'all':
            # Create subdirectory for each episode if processing a range
            if EPISODE_ID_RANGE is not None:
                save_dir = f"{SAVE_DIR}/episode_{ep_id}"
            else:
                save_dir = SAVE_DIR
            visualize_all_steps(episode, save_dir)
            print(f"Visualizations saved to: {save_dir}")
        elif MODE == 'single':
            visualize_episode_step(episode, SINGLE_STEP_INDEX)
        else:
            print(f"Error: Unknown mode '{MODE}'")
            print("Valid modes: 'interactive', 'all', 'single'")
            return

    # Summary
    if processed_count == 0:
        print(f"\nNo episodes found in the specified range.")
        if EPISODE_ID_RANGE is None:
            print(f"Episode {EPISODE_ID} not found in dataset")
    elif EPISODE_ID_RANGE is not None:
        print(f"\n{'='*60}")
        print(f"Batch complete! Processed {processed_count} episodes")
        print(f"Results saved to: {SAVE_DIR}")
        print('='*60)


if __name__ == '__main__':
    main()
