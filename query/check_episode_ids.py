"""
Quick script to check what episode IDs are available in the dataset.
"""

from datasets import load_dataset

def check_episode_ids():
    """Check the range and distribution of episode IDs in the dataset."""

    print("Loading dataset...")
    dataset = load_dataset('smolagents/android-control', split='train')
    print(f"Total episodes: {len(dataset)}")

    # Collect all episode IDs
    episode_ids = []
    for episode in dataset:
        episode_id = episode.get('episode_id')
        episode_ids.append(episode_id)

    # Analyze episode IDs
    print(f"\nEpisode ID Statistics:")
    print(f"  Min ID: {min(episode_ids)}")
    print(f"  Max ID: {max(episode_ids)}")
    print(f"  Unique IDs: {len(set(episode_ids))}")

    # Check if sequential
    sorted_ids = sorted(set(episode_ids))
    is_sequential = all(sorted_ids[i] == sorted_ids[i-1] + 1 for i in range(1, len(sorted_ids)))
    print(f"  Sequential: {is_sequential}")

    # Show first 20 episode IDs
    print(f"\nFirst 20 episode IDs:")
    print(sorted_ids[:20])

    # Show last 20 episode IDs
    print(f"\nLast 20 episode IDs:")
    print(sorted_ids[-20:])

    # Check for duplicates
    from collections import Counter
    id_counts = Counter(episode_ids)
    duplicates = [(id, count) for id, count in id_counts.items() if count > 1]
    if duplicates:
        print(f"\nDuplicate episode IDs found:")
        for id, count in duplicates[:10]:
            print(f"  ID {id}: {count} occurrences")
    else:
        print(f"\nNo duplicate episode IDs found")

if __name__ == '__main__':
    check_episode_ids()
