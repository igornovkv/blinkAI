from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class UploadView(APIView):
    def post(self, request, format=None):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file under media/uploads/
        file_path = default_storage.save(f"uploads/{file_obj.name}", ContentFile(file_obj.read()))

        return Response({"message": "File uploaded successfully", "path": file_path}, status=status.HTTP_201_CREATED)

