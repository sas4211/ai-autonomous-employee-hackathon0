# /Pending_Approval/cloud/

Draft outputs from the **Cloud agent** awaiting human review.

When the Cloud agent completes a draft (email reply, social post, invoice),
it writes an approval request file here and pushes to Git.

**Human action:** Review the file, edit if needed, then:
- Move to `/Approved/` to execute (Local agent will send/post)
- Move to `/Rejected/` to discard (Cloud agent logs and skips)
