# Data Safety Rules

1. **Do NOT commit secrets**: API keys, passwords, tokens must go in `.env`, never in code or config.yaml.
2. **Gitignore first**: Before creating any file that may contain sensitive data, ensure it's in `.gitignore`.
3. **SQLite safety**: Use parameterized queries for all SQL. No string formatting of `WHERE` clauses.
4. **No production data in dev**: Use synthetic/sample data for development and testing.
5. **File paths**: Use `os.path.join` or `pathlib.Path` to build paths, never string concatenation.
6. **Clean up temp files**: Temporary artifacts should be gitignored or explicitly deleted after use.
7. **Term_mapping**: The `term_mapping` table stores original/chinese term pairs. Chinese terms are display-only data, not executable code.