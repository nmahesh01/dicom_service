import pydicom
import numpy as np
from PIL import Image
from pathlib import Path
import grpc
from concurrent import futures
import file_service_pb2
import file_service_pb2_grpc
from tag_extractor import extract_dicom_tags_old
import os
from io import BytesIO
from models import File , DicomTag
from grpc_backend.db import engine, Base, SessionLocal
from sqlalchemy import inspect



default_upload_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads")))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", default_upload_dir)).resolve()

default_upload_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../converted")))
CONVERTED_DIR = Path(os.environ.get("CONVERTED_DIR", default_upload_dir)).resolve()

UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)


class FileServiceServicer(file_service_pb2_grpc.FileServiceServicer):

    def UploadDicom(self, request, context):
        #this method handles the upload of the dicom file + generating the tags and adding them to the database
        filename = request.filename
        request_data = request.data
        input_path = UPLOAD_DIR / filename
        file_size = len(request_data)
        session = SessionLocal()
        try:
            pydicom_data = pydicom.dcmread(BytesIO(request_data))
            # Check if file already exists in DB
            existing_file = session.query(File).filter_by(file_name=filename).first()

            if existing_file:
                print(f"File {filename} exists. Updating.")
                # Delete old tags
                session.query(DicomTag).filter_by(file_id=existing_file.id).delete()
                # Update file entry fields
                existing_file.uploaded_path = str(input_path)
                existing_file.size_bytes = file_size
                # You can also update timestamps, etc. if needed
                file_entry = existing_file
            else:
                file_entry = File(
                    file_name=filename,
                    uploaded_path=str(input_path),
                    size_bytes=file_size
                )
            session.add(file_entry)
            session.flush()  # Ensure file_entry.id is available
            for elem in pydicom_data.iterall():
                tag = DicomTag(
                    file_id=file_entry.id,
                    names=elem.name,
                    value=str(elem.value),
                    tag=str(elem.tag)
                )
                session.add(tag)
            session.commit()

            with open(input_path, "wb") as f:
                f.write(request_data)
            
            message = "File uploaded and parsed."
 
        except Exception as e:
            session.rollback()
            message = f"Failed: {str(e)}"
        
        session.close()

        return file_service_pb2.UploadResponse(
            message=message,
            filename=filename
        )


    def BatchConvertToPng(self, request, context):
        paths = []
        session = SessionLocal()
        for fname in request.filenames:
            file = session.query(File).filter_by(file_name=fname).first()
            if file and file.uploaded_path:
                paths.append((fname, Path(file.uploaded_path)))
            if not paths:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No valid files found.")
                session.close()

                return file_service_pb2.BatchFileResponse()
        if len(paths) == 1:
            fname, input_path = paths[0]
            out_path = CONVERTED_DIR / f"{Path(fname).stem}.png"
            self.dcm_to_png_file(input_path, out_path)
            file.converted_path = str(out_path)
            session.commit()
            session.close()
            return file_service_pb2.BatchFileResponse(
                    file_path=str(out_path),
                    content_type="image/png",
                    filename=fname
                )
        
    @staticmethod
    def dcm_to_png_file(dcm_path: Path, out_path: Path):
        ds = pydicom.dcmread(dcm_path)
        pixels = ds.pixel_array.astype(float)
        scaled = (np.maximum(pixels, 0) / pixels.max()) * 255.0
        scaled = np.uint8(scaled)
        image = Image.fromarray(scaled)
        image.save(out_path)

    
    def QueryTags(self, request, context):
        session = SessionLocal()
        filename = request.file_name
        tag_names = request.tags  # human-readable tag names like "PatientName"

        query = (
            session.query(File.file_name, DicomTag.names, DicomTag.value)
            .join(DicomTag)
            .filter(File.file_name == filename)
            .filter(DicomTag.names.in_(tag_names))
        )

        results = query.all()
        session.close()

        response = file_service_pb2.TagQueryResponse(file_name=filename, results=[])
        for _, tag_name, value in results:
            response.results.append(
                file_service_pb2.Tag(
                    tag=tag_name,
                    value=value
                )
            )
        return response



    def ExtractDicomTags(self, request, context):
        input_path = UPLOAD_DIR / request.filename
        if not input_path.exists():
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("File not found")
            return file_service_pb2.TagResponse()

        try:
            tag_list = list(request.tags)
            result = extract_dicom_tags_old(input_path, tag_list)
            tag_entries = [
                file_service_pb2.TagEntry(tag=tag, name=entry.get("name", ""), value=entry.get("value", entry.get("error", "Error")))
                for tag, entry in result.items()
            ]
            return file_service_pb2.TagResponse(entries=tag_entries)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return file_service_pb2.TagResponse()

def serve():
    Base.metadata.create_all(bind=engine)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server started on port 50051")  # <-- Add this line
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
