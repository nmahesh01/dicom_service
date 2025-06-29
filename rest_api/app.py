import sys
from flask import Flask, request, jsonify, send_file
from pathlib import Path
import pydicom
import grpc
from sqlalchemy.exc import IntegrityError
import zipfile
import tempfile
from datetime import datetime
import os
from grpc_backend import file_service_pb2, file_service_pb2_grpc

default_upload_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads")))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", default_upload_dir)).resolve()

default_upload_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../converted")))
CONVERTED_DIR = Path(os.environ.get("CONVERTED_DIR", default_upload_dir)).resolve()

app = Flask(__name__)

# Set up gRPC channel and stub
grpc_host = os.environ.get("GRPC_BACKEND_HOST", "localhost")
channel = grpc.insecure_channel(f"{grpc_host}:50051")
grpc_stub = file_service_pb2_grpc.FileServiceStub(channel)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "files" not in request.files:
        return jsonify({"error": "No files part in the request"}), 400
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400
    # for scaling considering - consider moving it to s3 & providing a s3 link for direct upload
    for file in files:
        try:
            grpc_request = file_service_pb2.UploadRequest(filename=file.filename, data=file.read())
            grpc_response = grpc_stub.UploadDicom(grpc_request)
        except grpc.RpcError as e:
            return jsonify({"error": f"gRPC error: {e.details()}"}), 500

    return jsonify({
        "message": "Upload completed for files"
    })

@app.route("/dicom-tags", methods=["POST"])
def get_multiple_dicom_tags():
    data = request.get_json()
    filename = data.get("filename")
    tags = data.get("tags")
    if not filename:
        return {"error": "filename is required"}, 400
    try:
        result = query_tags_via_grpc(filename, tags)
        return jsonify(result)
    except grpc.RpcError as e:
        return {"error": e.details(), "code": e.code().name}, 404

def query_tags_via_grpc(filename, tag_list=None):
    grpc_request = file_service_pb2.TagQueryRequest(file_name=filename,tags=tag_list or [])
    grpc_response = grpc_stub.QueryTags(grpc_request)

    return  {"filename": grpc_response.file_name,
            "tags": [{"tag": t.tag, "value": t.value} for t in grpc_response.results]
    }
 

@app.route("/convert", methods=["POST"])
def convert_dicom_batch():
    data = request.get_json()
    filenames = data.get("filenames")
    if not filenames:
        return jsonify({"error": "Missing or invalid 'filenames' list"}), 400
    exisiting_filename  =[]
    missing_files = []
    directory = UPLOAD_DIR
    if isinstance(filenames, list):
        for filename in filenames:
            if os.path.isfile(os.path.join(directory, filename)):
                exisiting_filename.append(filename)
            else:
                missing_files.append(filename)
    else:
        if os.path.isfile(os.path.join(directory, filenames)):
                exisiting_filename.append(filenames)
        else:
            missing_files.append(filenames)

    if missing_files:
        print(f"Files not found in upload dir: {missing_files}")

    if not exisiting_filename:
        return jsonify({"error": "No valid files found for conversion"}), 404

    try:
        grpc_request = file_service_pb2.BatchFileRequest(filenames=exisiting_filename)
        grpc_response = grpc_stub.BatchConvertToPng(grpc_request)
    except grpc.RpcError as e:
        return jsonify({"error": f"gRPC error: {e.details()}"}), 500
    return send_file(grpc_response.file_path,mimetype=grpc_response.content_type,as_attachment=True,
        download_name=grpc_response.filename)
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


