---
name: skill-content-validator
description: Use when validating SKILL.md content in the submission pipeline
---

# Skill Content Validator

## Gate 1 Rules

- Required frontmatter: name, description
- At least 3 trigger phrases
- short_desc <= 80 characters
- Unique slug (no existing skill with same slug)
- Content hash for duplicate detection

## Frontmatter Parsing

```python
import yaml
parts = content.split("---", 2)
frontmatter = yaml.safe_load(parts[1])
body = parts[2]
```

## Content Hash

```python
import hashlib
content_hash = hashlib.sha256(content.encode()).hexdigest()
```

## References

- Submission service: `apps/api/skillhub/services/submission.py`
- Submission model: `libs/db/skillhub_db/models/submission.py`
