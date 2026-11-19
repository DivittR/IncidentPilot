
import json
import re


# These are the error levels our system will recognize
VALID_LEVELS = {
    "DEBUG", "INFO", "WARNING", "WARN",
    "ERROR", "CRITICAL", "FATAL"
}


# Convert different names of log levels into standard names
def normalize_level(level):
    level = str(level).upper()

    if level == "WARN":
        return "WARNING"

    if level == "FATAL":
        return "CRITICAL"

    return level


# Convert different log formats into one common dictionary
def normalize_record(timestamp, level, service, message, log_format, raw):

    # Make sure the log level is in a standard format
    level = normalize_level(level)

    # Replace missing service names with unknown
    service = str(service).strip() if service else "unknown"

    # Create one common structure for every log
    return {
        "timestamp": str(timestamp).strip(),
        "level": level,
        "service": service,
        "message": str(message).strip(),
        "format": log_format,
        "raw": raw
    }


# Try to read a log line as JSON
def parse_json_log(line):

    try:
        data = json.loads(line)

        # Find timestamp, level, service and message
        timestamp = (
            data.get("timestamp")
            or data.get("@timestamp")
            or data.get("time")
            or data.get("datetime")
        )

        level = (
            data.get("level")
            or data.get("severity")
            or data.get("log_level")
        )

        service = (
            data.get("service")
            or data.get("service_name")
            or data.get("application")
        )

        message = (
            data.get("message")
            or data.get("msg")
            or data.get("event")
        )

        # Check whether the important information exists
        if not timestamp or not level or not message:
            return None

        # Reject levels that our system does not recognize
        if str(level).upper() not in VALID_LEVELS:
            return None

        return normalize_record(
            timestamp, level, service, message, "json", line
        )

    except (json.JSONDecodeError, AttributeError, TypeError):
        return None


# Try to read a normal text log using known patterns
def parse_text_log(line):

    # Pattern 1: 2026-11-18 10:00:05 ERROR checkout Payment timeout
    standard_pattern = (
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]"
        r"\d{2}:\d{2}:\d{2}(?:\.\d+)?"
        r"(?:Z|[+-]\d{2}:\d{2})?)\s+"
        r"(?P<level>[A-Za-z]+)\s+"
        r"(?P<service>[\w.-]+)\s+"
        r"(?P<message>.+)$"
    )

    # Pattern 2: [2026-11-18 10:00:05] ERROR: Payment timeout
    bracket_pattern = (
        r"^\[(?P<timestamp>[^\]]+)\]\s*"
        r"(?P<level>[A-Za-z]+):\s*"
        r"(?P<message>.+)$"
    )

    # Pattern 3: 2026-11-18 10:00:05 ERROR [checkout] Payment timeout
    service_pattern = (
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]"
        r"\d{2}:\d{2}:\d{2})\s+"
        r"(?P<level>[A-Za-z]+)\s+"
        r"\[(?P<service>[^\]]+)\]\s+"
        r"(?P<message>.+)$"
    )

    # Try each known text format until one matches
    patterns = [
        (service_pattern, "bracketed_service"),
        (standard_pattern, "standard"),
        (bracket_pattern, "bracketed")
    ]

    for pattern, log_format in patterns:

        match = re.match(pattern, line)

        if match:

            # Extract all matching fields
            data = match.groupdict()

            # Check whether the log level is recognized
            if data["level"].upper() not in VALID_LEVELS:
                return None

            return normalize_record(
                data["timestamp"],
                data["level"],
                data.get("service"),
                data["message"],
                log_format,
                line
            )

    # Return None if none of our patterns match
    return None


# Decide which parser should handle the incoming log line
def parse_log_line(line):

    # Remove unnecessary spaces and newline characters
    line = line.strip()

    # Ignore completely empty lines
    if not line:
        return None

    # JSON logs usually begin with an opening brace
    if line.startswith("{"):
        return parse_json_log(line)

    # Otherwise, try the known text formats
    return parse_text_log(line)


# Store successfully parsed logs and invalid lines
all_logs = []
invalid_logs = []

# Open the log file and process each line separately
with open("data/sample.log", "r", encoding="utf-8") as file:

    for line in file:

        # Convert the current line into a common structure
        record = parse_log_line(line)

        # Save lines that our parser cannot understand
        if record is None:
            if line.strip():
                invalid_logs.append(line.strip())
            continue

        # Store every successfully parsed record
        all_logs.append(record)


# Collect all records that contain errors
error_logs = [
    log for log in all_logs
    if log["level"] in {"ERROR", "CRITICAL"}
]


# Display all successfully parsed logs
print("\n========== ALL PARSED LOGS ==========")

for log in all_logs:
    print(log)


# Display only error records
print("\n========== ERROR LOGS ==========")

for log in error_logs:
    print(log)


# Display a summary of the processing
print("\n========== SUMMARY ==========")
print("Total parsed logs:", len(all_logs))
print("Total error logs:", len(error_logs))
print("Total invalid logs:", len(invalid_logs))


# Display lines that could not be understood
print("\n========== INVALID LOGS ==========")

for log in invalid_logs:
    print(log)
