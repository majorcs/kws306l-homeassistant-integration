# Contributing

## Workflow

`main` is a protected branch. All changes, including release version bumps,
land through a pull request — direct pushes to `main` are rejected, even for
repository admins.

1. Create a branch off `main`.
2. Make your changes and add/update tests as needed.
3. Run the test suite locally: `pip install -r requirements_test.txt && pytest -q`
   (a coverage gate of 90% is enforced via `pyproject.toml`).
4. Open a pull request. No reviewer approval is required, but the PR cannot
   be merged until all required checks pass:
   - `pytest` (`.github/workflows/tests.yml`)
   - `hassfest` (`.github/workflows/hassfest.yml`)
   - `validate-hacs` (`.github/workflows/validate.yml`)
5. Merge once checks are green.

## Cutting a release

1. On the PR (or a follow-up PR), bump `"version"` in
   `custom_components/kws306l/manifest.json` and `VERSION` in
   `custom_components/kws306l/const.py` to the same `YYYY.MM.DD.SEQ` value,
   and commit it as `Release YYYY.MM.DD.SEQ`.
2. Merge the PR into `main`.
3. Tag the resulting commit on `main` with the version and push the tag:
   `git tag YYYY.MM.DD.SEQ <commit> && git push origin YYYY.MM.DD.SEQ`.
   Tag pushes aren't branch pushes, so they aren't blocked by branch
   protection.
4. Pushing the tag triggers `.github/workflows/release.yml`, which validates
   the tag format and publishes the GitHub release automatically.

## Notes

- `validate.yml` also runs on a daily schedule. GitHub auto-disables
  scheduled workflows after roughly 60 days without any push to the repo —
  if `validate-hacs` stops showing up on a PR, check
  `gh workflow list --all` for a `disabled_inactivity` state before assuming
  something else broke.
- `docs/*.md` (except `docs/REGISTER_MODEL.md`, which predates the ignore
  rule and is already public) are local-only working notes excluded via
  `.gitignore` — they aren't meant to be committed.
