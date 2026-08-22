# Importers

SoloForge importers collect metadata from public sources and turn it into registry records.

The first importer target is GitHub repository metadata. It stores source information and counts candidate Cheat Engine table paths, but it does not download or redistribute trainer logic.

```bash
python3 tools/import_github_metadata.py owner/repo
```

Run validation after importing:

```bash
python3 tools/validate_registry.py
```
