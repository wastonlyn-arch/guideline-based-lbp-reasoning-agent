# Coding Style Rules

## Docstrings

Use **Google-style** docstrings for all public classes and functions.

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """Short description of the function.
    
    Longer description if needed, explaining behavior.
    
    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 0.
    
    Returns:
        Description of the return value.
    
    Raises:
        ValueError: If param1 is empty.
    """
```

## Type annotations

- All function parameters and return values must have type annotations.
- Use `Optional[X]` instead of `X | None` for Python <3.10 compatibility if needed.
- For complex types, use `from typing import List, Dict, Optional, Union, Any, Tuple`.

## Import order

Group and separate by blank lines in this order:
1. Standard library (`os`, `sys`, `pathlib`, `json`, `logging`, `re`, etc.)
2. Third-party (`numpy`, `openai`, `sqlite3`, `yaml`, `pydantic`, etc.)
3. Local application (`from src.xxx import ...`)

Within each group, sort alphabetically.

## Line length

Maximum **100 characters** per line.

## Naming conventions

| Type | Convention | Example |
|------|-----------|---------|
| Class | PascalCase | `DatabaseClient`, `KnowledgeGraphQuery` |
| Function | snake_case | `extract_entities()`, `build_path_query()` |
| Variable | snake_case | `patient_id`, `extracted_terms` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_EMBED_MODEL` |
| Private method/var | _prefix snake_case | `_validate_input()`, `_cache` |

## Prohibited patterns

- ❌ `from module import *`
- ❌ Bare `except:` without specifying exception type
- ❌ Mutable default arguments (`def f(x=[])`)
- ❌ `print()` in production code (use `logging`)
- ❌ Global variables for configuration (use Config dataclass)
- ❌ Circular imports (enforced by module dependency rules)