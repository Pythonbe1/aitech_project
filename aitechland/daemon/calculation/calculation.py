from collections import defaultdict
from typing import Dict, List


class Calculation:
    @staticmethod
    def count_classes(class_names: Dict[int, str], class_indices: List[int]) -> Dict[str, int]:
        """
        Count the occurrences of each class in the given list of class indices.

        Args:
            class_names (Dict[int, str]): Mapping of class indices to class names.
            class_indices (List[int]): List of class indices to count.

        Returns:
            Dict[str, int]: Dictionary with class names as keys and counts as values.
        """
        class_counts = defaultdict(int)
        for class_index in class_indices:
            class_name = class_names.get(class_index)
            if class_name is not None:
                class_counts[class_name] += 1
        return class_counts
