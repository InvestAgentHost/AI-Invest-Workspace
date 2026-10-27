#!/usr/bin/env python3
# LOCAL STATUS: Fiscal.ai is disabled for current stock-initial-screen runs; historical compatibility only.
"""Run one Fiscal.ai `execute_code` call outside the chat and save the FULL output to a file,
so large pulls (statements, daily ratios, filing PDFs) never have to pass through the conversation.

Setup (once):  pip install mcp   (tested with mcp 2.3 against a local test server)
  export FISCAL_MCP_URL="<the streamable-HTTP URL of your Fiscal.ai MCP server, as in ~/.codex/config.toml>"
  export FISCAL_MCP_TOKEN="<bearer token, if your Fiscal.ai MCP access uses one>"   # optional

usage:  fiscal_exec.py <code.js> <out.txt> [--tool execute_code]
        fiscal_exec.py --list            # list the server's tools (to check the tool name)
        fiscal_exec.py --docs <out.txt>  # save Fiscal.ai's api_docs once (fact collectors grep it)
Untested against Fiscal.ai from Codex: if the server only accepts browser (OAuth) sign-in, this script cannot connect;
see the SKILL.md section "If fiscal_exec.py cannot connect"."""
import asyncio, os, sys
from contextlib import asynccontextmanager
from mcp import ClientSession
try:    # mcp >= 2.0
    from mcp.client.streamable_http import streamable_http_client as _new, create_mcp_http_client
except ImportError: _new = None
try:    # mcp 1.x
    from mcp.client.streamable_http import streamablehttp_client as _old
except ImportError: _old = None

@asynccontextmanager
async def connect(url, headers):
    if _new:
        async with create_mcp_http_client(headers=headers) as hc:
            async with _new(url, http_client=hc) as streams:
                yield streams[0], streams[1]
    else:
        async with _old(url, headers=headers) as (r, w, _):
            yield r, w

async def run(argv):
    url = os.environ.get('FISCAL_MCP_URL')
    if not url: sys.exit('Set FISCAL_MCP_URL first.')
    tok = os.environ.get('FISCAL_MCP_TOKEN'); headers = {'Authorization': f'Bearer {tok}'} if tok else None
    async with connect(url, headers) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            if argv[:1] == ['--list']:
                for t in (await s.list_tools()).tools: print(t.name)
                return
            if argv[:1] == ['--docs']:   # save the API docs (helper signatures) once per run
                res = await s.call_tool('api_docs', {})
                txt = ''.join((getattr(c, 'text', None) or '') for c in res.content)
                open(argv[1], 'w').write(txt); print(f"{argv[1]}: {len(txt):,} characters"); return
            code_path, out_path = argv[0], argv[1]
            tool = argv[argv.index('--tool') + 1] if '--tool' in argv else 'execute_code'
            res = await s.call_tool(tool, {'code': open(code_path).read()})
            txt = ''.join((getattr(c, 'text', None) or '') for c in res.content)
            if getattr(res, 'isError', False): sys.exit('Fiscal.ai returned an error: ' + txt[:800])
            open(out_path, 'w').write(txt)
            print(f"{out_path}: {len(txt):,} characters")

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    asyncio.run(run(sys.argv[1:]))
