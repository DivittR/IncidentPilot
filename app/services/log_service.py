
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4


# Incident configuration
INCIDENT_WINDOW_MINUTES = 5
MIN_OCCURRENCES = 3


def parse_application_log(line, line_id):
    # JSON format
    try:
        data = json.loads(line)

        timestamp = data.get("timestamp") or data.get("@timestamp")
        severity = data.get("level") or data.get("severity")
        service = data.get("service") or data.get("service_name")
        message = data.get("message") or data.get("msg")

        if timestamp and severity and message:
            datetime.fromisoformat(timestamp)

            return {
                "line_id": line_id,
                "timestamp": timestamp,
                "severity": severity.upper(),
                "service": service,
                "message": message
            }

    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    # Plain-text format with optional service brackets
    match = re.match(
        r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
        r"\*{0,2}(INFO|WARNING|ERROR|CRITICAL)\*{0,2} "
        r"(?:\[([^\]]+)\]|(\S+)) (.+)$",
        line
    )

    if match:
        timestamp, severity, service1, service2, message = match.groups()

        return {
            "line_id": line_id,
            "timestamp": datetime.strptime(
                timestamp, "%Y-%m-%d %H:%M:%S"
            ).isoformat(),
            "severity": severity.upper(),
            "service": service1 or service2,
            "message": message
        }

    # Bracketed timestamp without a service
    match = re.match(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] "
        r"(INFO|WARNING|ERROR|CRITICAL): (.+)$",
        line
    )

    if match:
        timestamp, severity, message = match.groups()

        return {
            "line_id": line_id,
            "timestamp": datetime.strptime(
                timestamp, "%Y-%m-%d %H:%M:%S"
            ).isoformat(),
            "severity": severity.upper(),
            "service": None,
            "message": message
        }

    return None


def parse_apache_log(line, line_id):
    pattern = (
        r'^(\S+) \S+ \S+ '
        r'\[([^\]]+)\] '
        r'"(\S+) (\S+) [^"]+" '
        r'(\d{3}) (\d+)'
    )

    match = re.match(pattern, line)

    if not match:
        return None

    ip, timestamp, method, endpoint, status, size = match.groups()

    try:
        parsed_time = datetime.strptime(
            timestamp, "%d/%b/%Y:%H:%M:%S %z"
        ).isoformat()
    except ValueError:
        return None

    status = int(status)

    if status >= 500:
        severity = "ERROR"
    elif status >= 400:
        severity = "WARNING"
    else:
        severity = "INFO"

    return {
        "line_id": line_id,
        "timestamp": parsed_time,
        "severity": severity,
        "service": "web",
        "message": f"{method} {endpoint} returned {status}",
        "client_ip": ip,
        "status_code": status,
        "response_size": int(size)
    }


def parse_log_content(content, log_type="application"):
    parsed_records = []
    invalid_lines = []

    lines = content.splitlines()

    for line_id, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        if log_type == "apache":
            record = parse_apache_log(line, line_id)
        else:
            record = parse_application_log(line, line_id)

        if record:
            parsed_records.append(record)
        else:
            invalid_lines.append({
                "line_id": line_id,
                "content": line
            })

    return {
        "parsed_records": parsed_records,
        "invalid_lines": invalid_lines,
        "total_lines": len(lines)
    }


def normalize_message(message: str) -> str:
    return " ".join(message.lower().split())


def group_similar_errors(records):
    groups = {}

    # Sort errors chronologically before grouping
    error_records = [
        record for record in records
        if record["severity"] in ["ERROR", "CRITICAL"]
    ]

    error_records.sort(
        key=lambda record: datetime.fromisoformat(record["timestamp"])
    )

    for record in error_records:
        key = (
            record["service"],
            record["severity"],
            normalize_message(record["message"])
        )

        timestamp = datetime.fromisoformat(record["timestamp"])

        # Normalize timestamps for consistent comparisons
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        if key not in groups:
            groups[key] = []

        matching_group = None

        for group in groups[key]:
            difference = (
                timestamp - group["start_time"]
            ).total_seconds() / 60

            if 0 <= difference <= INCIDENT_WINDOW_MINUTES:
                matching_group = group
                break

        if matching_group is None:
            groups[key].append({
                "service": record["service"],
                "severity": record["severity"],
                "message": normalize_message(record["message"]),
                "start_time": timestamp,
                "end_time": timestamp,
                "occurrence_count": 1,
                "line_ids": [record["line_id"]]
            })
        else:
            matching_group["end_time"] = timestamp
            matching_group["occurrence_count"] += 1
            matching_group["line_ids"].append(record["line_id"])

    incidents = []

    for group_list in groups.values():
        for group in group_list:
            if group["occurrence_count"] >= MIN_OCCURRENCES:
                group["incident_id"] = (
                    f"INC-{uuid4().hex[:8].upper()}"
                )

                group["error_group"] = (
                    f'{group["service"]}:'
                    f'{group["severity"]}:'
                    f'{group["message"]}'
                )

                group["start_time"] = group["start_time"].isoformat()
                group["end_time"] = group["end_time"].isoformat()

                incidents.append(group)

    return incidents


def count_log_lines(content: str) -> int:
    return len(content.splitlines())
