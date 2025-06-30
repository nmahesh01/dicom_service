# REST API Routes Documentation

This service exposes several endpoints for DICOM file upload, tag querying, and batch conversion.
Tested with curl & Postman. Postman is recommended due to ease of use 

Installation: 
From the root directory: 
1. poetry install 
2. poetry run python3 grpc_backend/server.py -> This starts the server on port 50051
3. poetry run python3 rest_api/app.py -> This starts the application on port 8000

For Docker:
From root directory:
1. docker-compose build
2. docker-compse up

---

## 1. **POST `/upload`**

**Description:**  
Upload one or more DICOM files & add its to the Database along with its metadata + tags. Overwrites a file metadata, if it already exists 

In Postman for the image files -> click on body (below the IP) -> form-data -> in the key column on the right side of the coumn click on "type" and select file -> select the .dcm files in your directory which you want to upload 

**Request:**  
- Content-Type: `multipart/form-data`
- Field: `files` (one or more files)

**Example using `curl`:**
```sh
curl -X POST http://localhost:8000/upload \
  -F "files=@/path/to/your/file1.dcm" \
  -F "files=@/path/to/your/file2.dcm"
```

**Response:**
```json
{
  "message": "Upload completed for files"
}
```

---

## 2. **POST `/dicom-tags`**

**Description:**  
Queries the DB for a given file. It will only work if the file was previously uploaded to the server & added to the DB 

**Request:**  
- Content-Type: `application/json`
- Body:
  ```json
  {
    "filename": "IM000001",
    "tags": ["PatientName", "StudyDate"]
  }
  ```

**Example using `curl`:**
```sh
curl -X POST http://localhost:8000/dicom-tags \
  -H "Content-Type: application/json" \
  -d '{"filename": "IM000001", "tags":"Patient's Name",
        "Institution Name",
        "Study Description"]}'
```

**Response:**
```json
{
  "filename": "IM000001",
  "tags": [
    {"tag": "Patient's Name", "value": "John Doe"},
    ]
}
```

---

## 3. **POST `/convert`**

**Description:**  
Convert one or more DICOM files to PNG (single file) or ZIP (multiple files).
It can handle a batch convert. It writes to the DB the path where the converted image is present as well. 

In POstman for multiple images -> the zip file can be downloaded by clicking on "Save Response" on the right side of the response terminal. 

**Request:**  
- Content-Type: `application/json`
- Body:
  ```json
  {
    "filenames": ["IM000001", "IM000002"]
  }
  ```

**Example using `curl`:**
```sh
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"filenames": ["IM000001", "IM000002"]}' \
  --output converted_images.zip
```

**Response:**  
- Returns a PNG file (if one file) or a ZIP archive (if multiple files).

---

## Notes

- All endpoints run on port `8000` by default.
- Make sure the gRPC backend is running and accessible.

TODO:
Think about optimizing DB structure for scale 
Deploy it to Kubernetes


