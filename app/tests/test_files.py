import io

import httpx
from docx import Document
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import OrganizationMember

TXT_MIME = "text/plain"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"
AUDIO_MIME = "audio/mpeg"

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    tokens = await _register(client, email=email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _start_upload(
    client: AsyncClient, headers: dict[str, str], *, filename: str, mime_type: str, size_bytes: int
) -> dict:
    response = await client.post(
        "/api/v1/files/upload-url",
        json={"filename": filename, "mime_type": mime_type, "size_bytes": size_bytes},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def _put_to_presigned_url(url: str, *, content: bytes, content_type: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30.0) as raw_client:
        return await raw_client.put(url, content=content, headers={"Content-Type": content_type})


async def _upload_and_complete(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    filename: str,
    mime_type: str,
    content: bytes,
) -> dict:
    start = await _start_upload(
        client, headers, filename=filename, mime_type=mime_type, size_bytes=len(content)
    )
    put_response = await _put_to_presigned_url(
        start["upload_url"], content=content, content_type=mime_type
    )
    assert put_response.status_code == 200

    complete_response = await client.post(
        "/api/v1/files/complete-upload", json={"file_id": start["file_id"]}, headers=headers
    )
    assert complete_response.status_code == 200
    return complete_response.json()


def _build_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _build_minimal_pdf_bytes(text: str) -> bytes:
    content_stream = f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(content_stream)).encode()
        + b" >>\nstream\n"
        + content_stream
        + b"\nendstream",
    ]

    buffer = bytearray()
    buffer += b"%PDF-1.4\n"
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(buffer))
        buffer += f"{index} 0 obj\n".encode()
        buffer += body
        buffer += b"\nendobj\n"

    xref_offset = len(buffer)
    buffer += f"xref\n0 {len(objects) + 1}\n".encode()
    buffer += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        buffer += f"{offset:010d} 00000 n \n".encode()
    buffer += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    ).encode()
    return bytes(buffer)


async def test_upload_url_rejects_disallowed_mime_type(client: AsyncClient):
    headers = await _auth_headers(client, "files-bad-type@example.com")
    response = await client.post(
        "/api/v1/files/upload-url",
        json={"filename": "malware.zip", "mime_type": "application/zip", "size_bytes": 100},
        headers=headers,
    )
    assert response.status_code == 422


async def test_upload_url_rejects_oversized_declared_size(client: AsyncClient):
    headers = await _auth_headers(client, "files-too-big@example.com")
    response = await client.post(
        "/api/v1/files/upload-url",
        json={
            "filename": "huge.txt",
            "mime_type": TXT_MIME,
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_txt_upload_flow_extracts_real_text(client: AsyncClient):
    headers = await _auth_headers(client, "files-txt-flow@example.com")
    content = b"Hello from a real text file upload."

    file = await _upload_and_complete(
        client, headers, filename="note.txt", mime_type=TXT_MIME, content=content
    )
    assert file["status"] == "ready"

    text_response = await client.get(f"/api/v1/files/{file['id']}/text", headers=headers)
    assert text_response.status_code == 200
    text_body = text_response.json()
    assert text_body["status"] == "extracted"
    assert text_body["extracted_text"] == content.decode("utf-8")


async def test_docx_upload_flow_extracts_real_text(client: AsyncClient):
    headers = await _auth_headers(client, "files-docx-flow@example.com")
    content = _build_docx_bytes("This paragraph came from a real python-docx document.")

    file = await _upload_and_complete(
        client, headers, filename="report.docx", mime_type=DOCX_MIME, content=content
    )
    assert file["status"] == "ready"

    text_response = await client.get(f"/api/v1/files/{file['id']}/text", headers=headers)
    assert text_response.status_code == 200
    text_body = text_response.json()
    assert text_body["status"] == "extracted"
    assert "real python-docx document" in text_body["extracted_text"]


async def test_pdf_upload_flow_extracts_real_text(client: AsyncClient):
    headers = await _auth_headers(client, "files-pdf-flow@example.com")
    content = _build_minimal_pdf_bytes("Hello real pdf extraction")

    file = await _upload_and_complete(
        client, headers, filename="doc.pdf", mime_type=PDF_MIME, content=content
    )
    assert file["status"] == "ready"

    text_response = await client.get(f"/api/v1/files/{file['id']}/text", headers=headers)
    assert text_response.status_code == 200
    text_body = text_response.json()
    assert text_body["status"] == "extracted"
    assert "Hello real pdf extraction" in text_body["extracted_text"]


async def test_audio_file_marks_extraction_unsupported(client: AsyncClient):
    headers = await _auth_headers(client, "files-audio@example.com")
    content = b"not-really-audio-bytes-but-thats-fine-for-this-test"

    file = await _upload_and_complete(
        client, headers, filename="voice.mp3", mime_type=AUDIO_MIME, content=content
    )
    assert file["status"] == "ready"

    text_response = await client.get(f"/api/v1/files/{file['id']}/text", headers=headers)
    assert text_response.status_code == 200
    assert text_response.json()["status"] == "unsupported"

    analyze_response = await client.post(f"/api/v1/files/{file['id']}/analyze", headers=headers)
    assert analyze_response.status_code == 422


async def test_scan_flags_infected_file_and_blocks_access(client: AsyncClient):
    headers = await _auth_headers(client, "files-infected@example.com")
    content = b"this file contains [mock-fail] inside it"

    start = await _start_upload(
        client, headers, filename="bad.txt", mime_type=TXT_MIME, size_bytes=len(content)
    )
    put_response = await _put_to_presigned_url(
        start["upload_url"], content=content, content_type=TXT_MIME
    )
    assert put_response.status_code == 200

    complete_response = await client.post(
        "/api/v1/files/complete-upload", json={"file_id": start["file_id"]}, headers=headers
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "infected"

    download_response = await client.get(
        f"/api/v1/files/{start['file_id']}/download-url", headers=headers
    )
    assert download_response.status_code == 422

    analyze_response = await client.post(
        f"/api/v1/files/{start['file_id']}/analyze", headers=headers
    )
    assert analyze_response.status_code == 422


async def test_document_summary_mock_failure_and_success(client: AsyncClient):
    headers = await _auth_headers(client, "files-summary@example.com")

    failing_docx = _build_docx_bytes("This text intentionally contains [mock-fail] marker.")
    failing_file = await _upload_and_complete(
        client, headers, filename="fail.docx", mime_type=DOCX_MIME, content=failing_docx
    )
    assert failing_file["status"] == "ready"

    failing_analyze = await client.post(
        f"/api/v1/files/{failing_file['id']}/analyze", headers=headers
    )
    assert failing_analyze.status_code == 502

    ok_docx = _build_docx_bytes("This is a perfectly normal document with real content.")
    ok_file = await _upload_and_complete(
        client, headers, filename="ok.docx", mime_type=DOCX_MIME, content=ok_docx
    )

    ok_analyze = await client.post(f"/api/v1/files/{ok_file['id']}/analyze", headers=headers)
    assert ok_analyze.status_code == 200
    assert ok_analyze.json()["status"] == "completed"

    analysis_response = await client.get(
        f"/api/v1/files/{ok_file['id']}/analysis", headers=headers
    )
    assert analysis_response.status_code == 200
    assert "normal document" in analysis_response.json()["summary"]


async def test_download_url_and_delete_flow(client: AsyncClient):
    headers = await _auth_headers(client, "files-download-delete@example.com")
    file = await _upload_and_complete(
        client, headers, filename="download-me.txt", mime_type=TXT_MIME, content=b"download body"
    )

    download_response = await client.get(
        f"/api/v1/files/{file['id']}/download-url", headers=headers
    )
    assert download_response.status_code == 200
    download_url = download_response.json()["download_url"]

    async with httpx.AsyncClient(timeout=30.0) as raw_client:
        fetched = await raw_client.get(download_url)
    assert fetched.status_code == 200
    assert fetched.content == b"download body"

    delete_response = await client.delete(f"/api/v1/files/{file['id']}", headers=headers)
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/files", headers=headers)
    assert file["id"] not in {item["id"] for item in list_response.json()}

    blocked_download = await client.get(f"/api/v1/files/{file['id']}/download-url", headers=headers)
    assert blocked_download.status_code == 404


async def test_files_are_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "files-tenant-one@example.com")
    second_headers = await _auth_headers(client, "files-tenant-two@example.com")

    first_file = await _upload_and_complete(
        client, first_headers, filename="mine.txt", mime_type=TXT_MIME, content=b"tenant one file"
    )
    await _upload_and_complete(
        client, second_headers, filename="theirs.txt", mime_type=TXT_MIME, content=b"tenant two file"
    )

    list_response = await client.get("/api/v1/files", headers=first_headers)
    file_ids = {item["id"] for item in list_response.json()}
    assert file_ids == {first_file["id"]}

    cross_tenant_response = await client.get(
        f"/api/v1/files/{first_file['id']}", headers=second_headers
    )
    assert cross_tenant_response.status_code == 404


async def test_viewer_cannot_start_upload(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "files-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    response = await client.post(
        "/api/v1/files/upload-url",
        json={"filename": "note.txt", "mime_type": TXT_MIME, "size_bytes": 10},
        headers=headers,
    )
    assert response.status_code == 403


async def test_upload_rate_limit_is_enforced(client: AsyncClient):
    headers = await _auth_headers(client, "files-rate-limit@example.com")

    for _ in range(50):
        response = await client.post(
            "/api/v1/files/upload-url",
            json={"filename": "note.txt", "mime_type": TXT_MIME, "size_bytes": 10},
            headers=headers,
        )
        assert response.status_code == 201

    limited_response = await client.post(
        "/api/v1/files/upload-url",
        json={"filename": "note.txt", "mime_type": TXT_MIME, "size_bytes": 10},
        headers=headers,
    )
    assert limited_response.status_code == 429


async def test_oversized_actual_upload_is_rejected_on_complete(client: AsyncClient):
    headers = await _auth_headers(client, "files-oversized-actual@example.com")
    start = await _start_upload(
        client, headers, filename="declared-small.txt", mime_type=TXT_MIME, size_bytes=10
    )

    oversized_content = b"x" * (MAX_FILE_SIZE_BYTES + 1)
    put_response = await _put_to_presigned_url(
        start["upload_url"], content=oversized_content, content_type=TXT_MIME
    )
    assert put_response.status_code == 200

    complete_response = await client.post(
        "/api/v1/files/complete-upload", json={"file_id": start["file_id"]}, headers=headers
    )
    assert complete_response.status_code == 422
