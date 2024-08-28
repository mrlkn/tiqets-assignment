import csv
from typing import Any, Dict, List


class CSVHandler:
    @staticmethod
    def read(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)

    @staticmethod
    def write(file_path: str, data: List[Dict[str, Any]]) -> None:
        if not data:
            raise ValueError("No data to write")

        fieldnames = data[0].keys()
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
