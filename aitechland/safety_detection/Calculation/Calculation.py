from collections import defaultdict


class Calculation:
    @staticmethod
    def count_classes(class_names, class_indices):
        class_counts = defaultdict(int)
        for class_index in class_indices:
            class_name = class_names.get(class_index)
            if class_name is not None:
                class_counts[class_name] += 1
        return class_counts