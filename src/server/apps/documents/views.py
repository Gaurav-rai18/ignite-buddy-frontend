import os
import io
import uuid
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import KnowledgeDocument
from server.apps.accounts.models import Cohort, Batch


def format_file_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} GB"


class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        docs = KnowledgeDocument.objects.all()
        data = []
        for d in docs:
            data.append({
                "id": str(d.id),
                "name": d.title,
                "fileName": d.file_name,
                "fileType": d.file_type,
                "sizeBytes": d.size_bytes,
                "sizeFormatted": format_file_size(d.size_bytes),
                "uploadedAt": d.uploaded_at.strftime("%Y-%m-%d %H:%M"),
                "status": d.status,
                "chunks": d.chunks,
                "indexed": d.indexed,
                "audience": d.audience,
                "cohort": d.target_cohort.code if d.target_cohort else None,
                "batch": d.target_batch.full_code if d.target_batch else None,
                "description": d.description,
                "vectorStore": d.vector_store,
                "content": d.content,
                "fileUrl": request.build_absolute_uri(d.file.url) if d.file else None,
            })
        return Response(data)

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name") or Path(upload.name).stem
        audience = request.data.get("audience") or "All students"
        description = request.data.get("description") or f"Uploaded {Path(upload.name).suffix.upper()} knowledge source"
        cohort_id = request.data.get("cohort_id") or request.data.get("target_cohort")
        batch_id = request.data.get("batch_id") or request.data.get("target_batch")

        target_cohort_obj = Cohort.objects.filter(id=cohort_id).first() if cohort_id else None
        target_batch_obj = Batch.objects.filter(id=batch_id).first() if batch_id else None

        is_pdf = upload.name.lower().endswith(".pdf")
        file_type = "PDF" if is_pdf else "TXT"

        content_bytes = upload.read()
        extracted_text = ""
        try:
            if is_pdf:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                extracted_text = "\n\n".join(pages).strip()
            else:
                extracted_text = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            extracted_text = f"Content extracted from {upload.name}"

        # Estimate chunk count
        estimated_chunks = max(1, len(extracted_text) // 600)
        vector_doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Ingest into server RAG knowledge base if available
        try:
            import hashlib
            from server.knowledge.store import get_kb
            from server.knowledge.chunk import chunk_text
            kb = get_kb()
            f_hash = hashlib.sha256(content_bytes).hexdigest()
            stored_chunks = kb.add_document("ignite", upload.name, [(1, extracted_text)], f_hash)
            if stored_chunks:
                estimated_chunks = stored_chunks
        except Exception:
            pass

        # Reset file pointer for storage
        upload.seek(0)

        doc = KnowledgeDocument.objects.create(
            title=name,
            file=upload,
            file_name=upload.name,
            file_type=file_type,
            size_bytes=len(content_bytes),
            status="Ready",
            chunks=estimated_chunks,
            indexed=True,
            audience=audience,
            target_cohort=target_cohort_obj,
            target_batch=target_batch_obj,
            description=description,
            vector_store="SQLite / ChromaDB knowledge base",
            vector_doc_id=vector_doc_id,
            uploaded_by=request.user if request.user and request.user.is_authenticated else None,
            content=extracted_text,
        )

        return Response({
            "id": str(doc.id),
            "name": doc.title,
            "fileName": doc.file_name,
            "fileType": doc.file_type,
            "sizeBytes": doc.size_bytes,
            "sizeFormatted": format_file_size(doc.size_bytes),
            "uploadedAt": doc.uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "status": doc.status,
            "chunks": doc.chunks,
            "indexed": doc.indexed,
            "audience": doc.audience,
            "description": doc.description,
            "vectorStore": doc.vector_store,
            "content": doc.content,
            "fileUrl": request.build_absolute_uri(doc.file.url) if doc.file else None,
        }, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            d = KnowledgeDocument.objects.get(pk=pk)
            return Response({
                "id": str(d.id),
                "name": d.title,
                "fileName": d.file_name,
                "fileType": d.file_type,
                "sizeBytes": d.size_bytes,
                "sizeFormatted": format_file_size(d.size_bytes),
                "uploadedAt": d.uploaded_at.strftime("%Y-%m-%d %H:%M"),
                "status": d.status,
                "chunks": d.chunks,
                "indexed": d.indexed,
                "audience": d.audience,
                "description": d.description,
                "vectorStore": d.vector_store,
                "content": d.content,
                "fileUrl": request.build_absolute_uri(d.file.url) if d.file else None,
            })
        except KnowledgeDocument.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            d = KnowledgeDocument.objects.get(pk=pk)
            if d.file:
                try:
                    d.file.delete(save=False)
                except Exception:
                    pass
            d.delete()
            return Response({"success": True, "id": str(pk)})
        except KnowledgeDocument.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
