#!/usr/bin/env python3
import json, os, re, subprocess, time
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
 "FREE_TIER_AUDITOR":["https://textfree.com/free-phone-number/","https://textnow.com/","https://www.talkatone.com/free-talk-and-text-app/"],
 "NUMBER_PERMANENCE_AUDITOR":["https://textfree.com/free-phone-number/","https://help.textnow.com/hc/en-us/articles/360043106673-Help-My-Phone-Number-was-recycled-how-can-I-get-it-back","https://talkatone.zendesk.com/hc/en-us/articles/360037775852-For-how-long-do-I-get-to-keep-my-number"],
 "SIGNUP_FLOW_RESEARCHER":["https://textfree.com/","https://www.textnow.com/signup","https://www.talkatone.com/"]
}

def gh(args, check=False):
    return subprocess.run(["gh",*args],text=True,capture_output=True,check=check)

def comment(body):
    gh(["issue","comment",ISSUE,"--repo",REPO,"--body",body])

def fetch(url):
    r=gh(["api",url.replace("https://api.github.com/","/"),"-H","Accept: application/vnd.github.raw+json"],check=False)
    return r.stdout[:4000] if r.returncode==0 else ""

def main():
    started=datetime.now(timezone.utc).isoformat()
    comment(f"**{SESSION} BOOT** role={ROLE} mission=PHANTOM-20-REAL-NUMBER-001 target={TARGET}")
    evidence={"session_id":SESSION,"role":ROLE,"mission_id":"PHANTOM-20-REAL-NUMBER-001","target_sms_raw":TARGET,"started_at":started}
    if ROLE=="TARGET_VALIDATOR":
        evidence["target_validation"]="PASS_NANP_SHAPE" if re.fullmatch(r"[2-9][0-9]{9}",TARGET) else "FAIL_SHAPE"
        evidence["target_policy"]="Exact target preserved; no guessing or normalization."
    elif ROLE in ROLE_URLS:
        evidence["sources"]=ROLE_URLS[ROLE]
        evidence["research_status"]="READY_FOR_WEB_AUDIT"
        # The worker records the source set; browser-capable roles perform richer inspection in the workflow.
    elif ROLE=="BROWSER_RECON":
        evidence["browser_targets"]=["https://textfree.com/","https://www.textnow.com/signup","https://www.talkatone.com/"]
        evidence["browser_status"]="READY"
    elif ROLE=="CAPTCHA_CHECKPOINT_AUDITOR":
        evidence["checkpoint_rule"]="Observe and report CAPTCHA; never bypass it."
    elif ROLE=="RED_TEAM_COMPLIANCE":
        evidence["red_team"]="No fabricated identity, no anti-bot bypass, no account farming, no disposable-SMS verification."
    elif ROLE=="CROSS_AGENT_SYNTHESIZER":
        evidence["synthesis"]="Will read issue bus after peer check-ins and report contradictions."
    elif ROLE=="FINAL_MESSENGER":
        evidence["send_gate"]="Only send after all gates and provider compliance evidence pass."
    else:
        evidence["status"]="CHECKPOINT"
    Path(OUTPUT/f"{SESSION}.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    comment(f"**{SESSION} CHECKPOINT** role={ROLE} status=READY\nEvidence: `agent-output/{SESSION}.json`")
    return 0

if __name__=="__main__": raise SystemExit(main())