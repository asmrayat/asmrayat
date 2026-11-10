# Setup

These files go in your profile repo, `asmrayat/asmrayat`. Replace the old
`README.md` with the one here.

1. Copy everything into the repo (keep the `.github` folder) and push to the default branch.
2. On GitHub open **Actions > Refresh README cards > Run workflow**.
   It fetches your data, draws `cards/*.svg`, rewrites `README.md` and commits.
   After that it runs every morning and whenever you change `config.json` or the scripts.
3. If the commit step is refused, set **Settings > Actions > General >
   Workflow permissions** to "Read and write".

## Changing things

- `config.json`: name, tagline, monogram letters, the three tiles and the featured repos.
  A tile `value` is one of `public_repos`, `followers`, `total_contributions`,
  `current_streak`, `active_days`, or a plain number.
- `scripts/render_cards.py`: colours are at the top, each card has its own function.
- Private contributions are only counted if you add a personal access token
  (scope `read:user`) as a repo secret named `PROFILE_TOKEN`.

## Running it locally

```bash
GH_TOKEN=your_token python scripts/fetch_data.py
python scripts/render_cards.py             # animated cards
STATIC=1 python scripts/render_cards.py    # final frame, for screenshots
python scripts/render_cards.py --sample    # made-up numbers, for design work only
```

`README.md` is generated, so edit the script or the config instead of the file.
