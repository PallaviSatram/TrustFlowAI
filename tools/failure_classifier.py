import re

FAILURE_PATTERNS = {
    "Dependency": [
        r"ModuleNotFoundError",
        r"No module named",
        r"ImportError",
        r"Could not find a version that satisfies",
        r"No matching distribution found",
        r"Dependency resolution failed",
    ],
    "Test Failure": [
        r"AssertionError",
        r"FAILED\s+.*::",
        r"pytest.*failed",
        r"Tests? failed",
        r"Test failure",
    ],
    "Code / Syntax": [
        r"SyntaxError",
        r"IndentationError",
        r"NameError",
        r"UnboundLocalError",
    ],
    "Permission": [
        r"Permission denied",
        r"PermissionError",
        r"Access is denied",
        r"Operation not permitted",
    ],
    "Infrastructure / Network": [
        r"Connection timed out",
        r"Connection refused",
        r"Temporary failure in name resolution",
        r"Network is unreachable",
        r"Service unavailable",
    ],
    "Configuration": [
        r"Invalid configuration",
        r"Configuration error",
        r"Missing required environment variable",
        r"Required environment variable.*not set",
    ],
}

def classify_failure(context):
  """Identify the earliest detected failure category and other indicators."""
  if not context or not isinstance(context, str):
    return {
      "earliest_detected_category": "Unknown",
      "matched_indicators": [],
      "secondary_categories": [],
    }
    
  matches = []
  
  for category, patterns in FAILURE_PATTERNS.items():
    for pattern in patterns:
      for match in re.finditer(pattern, context, re.IGNORECASE):
        matches.append({
          "position" : match.start(),
          # Returns the starting character index of the matched text in context.
          "category" : category,
          "indicator" : match.group(),
          # Returns the exact text that matched the regular expression.
        })
        
  if not matches:  
    return {
      "earliest_detected_category" : "Unknown",
      "matched_indicators" : [],
      "secondary_categories": [],
    }
  
  # sort indicators by their position in the log
  matches.sort(key=lambda item: item["position"])
  
  earliest_category = matches[0]["category"]
  
  secondary_categories = list(dict.fromkeys(
    item["category"]
    for item in matches
    if item["category"] != earliest_category
  ))
  
  return {
    "earliest_detected_category": earliest_category,
    "matched_indicators": [
      item["indicator"] for item in matches
    ],
    "secondary_categories": secondary_categories
  }