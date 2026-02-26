# /Updates/

Signals written by the **Cloud agent** for the Local agent to read and merge.

Cloud writes here instead of directly editing Dashboard.md (single-writer rule).
Local scheduler checks this folder every 5 minutes, merges signals into Dashboard.md,
then moves update files to /Done/.

File format: `YYYY-MM-DD_<slug>.md`
