
import re
import json
from collections import Counter


# This pattern extracts important information from an Apache log line
APACHE_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\d+|-)'
)


# Convert one Apache log line into a dictionary
def parse_apache_line(line: str) -> dict | None:

    match = APACHE_PATTERN.match(line)

    # Return None if the line does not match Apache format
    if not match:
        return None

    data = match.groupdict()

    # Convert numeric fields into integers
    data["status"] = int(data["status"])
    data["size"] = int(data["size"]) if data["size"] != "-" else 0

    return data


# Analyze the complete Apache log file
def analyze_logs(file_path: str) -> dict:

    records = []
    invalid_count = 0

    # Read the file one line at a time
    with open(file_path, "r", encoding="utf-8") as file:

        for line in file:

            record = parse_apache_line(line.strip())

            # Count lines that could not be parsed
            if record is None:
                invalid_count += 1
                continue

            records.append(record)

    # Count HTTP response codes
    status_counts = Counter(
        record["status"] for record in records
    )

    # Count requests that resulted in server errors
    server_errors = [
        record for record in records
        if 500 <= record["status"] < 600
    ]

    # Count requests that resulted in client errors
    client_errors = [
        record for record in records
        if 400 <= record["status"] < 500
    ]

    # Prepare the final analysis summary
    summary = {
        "total_lines": len(records) + invalid_count,
        "parsed_lines": len(records),
        "invalid_lines": invalid_count,
        "status_counts": dict(status_counts),
        "server_error_count": len(server_errors),
        "client_error_count": len(client_errors),
        "server_errors": server_errors,
        "client_errors": client_errors
    }

    return summary


# Run the analyzer on our Apache log file
if __name__ == "__main__":

    summary = analyze_logs("data/apache_access.log")

    # Display the analysis results
    print(json.dumps(summary, indent=4))

    # Save the analysis results as a JSON file
    with open("data/apache_summary.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\nAnalysis saved to data/apache_summary.json")
