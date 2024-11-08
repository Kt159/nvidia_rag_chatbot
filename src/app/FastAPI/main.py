from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from indexing import Indexing_Pipeline 
from querying import Query_Pipeline 
import os
import io
import uvicorn
from minio import Minio
from llama_index.core import Settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Define Pydantic models for request validation
class Document(BaseModel):
    id: str
    text: str

class QueryRequest(BaseModel):
    query: str

# Initialize MinIO client
minio_client = Minio(
    "localhost:9000",  # MinIO URL
    access_key="minioadmin",  # MinIO access key
    secret_key="minioadmin",  # MinIO secret key
    secure=False  # Set to True if using https
)

bucket_name = os.getenv("MINIO_BUCKET_NAME")  # MinIO bucket name
if not minio_client.bucket_exists(bucket_name):
    minio_client.make_bucket(bucket_name)


@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to MinIO.
    """
    try:
        file_content = await file.read()
        file_name = file.filename
        minio_client.put_object(
            bucket_name,
            file_name,
            io.BytesIO(file_content),
            length=len(file_content)
        )
        return JSONResponse(content={"message": "File uploaded successfully", "file_name": file_name})
    except Exception as e:
        return JSONResponse(content={"message": "MinIO upload error", "error": str(e)}, status_code=500)


@app.get("/list_files")
async def list_files():
    """
    List all objects in the MinIO bucket.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            return JSONResponse(content={"message": "Bucket does not exist"}, status_code=404)
        objects = minio_client.list_objects(bucket_name, recursive=True)
        documents = [obj.object_name for obj in objects]
        return JSONResponse(content=documents)
    
    except Exception as e:
        return JSONResponse(content={"message": "Error fetching documents", "error": str(e)}, status_code=500)


@app.delete("/delete_minio")
async def delete_file(request: Request):
    """
    Delete a specific document from MinIO.
    """
    file_name = request.query_params.get("filename")
    if not file_name:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        minio_client.remove_object(bucket_name, file_name)
        return JSONResponse(content={"message": "Document deleted successfully"})
    except Exception as e:
        return JSONResponse(content={"message": "Error deleting document", "error": str(e)}, status_code=500)


# Background task for document indexing
def index_document_in_background(file_path):
    try: 
        indexing_pipeline = Indexing_Pipeline()
        index = indexing_pipeline.run([file_path])
        return index
    
    except Exception as e:
        print(f"Error indexing document: {e}") 


# Helper function for querying
def query_pipeline_execution(query: str):
    try:
        query_pipeline= Query_Pipeline() 
        # Set the embedder and LLM model in the settings
        Settings.embed_model = query_pipeline.embedder
        Settings.llm = query_pipeline.llm_model
        response = query_pipeline.run(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying documents: {e}")


@app.post("/index")
async def index_document(file_name: str):
    try:
        print(f"Attempting to retrieve file from MinIO: {file_name}")
        response = minio_client.get_object(bucket_name, file_name)
        
        if not response:
            raise HTTPException(status_code=404, detail=f"Document '{file_name}' not found in MinIO")

        index = index_document_in_background(file_name)
        return {"index": index}
    
    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Error indexing document: {e}")
    
    finally:
        if 'response' in locals():
            response.close()
            response.release_conn()

# Route to handle document querying
@app.post("/query")
async def query_documents(query: QueryRequest):
    try:
        response = query_pipeline_execution(query.query) 
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving response: {e}")

    
@app.delete("/delete_milvus")
async def delete_indexes(file_name: str = Query(...)):
    try:
        indexing_pipeline = Indexing_Pipeline()
        response = indexing_pipeline.delete_milvus_indexes_using_filename(file_name)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting indexes from milvus: {e}")
    

# Run the FastAPI application
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)