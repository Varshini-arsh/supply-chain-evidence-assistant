"""Capture current results from the running app and check their expected evidence."""
import datetime as dt
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/".dev-deps"))
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"/"screenshots"
OUT.mkdir(parents=True,exist_ok=True)

def main():
    errors=[]
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1100},device_scale_factor=1)
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto("http://127.0.0.1:8000")
        expect(page.locator("#model-status")).to_contain_text("Local AI + embeddings ready")
        def investigate(question,month,mode):
            page.select_option("#carrier","Atlas")
            page.select_option("#month",month)
            page.select_option("#mode",mode)
            page.fill("#question",question)
            page.click("#investigate")
            page.wait_for_selector("#result:not([hidden])",timeout=180000)
            expect(page.locator("#investigate")).to_be_enabled(timeout=10000)
            result=page.evaluate("() => currentRun")
            results.append(result)
            return result
        live=investigate("Why did delivery performance decline and which SLA policies apply?","2026-02","ai")
        assert live["status"]=="ok"
        assert live["planner"]=="llm" and live["composer"]=="llm"
        assert live["metrics"][0]["on_time_pct"]==65.0
        assert "-25.00 percentage points" in live["answer"]
        assert any(c["document_id"]=="SLA-ATLAS-V2" for c in live["citations"])
        page.locator("#result").screenshot(path=str(OUT/"01-live-ai-results.png"))
        page.locator(".source").first.click()
        page.wait_for_selector("#source-dialog[open]")
        page.locator("#source-dialog").screenshot(path=str(OUT/"02-source-evidence.png"))
        page.click("#close-source")
        page.set_viewport_size({"width":390,"height":844})
        assert page.locator("html").evaluate("(el) => el.scrollWidth <= window.innerWidth")
        page.locator("#result").screenshot(path=str(OUT/"03-mobile-ai-results.png"))
        page.set_viewport_size({"width":1440,"height":1100})
        historical=investigate("What SLA agreement applies?","2026-01","ai")
        assert historical["status"]=="ok" and "90%" in historical["answer"]
        assert any(c["document_id"]=="SLA-ATLAS-V1" for c in historical["citations"])
        assert not any(c["document_id"]=="SLA-ATLAS-V2" for c in historical["citations"])
        page.locator("#result").screenshot(path=str(OUT/"04-historical-policy.png"))
        missing=investigate("What is delivery performance?","2026-03","bm25")
        assert missing["status"]=="insufficient_evidence" and not missing["facts"]
        page.locator("#result").screenshot(path=str(OUT/"05-missing-data.png"))
        page.click("[data-tab=evaluation]")
        page.wait_for_selector("#evaluation-content .card")
        page.locator("#page-evaluation").screenshot(path=str(OUT/"06-evaluation-results.png"))
        browser.close()
    assert not errors,errors
    report={"captured_at":dt.datetime.now(dt.timezone.utc).isoformat(),"passed":True,"checks":["live AI planning and composition","exact shipment KPI and monthly change","current policy citation","historical policy exclusion","missing-data abstention","mobile layout","no browser errors"],"results":results,"browser_errors":errors}
    (ROOT/"results"/"reports"/"capture-checks.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"screenshots":len(list(OUT.glob("*.png"))),"output":str(OUT),"live_elapsed_ms":live["elapsed_ms"],"historical_planner":historical["planner"],"missing_status":missing["status"],"browser_errors":errors},indent=2))

if __name__=="__main__":
    main()

