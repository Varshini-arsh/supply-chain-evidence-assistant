"""Create a shareable source archive without model weights or local databases."""
from pathlib import Path
import zipfile
from rag.config import ROOT

def package():
    output=ROOT/"dist"
    output.mkdir(exist_ok=True)
    target=output/"SupplyChainEvidenceAssistant.zip"
    excluded={"models",".dev-deps",".venv","__pycache__",".git","dist","legacy"}
    files=[]
    for path in ROOT.rglob("*"):
        relative=path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in relative.parts):
            continue
        if path.suffix in (".sqlite3",".pyc",".log",".tmp") or path.name==".env":
            continue
        files.append(path)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path,Path("SupplyChainEvidenceAssistant")/path.relative_to(ROOT))
    print(f"{target} ({len(files)} files, {target.stat().st_size:,} bytes)")
    return target

if __name__=="__main__":
    package()

