# Automatic upstream synchronization and releases

This fork synchronizes [drakolordx7/pokopia-recomp](https://github.com/drakolordx7/pokopia-recomp), branch `main`.

The workflow lives in [`.github/workflows/upstream-sync-release.yml`](../.github/workflows/upstream-sync-release.yml).

## Behavior

- Checks the upstream every **30 minutes** (GitHub schedules are best effort). It also supports manual dispatch.
- Fetches upstream `main` and merges new commits into this fork's `main` branch. It never force-pushes or silently discards this fork's workflows/documentation.
- Publishes a **source-only prerelease** tagged `sync-<first 12 characters of upstream commit SHA>`, once per upstream revision.
- Mirrors the most recent **stable official upstream GitHub Release** when it has not been mirrored already. The original upstream Windows ZIP is downloaded unchanged; this fork also publishes SHA-256 hashes. Additional platforms are mirrored only if the upstream actually provides them.
- Uses release tags to avoid duplicate publication on subsequent scheduled runs.

## Important distinction: source changes versus installable builds

The upstream Windows build includes a launcher/toolchain that compiles the game from the player's **own** extracted Pokopia game files on the player's computer. The full build is not suitable for a public GitHub-hosted CI run without those personal game files. Consequently:

- `sync-*` = a GitHub source archive, **not** a runnable Windows installer.
- `v*` release mirrors = installable binaries originally compiled **by upstream**, not rebuilt or validated by this fork.
- The automation never distributes Nintendo game data, extracted code or console keys.
- Do not upload local game dumps, keys, generated artifacts or personal files to this repository or GitHub Actions.

At configuration time, upstream's latest stable installer was `v0.1.1`, `PokopiaRecomp-0.1.1-win64.zip`. There was no official Linux release.

## Monitoring and recovery

- [Actions runs](../../actions/workflows/upstream-sync-release.yml)
- [Published releases](../../releases)
- Workflow needs GitHub Actions enabled and the built-in `GITHUB_TOKEN` authorized for repository contents write (provided by `permissions: contents: write`).
- Merge conflicts fail safely. Resolve them manually without resetting local changes and rerun.
- GitHub schedules can run late or be skipped at times. Use **Run workflow** for a manual retry.
