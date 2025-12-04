from django import template
import subprocess
import os
from datetime import datetime

register = template.Library()


@register.filter
def get_range(value):
    """Returns a range from 1 to value (inclusive) for pagination."""
    try:
        value = int(value)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return []


@register.filter
def split(value, delimiter=","):
    """
    Split a string into a list using the given delimiter
    Usage (in template):
    {% for item in "a,b,c"|split:"," %}
        {{ item }}
    {% endfor %}
    """
    return value.split(delimiter)


@register.simple_tag
def get_git_commit_info():
    """
    Get the latest git commit date and hash
    Returns a dict with 'date' and 'hash' keys
    """
    try:
        # Get the latest commit date with time and timezone
        base_path = os.path.dirname(os.path.dirname(__file__))
        date_format = "--date=format:%B %d, %Y at %H:%M:%S %Z"
        date_result = subprocess.run(
            ["git", "log", "-1", "--format=%cd", date_format],
            capture_output=True,
            text=True,
            cwd=base_path,
        )

        # Get the latest commit hash (short version)
        hash_result = subprocess.run(
            ["git", "log", "-1", "--format=%h"],
            capture_output=True,
            text=True,
            cwd=base_path,
        )

        if date_result.returncode == 0 and hash_result.returncode == 0:
            return {
                "date": date_result.stdout.strip(),
                "hash": hash_result.stdout.strip(),
            }
    except Exception:
        pass

    # Fallback to current date if git command fails
    fallback_date = datetime.now().strftime("%B %d, %Y at %H:%M:%S %Z")
    return {"date": fallback_date, "hash": "unknown"}
