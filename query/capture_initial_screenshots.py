"""
Script to capture initial screenshots for all task queries.

This script loads the queries dataset and captures the initial phone screen
that an agent would see when receiving each task instruction.

Screenshots are saved with the same ID as in queries_dataset.json for easy linking.
"""

import json
import os
import numpy as np
from PIL import Image
from android_world import registry
from android_world.env import env_launcher
from android_world.task_evals import task_eval


def find_adb_directory():
    """Returns the directory where adb is located."""
    potential_paths = [
        os.path.expanduser('~/Library/Android/sdk/platform-tools/adb'),
        os.path.expanduser('~/Android/Sdk/platform-tools/adb'),
    ]
    for path in potential_paths:
        if os.path.isfile(path):
            return path
    raise EnvironmentError(
        'adb not found in the common Android SDK paths.'
    )


def capture_screenshots_for_queries(
    queries_file='queries_dataset.json',
    output_dir='screenshots_dataset',
    console_port=5554,
    adb_path=None,
    save_format='both',  # 'png', 'npy', or 'both'
    max_tasks=None,  # Set to limit number of tasks (for testing)
    update_original_json=True,  # Whether to update queries_dataset.json with screenshot paths
):
    """
    Capture initial screenshots for all queries.

    Screenshots are saved using the query 'id' field, making linking trivial:
    - Query ID: "ContactsAddContact_0"
    - Screenshot: "ContactsAddContact_0.png" and/or "ContactsAddContact_0.npy"

    Args:
        queries_file: Path to the queries JSON file
        output_dir: Directory to save screenshots
        console_port: Android device console port
        adb_path: Path to adb binary
        save_format: Format to save screenshots ('png', 'npy', or 'both')
        max_tasks: Maximum number of tasks to process (None = all)
        update_original_json: If True, adds screenshot_path fields to original queries file

    Returns:
        Updated dataset with queries and screenshot paths
    """
    # Load queries
    print(f"Loading queries from {queries_file}...")
    with open(queries_file, 'r') as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} queries")

    # Limit tasks if specified
    if max_tasks:
        queries = queries[:max_tasks]
        print(f"Processing only first {max_tasks} tasks")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Find adb if not provided
    if adb_path is None:
        adb_path = find_adb_directory()

    # Setup environment
    print(f"\nSetting up Android environment on port {console_port}...")
    env = env_launcher.load_and_setup_env(
        console_port=console_port,
        emulator_setup=False,  # Assuming emulator is already set up
        adb_path=adb_path,
    )

    # Get task registry
    task_registry = registry.TaskRegistry()
    all_tasks = task_registry.get_registry(family='android_world')

    # Process each query
    updated_queries = []
    failed_tasks = []
    success_count = 0

    for i, query_data in enumerate(queries):
        task_name = query_data['task_template']
        variation_id = query_data['variation_id']
        query_id = query_data['id']

        print(f"\n[{i+1}/{len(queries)}] Processing {query_id}...")

        try:
            # Get task class
            task_class = all_tasks[task_name]

            # Create task instance with original parameters
            params = query_data['params']
            task = task_class(params)

            # Initialize the task (this sets up the initial state)
            print(f"  Initializing: {task.goal}")
            task.initialize_task(env)

            # Get initial state (this is what the agent sees first)
            print(f"  Capturing initial screenshot...")
            env.reset(go_home=task.start_on_home_screen)
            initial_state = env.get_state(wait_to_stabilize=True)

            # Extract screenshot
            screenshot = initial_state.pixels  # numpy array

            # Save screenshot using the query ID
            screenshot_paths = {}

            if save_format in ['png', 'both']:
                png_filename = f"{query_id}.png"
                png_path = os.path.join(output_dir, png_filename)
                # Convert numpy array to PIL Image and save
                img = Image.fromarray(screenshot.astype('uint8'))
                img.save(png_path)
                screenshot_paths['png'] = png_filename  # Store relative filename
                print(f"  Saved PNG: {png_filename}")

            if save_format in ['npy', 'both']:
                npy_filename = f"{query_id}.npy"
                npy_path = os.path.join(output_dir, npy_filename)
                np.save(npy_path, screenshot)
                screenshot_paths['npy'] = npy_filename  # Store relative filename
                print(f"  Saved NPY: {npy_filename}")

            # Update query data with screenshot information
            query_data_updated = query_data.copy()
            query_data_updated['screenshot_png'] = screenshot_paths.get('png', None)
            query_data_updated['screenshot_npy'] = screenshot_paths.get('npy', None)
            query_data_updated['screenshot_shape'] = list(screenshot.shape)

            updated_queries.append(query_data_updated)

            # Teardown task
            task.tear_down(env)
            success_count += 1
            print(f"  ✅ Success")

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed_tasks.append({
                'id': query_id,
                'task_name': task_name,
                'error': str(e)
            })
            # Still add to updated_queries but without screenshot
            query_data_updated = query_data.copy()
            query_data_updated['screenshot_png'] = None
            query_data_updated['screenshot_npy'] = None
            query_data_updated['screenshot_shape'] = None
            query_data_updated['error'] = str(e)
            updated_queries.append(query_data_updated)

    # Close environment
    env.close()

    # Save updated dataset
    if update_original_json:
        # Update the original queries file with screenshot paths
        output_file = queries_file.replace('.json', '_with_screenshots.json')
        with open(output_file, 'w') as f:
            json.dump(updated_queries, f, indent=2)
        print(f"\n✅ Updated queries saved to: {output_file}")
    else:
        # Save to output directory
        output_file = os.path.join(output_dir, 'queries_with_screenshots.json')
        with open(output_file, 'w') as f:
            json.dump(updated_queries, f, indent=2)
        print(f"\n✅ Queries with screenshots saved to: {output_file}")

    # Create README for easy understanding
    readme_path = os.path.join(output_dir, 'README.txt')
    with open(readme_path, 'w') as f:
        f.write("AndroidWorld Dataset - Screenshots\n")
        f.write("=" * 80 + "\n\n")
        f.write("This directory contains initial screenshots for AndroidWorld tasks.\n\n")
        f.write("File naming convention:\n")
        f.write("  - Each screenshot is named using the query ID from queries_dataset.json\n")
        f.write("  - Example: 'ContactsAddContact_0.png' corresponds to query with id='ContactsAddContact_0'\n\n")
        f.write("How to link screenshots to queries:\n")
        f.write("  1. Load queries_with_screenshots.json (or queries_dataset_with_screenshots.json)\n")
        f.write("  2. Each query has 'screenshot_png' and/or 'screenshot_npy' fields\n")
        f.write("  3. The values are filenames in this directory\n\n")
        f.write(f"Statistics:\n")
        f.write(f"  - Total queries: {len(queries)}\n")
        f.write(f"  - Successfully captured: {success_count}\n")
        f.write(f"  - Failed: {len(failed_tasks)}\n")

    print(f"\n{'='*80}")
    print("DATASET CREATION COMPLETE")
    print(f"{'='*80}")
    print(f"Successfully captured: {success_count}/{len(queries)} screenshots")
    print(f"Failed: {len(failed_tasks)} tasks")
    print(f"Screenshot directory: {output_dir}")
    print(f"Updated queries file: {output_file}")
    print(f"README: {readme_path}")

    # Save failed tasks log if any
    if failed_tasks:
        failed_log_path = os.path.join(output_dir, 'failed_tasks.json')
        with open(failed_log_path, 'w') as f:
            json.dump(failed_tasks, f, indent=2)
        print(f"Failed tasks logged to: {failed_log_path}")

    return updated_queries


def main():
    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Path to the queries JSON file (generated by generate_queries.py)
    QUERIES_FILE = 'queries_dataset.json'

    # Directory to save screenshots
    OUTPUT_DIR = 'screenshots_dataset'

    # Android device console port
    CONSOLE_PORT = 5554

    # Path to adb (None = auto-detect)
    ADB_PATH = None

    # Screenshot save format: 'png', 'npy', or 'both'
    # - 'png': Human-readable images (good for visualization)
    # - 'npy': Numpy arrays (good for ML training, smaller file size)
    # - 'both': Save in both formats
    SAVE_FORMAT = 'both'

    # Maximum number of tasks to process (None = all)
    # Set to a small number (e.g., 5) for testing first!
    MAX_TASKS = 5

    # Whether to create a new file with screenshots or update queries inline
    UPDATE_ORIGINAL_JSON = True  # Creates queries_dataset_with_screenshots.json

    # ========================================================================
    # END CONFIGURATION
    # ========================================================================

    print("="*80)
    print("ANDROIDWORLD SCREENSHOT CAPTURE")
    print("="*80)
    print(f"Input file: {QUERIES_FILE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Screenshot format: {SAVE_FORMAT}")
    print(f"Max tasks: {MAX_TASKS if MAX_TASKS else 'ALL'}")
    print("="*80)

    dataset = capture_screenshots_for_queries(
        queries_file=QUERIES_FILE,
        output_dir=OUTPUT_DIR,
        console_port=CONSOLE_PORT,
        adb_path=ADB_PATH,
        save_format=SAVE_FORMAT,
        max_tasks=MAX_TASKS,
        update_original_json=UPDATE_ORIGINAL_JSON,
    )

    print(f"\n✅ Dataset created with {len(dataset)} entries")
    print("\nHow to use the dataset:")
    print("  1. Load queries_dataset_with_screenshots.json")
    print("  2. Each entry has 'query' and 'screenshot_png'/'screenshot_npy' fields")
    print("  3. Screenshot files are in screenshots_dataset/ directory")
    print("\nExample:")
    print("  query_id = 'ContactsAddContact_0'")
    print("  screenshot = 'screenshots_dataset/ContactsAddContact_0.png'")


if __name__ == '__main__':
    main()
