import os
import json
import sys


def clear_metrics_file(filename="data/outputs/realtime_metrics.json"):
    """Clear the metrics file by replacing it with an empty array."""
    try:
        with open(filename, 'w') as f:
            json.dump([], f)
        print(f"Successfully cleared metrics file: {filename}")
        return True
    except Exception as e:
        print(f"Error clearing metrics file: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "data/outputs/realtime_metrics.json"

    clear_metrics_file(filename)
