# Source bundles (opt-in)

Each subdirectory here is a **copy-to-enable** source. The committed `.mcp.json`
stays neutral (`.codex/config.toml` / `.cursor/mcp.json` are local-only) — you only
wire a source you actually use. Onboarding is "add what you have," not "delete
what you don't."

A bundle has up to three files:

| File | What it is | Where it goes |
| --- | --- | --- |
| `source.json` | the registry spec (describes the source for planning + prompting) | merge into `config/sources.json` |
| `mcp.snippet.json` | the MCP server block in all three tool shapes | paste into `.mcp.json` / `.codex/config.toml` / `.cursor/mcp.json` |
| `SETUP.md` | credentials + how read-only is enforced for this source | follow it once |

A source that reaches its system without an MCP server — a `cli` or `native`
transport such as **GSC** (`research gsc`) — is **MCP-less**: it ships only
`source.json` and `SETUP.md`, no `mcp.snippet.json`. Enabling it just registers the
spec; no MCP config is touched.

## Enabling a source

The easy way — `research source enable <name>` does the wiring for you:

```bash
uv run research source enable github     # merge source.json + wire all 3 MCP configs
uv run research source list              # show every bundle and which are enabled
uv run research source disable github    # undo
```

Then follow the bundle's `SETUP.md` for credentials and read-only setup. The command
edits your local (git-tracked) MCP configs — that's your opt-in; don't commit them
back to the shared repo, which keeps its committed configs neutral.

By hand, if you prefer:

1. Merge the bundle's `source.json` into `config/sources.json` (create it from
   `config/sources.json.example` if it does not exist). The source becomes
   available as `--no-<name>` / `--<name>-hint` CLI flags.
2. Paste the `mcp.snippet.json` blocks into the three committed MCP configs
   (`claude` → `.mcp.json` `mcpServers`; `cursor` → `.cursor/mcp.json`
   `mcpServers`; `codex_toml` → append to `.codex/config.toml`). Skip this step
   for an MCP-less bundle (no `mcp.snippet.json`).
3. Follow `SETUP.md` for credentials and read-only setup.

## Read-only is mandatory

Every source declares a `read_only_mechanism`. Where read-only is enforceable in
config (e.g. a `/readonly` endpoint or a `--access-mode=restricted` flag), the
bundle's MCP snippet carries it and `tests/test_readonly_contract.py` asserts it.
Where read-only can only be enforced at the credential layer (`credential-only`,
e.g. a view-only account), `SETUP.md` documents it and the test checks that the
note is present. Adding a bundle that violates its declared mechanism fails the
test — by design.
