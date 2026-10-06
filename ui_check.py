"""Headless browser checks; uses installed Edge and isolated temporary data."""
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parent/".dev-deps"))
from playwright.sync_api import sync_playwright, expect
import app
from rag import store
from rag.config import ROOT, REPORTS

def main():
    REPORTS.mkdir(exist_ok=True)
    original=store.DATA
    errors=[]
    with tempfile.TemporaryDirectory() as directory:
        store.DATA=Path(directory)
        for name in ("documents.json","extra_documents.json"):
            shutil.copyfile(ROOT/"data"/name,store.DATA/name)
        store.initialize()
        server=app.ThreadingHTTPServer(("127.0.0.1",0),app.Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        base=f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",headless=True)
                page=browser.new_page(viewport={"width":1440,"height":1000},device_scale_factor=1)
                page.on("pageerror",lambda error:errors.append(str(error)))
                page.goto(base)
                expect(page.locator("#doc-count")).to_have_text(re.compile(r"\d+"))
                page.screenshot(path=str(REPORTS/"desktop-home.png"),full_page=True)
                page.set_viewport_size({"width":390,"height":844})
                assert page.locator("html").evaluate("(el) => el.scrollWidth <= window.innerWidth"),"Mobile horizontal overflow"
                page.screenshot(path=str(REPORTS/"mobile-home.png"),full_page=True)
                page.set_viewport_size({"width":1440,"height":1000})
                page.select_option("#mode","bm25")
                page.click("#investigate")
                page.wait_for_selector("#result:not([hidden])",timeout=30000)
                assert "65%" in page.locator("#kpis").inner_text()
                assert "SOURCE CHECKS PASSED" in page.locator("#verify-badge").inner_text()
                assert "-25.00 percentage points" in page.locator("#facts").inner_text()
                page.locator(".cite").first.click()
                page.wait_for_selector("#source-dialog[open]")
                assert json.loads(page.locator("#source-text").inner_text())["on_time_pct"] == 65.0
                page.click("#close-source")
                page.locator(".source").first.click()
                page.wait_for_selector("#source-dialog[open]")
                assert page.locator("#source-text").inner_text()
                page.click("#close-source")
                page.click("#stage-review")
                page.get_by_role("button",name="Approve local record").first.click()
                expect(page.locator("#reviews")).to_contain_text("approved")
                with page.expect_download() as download_info:
                    page.click("#export-run")
                download=download_info.value
                export_path=REPORTS/"browser-export.json"
                download.save_as(str(export_path))
                assert json.loads(export_path.read_text())["metrics"][0]["on_time_pct"]==65.0
                page.screenshot(path=str(REPORTS/"desktop-investigation.png"),full_page=True)
                page.set_viewport_size({"width":390,"height":844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),"Mobile result overflow"
                page.screenshot(path=str(REPORTS/"mobile-investigation.png"),full_page=True)
                page.set_viewport_size({"width":1440,"height":1000})
                page.select_option("#mode","ai")
                page.click("#investigate")
                page.wait_for_selector("#result:not([hidden])",timeout=120000)
                expect(page.locator("#run-mode")).to_contain_text("LLM-planned",timeout=120000)
                assert "65%" in page.locator("#kpis").inner_text()
                page.screenshot(path=str(REPORTS/"desktop-agentic.png"),full_page=True)
                page.click("[data-tab=library]")
                page.fill("#upload-title","Browser PDF fixture")
                page.select_option("#upload-carrier","Atlas")
                page.set_input_files("#upload-file",str(ROOT/"data"/"sample-policy.pdf"))
                page.click("#upload-button")
                expect(page.locator("#upload-status")).to_contain_text("chunks indexed")
                assert "Browser PDF fixture" in page.locator("#document-rows").inner_text()
                page.screenshot(path=str(REPORTS/"document-library.png"),full_page=True)
                page.click("[data-tab=history]")
                page.wait_for_selector(".history-item")
                page.locator(".history-item button").first.click()
                assert page.locator("#result").is_visible()
                page.click("[data-tab=evaluation]")
                page.wait_for_selector("#evaluation-content .card",timeout=10000)
                page.screenshot(path=str(REPORTS/"evaluation-lab.png"),full_page=True)
                browser.close()
            if errors:
                raise AssertionError("Browser errors: "+str(errors))
            report={"passed":True,"checks":["desktop rendering","mobile layout without horizontal overflow","investigation and exact KPI display","metric source dialog","document source dialog","local review approval","JSON export","PDF upload and indexing","saved history replay","evaluation report display","live LLM-planned UI investigation"],"browser":"Microsoft Edge / Playwright","page_errors":errors}
            (REPORTS/"browser-checks.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            print(json.dumps(report,indent=2))
        finally:
            server.shutdown()
            server.server_close()
            worker.join()
            store.DATA=original

if __name__=="__main__":
    main()

