# MCP Server: Filesystem

> Type: MCP Server
> Status: Configured
> Config: `.claude/mcp.json`

---

## Purpose

Gives Claude Code read/write/move access to vault files via the MCP filesystem server. This is the foundational "button" layer -- every file move, creation, and edit can be executed as a structured MCP action.

## Capabilities

| Action | Description |
|--------|-------------|
| Read file | Read any markdown file in the vault |
| Write file | Create or overwrite a file |
| Move file | Move a file between folders (state transition) |
| List directory | Scan folder contents |
| Delete file | Remove a file (requires approval) |

## Scope

Restricted to: `C:\Users\Amena\Desktop\ai-empolyee`

No access outside the vault directory.

## Approval Rules

| Action | Requires Approval |
|--------|-------------------|
| Read | No |
| List | No |
| Write (new file) | No |
| Write (overwrite) | No |
| Move | No |
| Delete | **Yes** -- triggers `approval_request` skill |
