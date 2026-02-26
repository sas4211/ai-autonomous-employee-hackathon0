# /Needs_Action/cloud/

Tasks routed to the **Cloud agent** for draft processing.

Populated by: Gmail watcher (Cloud), social media watcher (Cloud), scheduler.
Consumed by: Cloud agent autonomy loop (claim-by-move to /In_Progress/cloud/).

Cloud agent handles: email triage, draft replies, social post drafts, Odoo read-only queries.
Cloud agent NEVER sends, pays, or approves — all final actions require Local + human approval.
