from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from evidence_vault.db.session import get_db, init_db, update_fts, log_action
from evidence_vault.services.encryption import encrypt_bytes, decrypt_bytes
from evidence_vault.services.background import start_background, job_status
import os
import shutil
import io

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/upload")
def upload(file: UploadFile = File(...), db=Depends(get_db)):
    filename = os.path.basename(file.filename)
    dest = os.path.join(UPLOAD_DIR, filename)
    try:
        data = file.file.read()
        enc = encrypt_bytes(data)
        with open(dest, "wb") as out:
            out.write(enc)
        cur = db.execute("INSERT INTO documents (title, filename, uploaded_by, content) VALUES (?, ?, ?, ?)",
                         (filename, filename, "api", ""))
        db.commit()
        doc_id = cur.lastrowid
        # optionally extract text server-side and update FTS
        # update_fts will ignore if FTS not available
        update_fts(db, doc_id, filename, "", filename)
        log_action(db, 'api', 'upload', target=str(doc_id), details=filename)
        return {"ok": True, "filename": filename, "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/download/{doc_id}')
def download(doc_id: int, db=Depends(get_db)):
    row = db.execute('SELECT filename, uploaded_by FROM documents WHERE id=?', (doc_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Not found')
    filename = row['filename']
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='File missing')
    with open(path, 'rb') as fh:
        enc = fh.read()
    data = decrypt_bytes(enc)
    log_action(db, 'api', 'download', target=str(doc_id), details=filename)
    return Response(content=data, media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{filename}"'})

@router.get('/search')
def search(q: str = '', page: int = 1, per_page: int = 20, db=Depends(get_db)):
    offset = (page - 1) * per_page
    if q:
        # try FTS first
        try:
            rows = db.execute("SELECT documents.* FROM documents JOIN documents_fts ON documents_fts.rowid = documents.id WHERE documents_fts MATCH ? LIMIT ? OFFSET ?", (q, per_page, offset)).fetchall()
            total = db.execute("SELECT count(*) FROM documents_fts WHERE documents_fts MATCH ?", (q,)).fetchone()[0]
        except Exception:
            # fallback simple LIKE
            like = f"%{q}%"
            rows = db.execute("SELECT * FROM documents WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?", (like, like, per_page, offset)).fetchall()
            total = db.execute("SELECT count(*) FROM documents WHERE title LIKE ? OR content LIKE ?", (like, like)).fetchone()[0]
    else:
        rows = db.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
        total = db.execute("SELECT count(*) FROM documents").fetchone()[0]
    docs = [dict(r) for r in rows]
    return {"total": total, "page": page, "per_page": per_page, "docs": docs}

@router.post('/analyze_async/{doc_id}')
def analyze_async(doc_id: int, db=Depends(get_db)):
    def heavy_analysis(doc_id):
        # load document content and run simple keyword analysis fallback
        row = db.execute('SELECT content, title FROM documents WHERE id=?', (doc_id,)).fetchone()
        text = row['content'] or ''
        # placeholder for detect_toxicity logic — simple keyword detection
        keywords = ['badword', 'toxic']
        found = [k for k in keywords if k in text.lower()]
        result = {'keywords': found}
        # persist result into audit
        log_action(db, 'api', 'analyze', target=str(doc_id), details=str(result))
        return result

    job_id = start_background(heavy_analysis, doc_id)
    return {"job_id": job_id}

@router.get('/job_status/{job_id}')
def job_status_route(job_id: str):
    return job_status(job_id)