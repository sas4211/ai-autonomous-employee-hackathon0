# /In_Progress/cloud/

Tasks currently being processed by the **Cloud agent**.

**Claim-by-move rule:** The Cloud agent moves a task here from `/Needs_Action/cloud/`
atomically (move + git push) to claim ownership.

**Local agent rule:** Never touch files in this folder. If you see a task here, it is
already owned by Cloud. Check `/Pending_Approval/cloud/` for the result when it arrives.
