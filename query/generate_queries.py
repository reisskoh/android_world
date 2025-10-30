"""
Script to generate all task queries with configurable parameter variations.

This script generates queries from AndroidWorld task templates. Each template
can be instantiated multiple times with different random parameters.
"""

import json
from android_world import registry
from android_world import suite_utils


def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert non-serializable objects to string representation
        return str(obj)


def count_task_templates(family='android_world'):
    """Count the number of base task templates."""
    task_registry = registry.TaskRegistry()
    task_dict = task_registry.get_registry(family=family)
    return len(task_dict)


def generate_all_queries(
    family='android_world',
    n_variations=1,
    seed=42,
    output_file='queries_dataset.json',
    specific_tasks=None,
):
    """
    Generate all task queries with parameter variations.

    Args:
        family: Task family to use (android_world, android, information_retrieval, etc.)
        n_variations: Number of parameter variations per task template
        seed: Random seed for reproducibility
        output_file: Path to save the output JSON file
        specific_tasks: Optional list of specific task names to generate

    Returns:
        List of query dictionaries
    """
    task_registry = registry.TaskRegistry()

    print(f"Generating queries for family: {family}")
    print(f"Variations per task: {n_variations}")
    print(f"Random seed: {seed}")

    # Create suite with specified parameters
    suite = suite_utils.create_suite(
        task_registry.get_registry(family=family),
        n_task_combinations=n_variations,
        seed=seed,
        tasks=specific_tasks,
        use_identical_params=False,  # Each variation gets different params
        env=None,  # No environment needed for query generation
    )

    print(f"\nFound {len(suite)} task templates")
    print(f"Total queries to generate: {len(suite) * n_variations}")

    # Extract all queries
    queries_dataset = []

    for task_name, instances in suite.items():
        print(f"Processing {task_name}: {len(instances)} variations")

        for i, task in enumerate(instances):
            query_data = {
                'id': f"{task_name}_{i}",
                'task_template': task_name,
                'variation_id': i,
                'query': task.goal,
                'template_string': task.template,
                'params': make_json_serializable(task.params),
                'complexity': task.complexity,
                'app_names': list(task.app_names) if task.app_names else [],
                'seed': task.params.get('seed', None),
            }

            queries_dataset.append(query_data)

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(queries_dataset, f, indent=2)

    print(f"\n✅ Saved {len(queries_dataset)} queries to {output_file}")

    # Print statistics
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"Total task templates: {len(suite)}")
    print(f"Variations per template: {n_variations}")
    print(f"Total queries: {len(queries_dataset)}")
    print(f"Output file: {output_file}")

    return queries_dataset


def print_sample_queries(queries_dataset, n=5):
    """Print sample queries from each task template."""
    print("\n" + "="*60)
    print(f"SAMPLE QUERIES (first {n} tasks)")
    print("="*60)

    seen_templates = set()
    count = 0

    for q in queries_dataset:
        if q['task_template'] not in seen_templates:
            print(f"\nTask: {q['task_template']}")
            print(f"Query: {q['query']}")
            print(f"Params: {json.dumps(q['params'], indent=2)}")
            print(f"Complexity: {q['complexity']}")

            seen_templates.add(q['task_template'])
            count += 1

            if count >= n:
                break


def list_all_task_templates(family='android_world'):
    """List all available task templates in a family."""
    task_registry = registry.TaskRegistry()
    task_dict = task_registry.get_registry(family=family)

    print(f"\nAvailable task templates in '{family}' family:")
    print("="*60)

    for i, task_name in enumerate(sorted(task_dict.keys()), 1):
        print(f"{i:3d}. {task_name}")

    print(f"\nTotal: {len(task_dict)} task templates")


def main():
    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Task family to generate queries from
    # Options: 'android_world', 'android', 'information_retrieval', 'miniwob', 'miniwob_subset'
    FAMILY = 'android_world'

    # Number of parameter variations per task template
    # E.g., 5 means each task template will generate 5 different queries with different params
    N_VARIATIONS = 1

    # Random seed for reproducibility
    SEED = 42

    # Output file path
    OUTPUT_FILE = 'queries_dataset.json'

    # Specific tasks to generate (None = all tasks)
    # Example: ['ContactsAddContact', 'SystemWifiTurnOn']
    SPECIFIC_TASKS = None

    # Number of sample queries to print at the end
    N_SAMPLES = 5

    # Set to True to just list all available task templates and exit
    LIST_TASKS_ONLY = False

    # ========================================================================
    # END CONFIGURATION
    # ========================================================================

    # List tasks and exit if requested
    if LIST_TASKS_ONLY:
        list_all_task_templates(FAMILY)
        return

    # Generate queries
    queries_dataset = generate_all_queries(
        family=FAMILY,
        n_variations=N_VARIATIONS,
        seed=SEED,
        output_file=OUTPUT_FILE,
        specific_tasks=SPECIFIC_TASKS,
    )

    # Print sample queries
    if queries_dataset:
        print_sample_queries(queries_dataset, n=N_SAMPLES)


if __name__ == '__main__':
    main()
