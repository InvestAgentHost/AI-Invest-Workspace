"""Build, audit and render a complete v2 screen from saved evidence."""
import argparse
import json
import hashlib
import os
from pathlib import Path
from html import escape
from urllib.parse import quote
from build_v2 import build
from audit_v2 import audit_files
from render_v2 import render


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('config',type=Path);args=parser.parse_args()
    root=Path.cwd();cfg,_=build(root,args.config);folder=root/cfg['output_dir']
    audit=audit_files(root,folder)
    if audit['errors']:raise ValueError(audit['errors'])
    source_catalog={'as_of':cfg['as_of'],'sources':json.loads((folder/'source-manifest.json').read_text()),
                    'note':'References actually used in the completed report. Initial failed retrieval attempts are preserved separately in manifest.json; neither a failed attempt nor a missing field is evidence of zero.',
                    'initial_attempt_log':'manifest.json'}
    (root/cfg['source_dir']/'manifest-complete.json').write_text(json.dumps(source_catalog,ensure_ascii=False,indent=2)+'\n')
    report=render(root,cfg)
    alias=cfg.get('legacy_html_alias')
    if alias:
        path=root/alias
        if path.exists() and 'stock-screen-v2-alias' not in path.read_text():
            raw=path.read_bytes();backup=path.with_name('report.reverse-v1-'+hashlib.sha256(raw).hexdigest()[:12]+'.html')
            if backup.exists() and backup.read_bytes()!=raw:raise ValueError('Archive name conflict')
            if not backup.exists():backup.write_bytes(raw)
        url=quote(os.path.relpath(root/cfg['html_path'],path.parent),safe='/')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('<!doctype html><!-- stock-screen-v2-alias --><meta charset="utf-8">'
                        +f'<meta http-equiv="refresh" content="0;url={escape(url,quote=True)}">'
                        +f'<title>已更新为完整v2报告</title><p>旧版已保留，完整评分报告已更新。<a href="{url}">打开新版报告</a></p>')
        report['legacy_alias']=alias
    (folder/'render-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'audit':audit['delivery_status'],**report},ensure_ascii=False))


if __name__=='__main__':main()
