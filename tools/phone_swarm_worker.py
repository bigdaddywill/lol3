#!/usr/bin/env python3
import json, os, re, subprocess, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO=os.environ["GITHUB_REPOSITORY"]
ISSUE=os.environ.get("SWARM_ISSUE","2")
SESSION=os.environ["SESSION_ID"]
ROLE=os.environ["ROLE"]
TARGET=os.environ.get("TARGET_SMS","3059278198")
OUTPUT=Path("agent-output"); OUTPUT.mkdir(exist_ok=True)

ROLE_URLS={
 "PROVIDER_RESEARCH_TEXTNOW":["https://help.textnow.com/hc/en-us/articles/360043031633-Getting-started-with-TextNow","https://help.textnow.com/hc/en-us/articles/360043106673-Help-My-Phone-Number-was-recycled-how-can-I-get-it-back"],
 "PROVIDER_RESEARCH_TALKATONE":["https://talkatone.zendesk.com/hc/en-us/articles/360038142291-How-do-I-start","https://talkatone.zendesk.com/hc/en-us/articles/360037775852-For-how-long-do-I-get-to-keep-my-number"],
 "PROVIDER_RESEARCH_GOOGLE_VOICE":["https://support.google.com/voice/"],
 "FREE_TIER_AUDITOR":["https://textfree.com/free-phone-number/","https://help.textnow.com/hc/en-us/articles/360043106673-Help-My-Phone-Number-was-recycled-how-can-I-get-it-back","https://talkatone.zendesk.com/hc/en-us/articles/360037775852-For-how-long-do-I-get-to-keep-my-number"],
 "NUMBER_PERMANENCE_AUDITOR":["https://textfree.com/free-phone-number/","https://help.textnow.com/hc/en-us/articles/360043106673-Help-My-Phone-Number-was-recycled-how-can-I-get-it-back","https://talkatone.zendesk.com/hc/en-us/articles/360037775852-For-how-long-do-I-get-to-keep-my-number"],
 "SIGNUP_FLOW_RESEARCHER":["https://textfree.com/","https://www.textnow.com/signup","https://www.talkatone.com/"],
 "SMS_OUTBOUND_RESEARCHER":["https://textfree.com/free-texting/","https://www.talkatone.com/free-talk-and-text-app/"],
}

def gh(args):
    return subprocess.run(["gh",*args],text=True,capture_output=True)

def comment(body):
    gh(["issue","comment",ISSUE,"--repo",REPO,"--body",body])

def read_bus():
    r=gh(["issue","view",ISSUE,"--repo",REPO,"--comments","--json","comments"])
    if r.returncode!=0: return []
    try: return json.loads(r.stdout).get("comments",[])
    except Exception: return []

def latest_peer(comments):
    for c in reversed(comments):
        body=c.get("body","")
        m=re.search(r"\*\*(PHANTOM-20-\d{2}) (BOOT|CHECKPOINT|INTERAGENT)",body)
        if m and m.group(1)!=SESSION:
            return m.group(1), body[:600]
    return None, None

def fetch_source(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"PHANTOM-20-audit/1.0"})
        with urllib.request.urlopen(req,timeout=20) as r:
            text=r.read().decode("utf-8","replace")
        text=re.sub(r"<script.*?</script>|<style.*?</style>"," ",text,flags=re.I|re.S)
        text=re.sub(r"<[^>]+>"," ",text)
        text=re.sub(r"\s+"," ",text)
        return text[:5000]
    except Exception as e:
        return f"FETCH_ERROR: {e}"

def role_observation(peer_id, peer_body):
    if peer_id:
        return f"ACK {peer_id}: consumed peer message before checkpoint; next action is to test the peer claim against role evidence."
    return "No peer message observed in initial polling window; this is recorded as a coordination gap rather than silently ignored."

def main():
    started=datetime.now(timezone.utc).isoformat()
    comment(f"**{SESSION} BOOT** role={ROLE} mission=PHANTOM-20-REAL-NUMBER-001 target={TARGET}")
    # Explicitly consume the shared bus before producing a conclusion.
    peer_id=None; peer_body=None; comments=[]
    for _ in range(10):
        comments=read_bus()
        peer_id,peer_body=latest_peer(comments)
        if peer_id: break
        time.sleep(3)
    evidence={"session_id":SESSION,"role":ROLE,"mission_id":"PHANTOM-20-REAL-NUMBER-001","target_sms_raw":TARGET,"started_at":started}
    evidence["peer_messages_seen"]=len([c for c in comments if "PHANTOM-20-" in c.get("body","")])
    evidence["responded_to"]=peer_id
    if ROLE=="TARGET_VALIDATOR":
        evidence["target_validation"]="PASS_NANP_SHAPE" if re.fullmatch(r"[2-9][0-9]{9}",TARGET) else "FAIL_SHAPE"
        evidence["target_policy"]="Exact target preserved; no guessing or normalization."
    elif ROLE in ROLE_URLS:
        evidence["sources"]=ROLE_URLS[ROLE]
        evidence["research_status"]="READY_FOR_WEB_AUDIT"
        evidence["source_samples"]={u:fetch_source(u)[:700] for u in ROLE_URLS[ROLE][:2]}
    elif ROLE=="BROWSER_RECON":
        evidence["browser_targets"]=["https://textfree.com/free-phone-number/","https://www.textnow.com/signup","https://www.talkatone.com/"]
        evidence["browser_status"]="READY"
    elif ROLE=="CAPTCHA_CHECKPOINT_AUDITOR":
        evidence["checkpoint_rule"]="Observe and report CAPTCHA; never bypass it."
    elif ROLE=="RED_TEAM_COMPLIANCE":
        evidence["red_team"]="No fabricated identity, no anti-bot bypass, no account farming, no disposable-SMS verification."
    elif ROLE=="CROSS_AGENT_SYNTHESIZER":
        evidence["synthesis"]="Consume peer evidence, compare provider claims, and flag contradictions in the handoff."
    elif ROLE=="FINAL_HANDOFF_COORDINATOR":
        evidence["send_gate"]="Human-controlled final action only; no automated account creation or outbound SMS."
    else:
        evidence["status"]="CHECKPOINT"
    evidence["interagent_observation"]=role_observation(peer_id,peer_body)
    Path(OUTPUT/f"{SESSION}.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    comment(f"**{SESSION} INTERAGENT** read_peer={peer_id or "NONE"} seen={evidence["peer_messages_seen"]} | {evidence["interagent_observation"]}")
    comment(f"**{SESSION} CHECKPOINT** role={ROLE} status=READY peer_consumed={peer_id or "NONE"}\nEvidence: `agent-output/{SESSION}.json`")
    return 0

if __name__=="__main__": raise SystemExit(main())