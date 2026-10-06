"""Create a small two-page, text-based fixture without third-party PDF writers."""
from pathlib import Path
from rag.config import DATA

def make_pdf():
    pages=[
        ["SYNTHETIC CARRIER POLICY - DEMONSTRATION ONLY",
         "Vehicle recovery handbook", 
         "Request a replacement vehicle from the carrier manager.",
         "Collect affected shipment IDs before proposing recovery.",
         "Confirm capacity before promising a revised arrival time."],
        ["Evidence and approval requirements",
         "Retain promised dates, delivered dates and incident references.",
         "A local review record needs explicit user approval.",
         "No external email or carrier notification is sent by this demo."]
    ]
    objects=[
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 7 0 R >> >> /Contents 4 0 R >>",
        None,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 7 0 R >> >> /Contents 6 0 R >>",
        None,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    ]
    for index,lines in zip([3,5],pages):
        stream=("BT /F1 12 Tf 50 740 Td 20 TL "+" ".join("("+line+") Tj T*" for line in lines)+" ET").encode()
        objects[index]=b"<< /Length "+str(len(stream)).encode()+b" >>\nstream\n"+stream+b"\nendstream"
    data=bytearray(b"%PDF-1.4\n")
    offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(data))
        data.extend(f"{i} 0 obj\n".encode()+obj+b"\nendobj\n")
    xref=len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(data)

if __name__=="__main__":
    DATA.mkdir(exist_ok=True)
    target=DATA/"sample-policy.pdf"
    target.write_bytes(make_pdf())
    print(target)

