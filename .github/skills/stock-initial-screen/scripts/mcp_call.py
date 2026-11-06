#!/usr/bin/env python3
"""Call FocusAlpha MCP tools outside the chat and save each FULL result to a file (FocusAlpha-only version, v4.11.4), so ten years of
statements and eight years of daily prices for dozens of companies never pass through the conversation.

Setup (once):  pip install mcp
  export FOCUSALPHA_MCP_URL="<the streamable-HTTP URL of your FocusAlpha MCP server, as in ~/.codex/config.toml>"
  export FOCUSALPHA_MCP_TOKEN="<bearer token, if your FocusAlpha access uses one>"   # optional

usage:  mcp_call.py --list                                  # the server's tool names (check the connection)
        mcp_call.py <tool> '<json args>' <out.json>         # one call
        mcp_call.py --batch calls.json                      # [{"tool", "args", "out"}, ...]; a result with next_cursor is followed page by page
                                                            #   into out, out.p2, out.p3 ... (pass all of them to the converters)
If the server accepts only browser (OAuth) sign-in, this script cannot connect: small calls can still run through the MCP tool in the chat,
but never retype a large result into a file by hand. Stop and tell the user.
Never put the user's email or any personal data in a header, URL or User-Agent.
"""
import asyncio, json, os, sys
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

async def call(s, tool, args, out):
    page, path, n = 1, out, 0
    while True:
        res = await s.call_tool(tool, args)
        txt = ''.join((getattr(c, 'text', None) or '') for c in res.content)
        if getattr(res, 'isError', False): print(f"{tool} {json.dumps(args)[:80]}: ERROR {txt[:300]}"); return
        open(path, 'w').write(txt); n += len(txt)
        try: cur = json.loads(txt).get('next_cursor')
        except Exception: cur = None
        if not cur: break
        page += 1; args = dict(args, cursor=cur); path = f"{out}.p{page}"
    print(f"{out}: {page} page(s), {n:,} characters")

async def run(argv):
    url = os.environ.get('FOCUSALPHA_MCP_URL')
    if not url: sys.exit('Set FOCUSALPHA_MCP_URL first.')
    tok = os.environ.get('FOCUSALPHA_MCP_TOKEN'); headers = {'Authorization': f'Bearer {tok}'} if tok else None
    async with connect(url, headers) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            if argv[:1] == ['--list']:
                for t in (await s.list_tools()).tools: print(t.name)
                return
            if argv[:1] == ['--batch']:
                for c in json.load(open(argv[1])): await call(s, c['tool'], c['args'], c['out'])
                return
            await call(s, argv[0], json.loads(argv[1]), argv[2])

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    asyncio.run(run(sys.argv[1:]))
