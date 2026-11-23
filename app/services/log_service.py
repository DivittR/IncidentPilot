# Count the number of lines in uploaded log content
def count_log_lines(content: str) -> int:
    return len(content.splitlines())