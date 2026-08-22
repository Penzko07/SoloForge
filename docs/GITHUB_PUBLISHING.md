# GitHub Publishing

Normal Git is the preferred workflow:

```bash
git push origin main
```

If local HTTPS credentials are missing, SoloForge includes a GitHub API publish helper.

## Token Setup

Create a fine-grained GitHub token with repository contents write access, then export it only for the current shell:

```bash
export SOLOFORGE_GITHUB_TOKEN="github_pat_..."
```

Do not commit tokens to the repository.

## Publish Committed HEAD

Commit locally first:

```bash
git status --short
git add .
git commit -m "Your commit message"
```

Publish the committed `HEAD`:

```bash
python3 tools/publish_to_github.py --repo Penzko07/SoloForge --branch main
```

Dry run:

```bash
python3 tools/publish_to_github.py --repo Penzko07/SoloForge --branch main --dry-run
```

The helper mirrors the committed local tree through GitHub's Git API and fast-forwards the branch. It does not store the token.
