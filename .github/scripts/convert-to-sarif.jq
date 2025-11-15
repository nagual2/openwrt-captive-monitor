[.[] | select(.level == "error" or .level == "warning")] as $issues |
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": {
      "driver": {
        "name": "ShellCheck",
        "informationUri": "https://www.shellcheck.net/",
        "version": "0.9.0",
        "rules": []
      }
    },
    "results": ($issues | map({
      "ruleId": ("SC" + (.code | tostring)),
      "level": (if .level == "error" then "error" else "warning" end),
      "message": {
        "text": .message
      },
      "locations": [{
        "physicalLocation": {
          "artifactLocation": {
            "uri": .file
          },
          "region": {
            "startLine": .line,
            "startColumn": .column
          }
        }
      }]
    }))
  }]
}
