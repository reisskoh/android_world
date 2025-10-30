"""
Script to inspect what parameters different task templates use.
This helps understand what changes when you increase N_VARIATIONS.
"""

from android_world import registry
from android_world.task_evals import task_eval
import json


def inspect_task_parameters(family='android_world', n_samples=3):
    """
    Show what parameters each task template uses and how they vary.

    Args:
        family: Task family to inspect
        n_samples: Number of random parameter samples to generate per task
    """
    task_registry = registry.TaskRegistry()
    task_dict = task_registry.get_registry(family=family)

    print(f"Inspecting {len(task_dict)} task templates from '{family}' family")
    print("="*80)

    for i, (task_name, task_class) in enumerate(sorted(task_dict.items())[:10], 1):
        print(f"\n{i}. {task_name}")
        print("-" * 80)

        # Show the template string
        template = task_class.template
        print(f"Template: {template}")

        # Show the schema (defines what parameters this task accepts)
        schema = task_class.schema
        print(f"\nParameter Schema:")
        print(json.dumps(schema, indent=2))

        # Generate multiple random parameter samples
        print(f"\nSample Parameter Variations (showing {n_samples} examples):")
        for j in range(n_samples):
            params = task_class.generate_random_params()
            # Remove seed from display for clarity
            display_params = {k: v for k, v in params.items() if k != 'seed'}
            print(f"  Variation {j+1}: {json.dumps(display_params, indent=4)}")

            # Show the resulting goal/query
            task_instance = task_class(params)
            print(f"  → Goal: {task_instance.goal}")

        print()

    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    print("- Each task template has a TEMPLATE STRING with placeholders (e.g., {name})")
    print("- Each task template defines a SCHEMA showing what parameters it needs")
    print("- generate_random_params() creates random values for these parameters")
    print("- N_VARIATIONS controls how many different random parameter sets to generate")
    print(f"- With N_VARIATIONS=5, you get 5 different random parameter combinations per task")
    print(f"- Total queries = {len(task_dict)} templates × N_VARIATIONS")


def compare_variations_for_task(task_name='ContactsAddContact', n_variations=5):
    """
    Deep dive into one specific task to see how variations work.

    Args:
        task_name: Name of the task to inspect
        n_variations: Number of variations to generate
    """
    task_registry = registry.TaskRegistry()
    task_dict = task_registry.get_registry(family='android_world')

    if task_name not in task_dict:
        print(f"Task '{task_name}' not found!")
        return

    task_class = task_dict[task_name]

    print(f"\nDETAILED ANALYSIS: {task_name}")
    print("="*80)
    print(f"Template String: {task_class.template}")
    print(f"\nGenerating {n_variations} different parameter variations:\n")

    for i in range(n_variations):
        params = task_class.generate_random_params()
        task_instance = task_class(params)

        print(f"Variation {i+1}:")
        print(f"  Parameters: {json.dumps({k: v for k, v in params.items() if k != 'seed'}, indent=6)}")
        print(f"  Final Goal: {task_instance.goal}")
        print()


def main():
    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Choose what to inspect:
    # Option 1: Overview of first 10 tasks
    OVERVIEW_MODE = True

    # Option 2: Deep dive into a specific task
    DEEP_DIVE_MODE = True
    TASK_TO_INSPECT = 'ContactsAddContact'

    # Number of sample variations to show
    N_SAMPLE_VARIATIONS = 3

    # ========================================================================

    if OVERVIEW_MODE:
        print("\n" + "="*80)
        print("OVERVIEW: First 10 Task Templates")
        print("="*80)
        inspect_task_parameters(family='android_world', n_samples=N_SAMPLE_VARIATIONS)

    if DEEP_DIVE_MODE:
        print("\n" + "="*80)
        print("DEEP DIVE: Single Task Analysis")
        print("="*80)
        compare_variations_for_task(
            task_name=TASK_TO_INSPECT,
            n_variations=N_SAMPLE_VARIATIONS
        )


if __name__ == '__main__':
    main()
