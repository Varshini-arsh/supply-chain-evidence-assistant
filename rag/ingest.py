import base64
import binascii
from io import BytesIO
from pathlib import Path
import uuid
from . import store

def ingest(payload):
    title=payload.get("title","")
    if not isinstance(title,str) or not 1<=len(title.strip())<=160:
        raise ValueError("Provide a document title (1-160 characters).")
    carrier=payload.get("carrier","all")
    start=payload.get("start","2026-01")
    end=payload.get("end") or None
    name=payload.get("filename","document.txt")
    if not isinstance(name,str):
        raise ValueError("Invalid filename.")
    name=Path(name.replace("\\","/")).name[:160]
    extension=Path(name).suffix.lower()
    if extension not in (".pdf",".md",".txt"):
        raise ValueError("Upload a text-based PDF, Markdown, or TXT file.")
    try:
        encoded=payload.get("content_base64","")
        if not isinstance(encoded,str):
            raise ValueError("Invalid document encoding.")
        raw=base64.b64decode(encoded,validate=True)
    except (binascii.Error,ValueError) as error:
        raise ValueError("Invalid document encoding.") from error
    if not 0<len(raw)<=5*1024*1024:
        raise ValueError("Document must be 1 byte to 5 MB.")
    if extension==".pdf":
        from pypdf import PdfReader
        try:
            reader=PdfReader(BytesIO(raw))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are unsupported.")
            if len(reader.pages)>80:
                raise ValueError("PDF limit is 80 pages.")
            pages=[]
            for i,page in enumerate(reader.pages,1):
                stream=page.get_contents()
                if stream is not None and len(stream.get_data())>8*1024*1024:
                    raise ValueError("PDF page content is too large.")
                text=page.extract_text() or ""
                if text.strip():
                    pages.append((i,text))
        except ValueError:
            raise
        except Exception as error:
            raise ValueError("PDF could not be parsed.") from error
    else:
        try:
            pages=[(1,raw.decode("utf-8-sig"))]
        except UnicodeDecodeError as error:
            raise ValueError("Text files must use UTF-8 encoding.") from error
    if sum(len(text) for _,text in pages)>600000:
        raise ValueError("Extracted text exceeds the document limit.")
    doc={"id":"UPLOAD-"+uuid.uuid4().hex[:12],"title":title.strip(),"carrier":carrier,"start":start,"end":end,"source_name":name,"synthetic":False}
    return store.add_document(doc,pages)

def ingest_file(path,title,carrier,start,end=None):
    path=Path(path)
    return ingest({"title":title,"carrier":carrier,"start":start,"end":end,"filename":path.name,
                   "content_base64":base64.b64encode(path.read_bytes()).decode()})

