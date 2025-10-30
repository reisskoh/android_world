"""
Script to download and analyze datasets from Hugging Face.

This script helps you quickly download any dataset from Hugging Face Hub
and perform basic analysis on it.
"""

import json
import os
from datasets import load_dataset
import pandas as pd


def download_and_analyze_dataset(
    dataset_name,
    output_dir='hf_datasets',
    subset=None,
    split='train',
    save_sample=True,
    sample_size=10,
    save_format='json',  # 'json', 'csv', or 'parquet'
):
    """
    Download and analyze a Hugging Face dataset.

    Args:
        dataset_name: Name of the dataset on Hugging Face (e.g., 'squad', 'glue')
        output_dir: Directory to save downloaded data
        subset: Dataset subset/config name (e.g., 'sst2' for GLUE)
        split: Which split to download ('train', 'test', 'validation', 'all')
        save_sample: Whether to save a sample of the data
        sample_size: Number of examples to save in sample
        save_format: Format to save the sample ('json', 'csv', 'parquet')
    """
    print("="*80)
    print(f"DOWNLOADING DATASET FROM HUGGING FACE")
    print("="*80)
    print(f"Dataset: {dataset_name}")
    if subset:
        print(f"Subset: {subset}")
    print(f"Split: {split}")
    print("="*80)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Download dataset
    print(f"\nDownloading dataset...")
    try:
        if split == 'all':
            dataset = load_dataset(dataset_name, subset)
        else:
            dataset = load_dataset(dataset_name, subset, split=split)
        print(f"✅ Successfully downloaded dataset!")
    except Exception as e:
        print(f"❌ Failed to download dataset: {e}")
        return None

    # Analyze dataset
    print(f"\n{'='*80}")
    print("DATASET ANALYSIS")
    print("="*80)

    if split == 'all':
        # Multiple splits
        print(f"\nAvailable splits: {list(dataset.keys())}")
        for split_name, split_data in dataset.items():
            print(f"\n{split_name.upper()} Split:")
            print(f"  Number of examples: {len(split_data)}")
            if len(split_data) > 0:
                print(f"  Features: {split_data.features}")
                print(f"  Column names: {split_data.column_names}")

        # Use first split for sample
        first_split = list(dataset.keys())[0]
        data_to_analyze = dataset[first_split]
        print(f"\nUsing '{first_split}' split for sample and further analysis")
    else:
        # Single split
        print(f"\nNumber of examples: {len(dataset)}")
        print(f"Features: {dataset.features}")
        print(f"Column names: {dataset.column_names}")
        data_to_analyze = dataset

    # Show sample examples
    if len(data_to_analyze) > 0:
        print(f"\n{'='*80}")
        print(f"SAMPLE EXAMPLES (first 3)")
        print("="*80)

        for i in range(min(3, len(data_to_analyze))):
            print(f"\nExample {i+1}:")
            example = data_to_analyze[i]
            for key, value in example.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 200:
                    value_display = value[:200] + "..."
                else:
                    value_display = value
                print(f"  {key}: {value_display}")

    # Save sample to file
    if save_sample and len(data_to_analyze) > 0:
        print(f"\n{'='*80}")
        print(f"SAVING SAMPLE DATA")
        print("="*80)

        # Get sample
        num_samples = min(sample_size, len(data_to_analyze))
        sample_data = data_to_analyze.select(range(num_samples))

        # Determine filename
        dataset_clean_name = dataset_name.replace('/', '_')
        if subset:
            subset_clean = subset.replace('/', '_')
            filename_base = f"{dataset_clean_name}_{subset_clean}_sample"
        else:
            filename_base = f"{dataset_clean_name}_sample"

        # Save in requested format
        if save_format == 'json':
            output_file = os.path.join(output_dir, f"{filename_base}.json")
            sample_data.to_json(output_file, indent=2)
        elif save_format == 'csv':
            output_file = os.path.join(output_dir, f"{filename_base}.csv")
            sample_data.to_csv(output_file, index=False)
        elif save_format == 'parquet':
            output_file = os.path.join(output_dir, f"{filename_base}.parquet")
            sample_data.to_parquet(output_file)

        print(f"✅ Saved {num_samples} examples to: {output_file}")

        # Also save statistics
        stats_file = os.path.join(output_dir, f"{filename_base}_stats.txt")
        with open(stats_file, 'w') as f:
            f.write(f"Dataset: {dataset_name}\n")
            if subset:
                f.write(f"Subset: {subset}\n")
            f.write(f"Split: {split}\n")
            f.write(f"Total examples: {len(data_to_analyze)}\n")
            f.write(f"Sample size: {num_samples}\n")
            f.write(f"\nFeatures:\n")
            for feature_name, feature_type in data_to_analyze.features.items():
                f.write(f"  - {feature_name}: {feature_type}\n")
            f.write(f"\nColumn names: {data_to_analyze.column_names}\n")

        print(f"✅ Saved statistics to: {stats_file}")

    # Return dataset for further use
    return dataset if split == 'all' else data_to_analyze


def analyze_specific_columns(dataset, columns_to_analyze):
    """
    Perform detailed analysis on specific columns.

    Args:
        dataset: HuggingFace dataset
        columns_to_analyze: List of column names to analyze
    """
    print(f"\n{'='*80}")
    print("DETAILED COLUMN ANALYSIS")
    print("="*80)

    for col in columns_to_analyze:
        if col not in dataset.column_names:
            print(f"\n⚠️  Column '{col}' not found in dataset")
            continue

        print(f"\nColumn: {col}")
        print("-" * 40)

        # Get column data
        col_data = dataset[col]

        # Basic stats
        print(f"Total values: {len(col_data)}")

        # Type-specific analysis
        if len(col_data) > 0:
            first_val = col_data[0]

            if isinstance(first_val, str):
                # String analysis
                lengths = [len(s) for s in col_data if s]
                print(f"String length - Min: {min(lengths)}, Max: {max(lengths)}, Avg: {sum(lengths)/len(lengths):.1f}")

                # Show unique values if not too many
                unique_vals = set(col_data)
                if len(unique_vals) <= 20:
                    print(f"Unique values ({len(unique_vals)}): {sorted(unique_vals)}")
                else:
                    print(f"Number of unique values: {len(unique_vals)}")

            elif isinstance(first_val, (int, float)):
                # Numeric analysis
                print(f"Min: {min(col_data)}, Max: {max(col_data)}, Avg: {sum(col_data)/len(col_data):.2f}")

            elif isinstance(first_val, list):
                # List analysis
                lengths = [len(lst) for lst in col_data]
                print(f"List length - Min: {min(lengths)}, Max: {max(lengths)}, Avg: {sum(lengths)/len(lengths):.1f}")


def main():
    # ========================================================================
    # CONFIGURE THESE PARAMETERS
    # ========================================================================

    # Hugging Face dataset name
    # Examples: 'squad', 'glue', 'imdb', 'cnn_dailymail', 'wikitext'
    # For datasets with owner: 'username/dataset_name'
    DATASET_NAME = 'smolagents/android-control'

    # Subset/config name (None if no subset)
    # Example: For GLUE, you might use 'sst2', 'mnli', etc.
    SUBSET = None

    # Which split to download
    # Options: 'train', 'test', 'validation', 'all'
    SPLIT = 'train'  # Download only train split

    # Directory to save downloaded data
    OUTPUT_DIR = 'hf_datasets'

    # Whether to save a sample of the data
    SAVE_SAMPLE = True

    # Number of examples to save in sample
    SAMPLE_SIZE = 10  # Start with small sample to see structure

    # Format to save sample
    # Options: 'json', 'csv', 'parquet'
    SAVE_FORMAT = 'json'

    # Specific columns to analyze in detail (None = skip detailed analysis)
    # Example: ['question', 'context', 'answers'] for SQuAD
    # Will be set after seeing what columns exist
    COLUMNS_TO_ANALYZE = None

    # ========================================================================
    # END CONFIGURATION
    # ========================================================================

    # Download and analyze
    dataset = download_and_analyze_dataset(
        dataset_name=DATASET_NAME,
        output_dir=OUTPUT_DIR,
        subset=SUBSET,
        split=SPLIT,
        save_sample=SAVE_SAMPLE,
        sample_size=SAMPLE_SIZE,
        save_format=SAVE_FORMAT,
    )

    # Detailed column analysis if requested
    if dataset and COLUMNS_TO_ANALYZE:
        analyze_specific_columns(dataset, COLUMNS_TO_ANALYZE)

    print(f"\n{'='*80}")
    print("DONE!")
    print("="*80)


if __name__ == '__main__':
    main()
