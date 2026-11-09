#!/usr/bin/env python3
"""严格跑豆包：把一个题面发进豆包页面，抓取回答，落运行记录。

前提：Chrome 以 `--remote-debugging-port=9334` 启动并已登录豆包。
没有调试端口时**拒绝运行**，不会伪造结果。

用法：
  python3 tools/run_doubao.py --item 7705055555161788179 --prompt packs/fin01/prompt.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
CDP = "http://127.0.0.1:9334"


def cdp_alive() -> bool:
    try:
        out = subprocess.run(["curl", "-s", "--max-time", "3", CDP + "/json/version"],
                             capture_output=True, text=True)
        return '"Browser"' in out.stdout
    except Exception:                                  # noqa: BLE001
        return False


NODE = r"""
const base='http://127.0.0.1:9334';
const prompt=process.env.PROMPT_TEXT||'';
const targets=await (await fetch(base+'/json/list')).json();
let t=targets.find(x=>x.type==='page'&&x.url.includes('doubao.com/chat'));
if(!t){ console.error('NO_DOUBAO_TAB'); process.exit(3); }
const ws=new WebSocket(t.webSocketDebuggerUrl); let seq=0; const pend=new Map();
ws.addEventListener('message',ev=>{const m=JSON.parse(ev.data); if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id);}});
await new Promise(r=>ws.addEventListener('open',r,{once:true}));
const send=(m,p={})=>new Promise(res=>{const i=++seq;pend.set(i,res);ws.send(JSON.stringify({id:i,method:m,params:p}));});
await send('Runtime.enable');
// 1) 找输入框（contenteditable 或 textarea）
const setText=`(()=>{
  const el=[...document.querySelectorAll('[contenteditable=true],textarea')]
    .filter(e=>e.offsetParent).sort((a,b)=>b.getBoundingClientRect().height-a.getBoundingClientRect().height)[0];
  if(!el) return 'NO_INPUT';
  el.focus();
  if(el.tagName==='TEXTAREA'){ el.value=PROMPT; el.dispatchEvent(new Event('input',{bubbles:true})); }
  else { document.execCommand('insertText',false,PROMPT); }
  return 'OK';
})()`;
const r1=await send('Runtime.evaluate',{expression:setText.replace('PROMPT',JSON.stringify(prompt)),returnByValue:true});
if(r1.result?.result?.value!=='OK'){ console.log(JSON.stringify({ok:false,step:'input',detail:r1.result?.result?.value})); process.exit(4); }
await new Promise(r=>setTimeout(r,600));
// 2) 发送（Enter）
for(const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
await new Promise(r=>setTimeout(r,1500));
// 3) 轮询回答是否稳定
let last='', stable=0, text='';
for(let i=0;i<120;i++){
  await new Promise(r=>setTimeout(r,2000));
  const q=await send('Runtime.evaluate',{expression:`(()=>{const es=[...document.querySelectorAll('[class*=message],[class*=answer],[class*=markdown]')];return es.map(e=>e.innerText).join('\\n').slice(-20000)})()`,returnByValue:true});
  text=q.result?.result?.value||'';
  if(text===last && text.length>50) stable++; else stable=0;
  last=text;
  if(stable>=3) break;
}
const url=await send('Runtime.evaluate',{expression:'location.href',returnByValue:true});
console.log(JSON.stringify({ok:text.length>50,url:url.result?.result?.value,chars:text.length,text}));
ws.close();
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", required=True)
    ap.add_argument("--prompt", default="packs/fin01/prompt.md")
    ap.add_argument("--out", default="runs/fin01")
    a = ap.parse_args()

    if not cdp_alive():
        print("拒绝运行：CDP 9334 不可用。请先以调试端口启动 Chrome 并登录豆包：\n"
              '  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\\n'
              '    --remote-debugging-port=9334 --user-data-dir="$HOME/Library/Application Support/Google/Chrome"',
              file=sys.stderr)
        return 2

    prompt_path = ROOT / a.prompt
    prompt = prompt_path.read_text(encoding="utf-8")
    started = datetime.now(TZ)
    script = Path("/tmp/_fsf_doubao.mjs")
    script.write_text(NODE, encoding="utf-8")
    import os
    env = dict(os.environ, PROMPT_TEXT=prompt)
    proc = subprocess.run(["node", str(script)], capture_output=True, text=True, env=env, timeout=600)
    if proc.returncode != 0:
        print(f"运行失败（exit {proc.returncode}）：{proc.stdout[-400:]} {proc.stderr[-300:]}",
              file=sys.stderr)
        return proc.returncode or 5
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    ended = datetime.now(TZ)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rec = {
        "item_id": a.item,
        "prompt_path": str(prompt_path.relative_to(ROOT)),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "model": "豆包 2.1 Pro（工作任务模式，云电脑，推理强度高）",
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "duration_seconds": int((ended - started).total_seconds()),
        "share_url": payload.get("url", ""),
        "answer_chars": payload.get("chars", 0),
        "answer_text": payload.get("text", ""),
        "status": "COMPLETED" if payload.get("ok") else "NO_ANSWER",
    }
    (out / "doubao_run.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    (out / "doubao_answer.md").write_text(rec["answer_text"], encoding="utf-8")
    print(f"{rec['status']}  {rec['answer_chars']} 字符  {rec['duration_seconds']}s  {rec['share_url']}")
    return 0 if rec["status"] == "COMPLETED" else 6


if __name__ == "__main__":
    raise SystemExit(main())
