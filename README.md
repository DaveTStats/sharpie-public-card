# Sharpie Public Card

Public Streamlit app for sharing Sharpie's MLB 1+ hit card.

Entrypoint:

```text
sharpie_public_app.py
```

For Streamlit Community Cloud, use a public repo that includes:

```text
sharpie_public_app.py
requirements.txt
data/processed/sharpie_picks.csv
data/processed/sharpie_writeups.csv
data/processed/sharpie_results_public.csv
data/processed/sharpie_player_lookup_public.csv
```

If copying from the main MLB model repo, copy:

```text
requirements-sharpie-public.txt
```

to:

```text
requirements.txt
```

Do not include API keys, service-account JSON files, config files, or raw odds caches in the public repository.
