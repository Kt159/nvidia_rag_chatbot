from dotenv import load_dotenv
from typing import List, Optional
import os
import PyPDF2
from io import BytesIO
import torch
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Document
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.milvus import MilvusVectorStore

from minio import Minio
from pymilvus import Collection, connections, utility

from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding


load_dotenv()

class Indexing_Pipeline():

    """Pipeline for indexing the documents.
       Current implementation supports indexing the documents using NVIDIA and Azure OpenAI models.

    """

    def __init__(self, chunk_size:int = 512):
        self.chunk_size = chunk_size  
        self.collection_name = os.getenv("MILVUS_COLLECTION_NAME", "test")
        self.milvus_port = os.getenv("MILVUS_PORT", 19530)
        self.milvus_host_IP = os.getenv("MILVUS_HOST", "localhost")
        self.model_host = os.getenv("MODEL_HOST", "NVIDIA")
        self.embedder = self.initialize_embedder()
        self.embedder_dims = os.getenv("EMBEDDING_MODEL_DIMS", 1024)
        self.minio_bucket = os.getenv("MINIO_BUCKET_NAME", "test")
        self.minio_client = Minio(
                                endpoint="localhost:9000",
                                access_key='minioadmin',
                                secret_key='minioadmin',
                                secure=False  
                            )
        self.milvus_store = None

    def read_document(self, path:List[str]) -> List[Document]:
        """Reads documents from the given path
        
        Args:
            path (List[str]): List of paths to the files (pdf, docx)
        
        Returns:
            List[Document]: List of documents (each document is a page of the file with associated metadata)
        
        """
        documents = []

        for file_path in path:
            # Fetch the file from MinIO
            file_name = file_path.split("/")[-1]
            response = self.minio_client.get_object(self.minio_bucket, file_name)
            file_content = response.read()  # Read the file as binary
            
            if file_name.endswith('.pdf'):
                # Handle PDF files
                pdf_stream = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_stream)

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_text = page.extract_text() or ""

                     # Sanitize the extracted text
                    pdf_text = pdf_text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

                    documents.append(Document(text=pdf_text, metadata={"file_name": file_name, "page_num": page_num}))

        return documents
    
    def initialize_embedder(self):
        """
        Initializes the embedder based on the model host (NVIDIA or Azure)
        """

        if self.model_host == "NVIDIA":
            os.environ["NVIDIA_API_KEY"] = os.getenv("NVIDIA_API_KEY")
            embedder = NVIDIAEmbedding(
                model=os.getenv('EMBEDDING_MODEL'),
                truncate="END")

        elif self.model_host == "AZURE":
            embedder = AzureOpenAIEmbedding(
                model=os.getenv('EMBEDDING_MODEL'),
                engine=os.getenv('EMBEDDING_MODEL'),
                api_version=os.getenv('LLM_API_VERSION'),
                azure_endpoint=os.getenv('LLM_ENDPOINT'),
                api_key=os.getenv('LLM_API_KEY')
            )

        else:
            raise Exception("Model host not supported. Please choose NVIDIA or AZURE.")    

        return embedder

    def chunk_document(self, documents:List[Document], chunk_size:int) -> List[BaseNode]:
        """Chunks the document into smaller parts

        Args:
            documents (List[Document]): List of documents

        Returns:
            List[BaseNode]: List of chunks
        """
        base_splitter = SentenceSplitter(chunk_size=chunk_size) 
        splitter = SemanticSplitterNodeParser(
            buffer_size=1, breakpoint_percentile_threshold=95, embed_model=self.embedder, base_splitter=base_splitter
        )
        chunks = splitter.get_nodes_from_documents(documents)
        print(f"Chunked the document into {len(chunks)} chunks")

        return chunks
    
    def initialize_milvus_store(self, dim):
        """
        Initializes the milvus store with the given vector dimensions

        Args:
            dim (int): Dimension of the vectors
            collection_name (str): Name of the collection

        Returns:
            str: Message indicating the status of the initialization
        
        """
        if self.milvus_store:
            return f"Milvus store already initialized at {self.milvus_store.uri}, skipping initialization"
        
        connections.connect(host=self.milvus_host_IP, port=self.milvus_port)
        
        # Check if the collection already exists
        if utility.has_collection(self.collection_name):
            print(f"Milvus collection '{self.collection_name}' already exists. Reusing the existing collection.")
            self.milvus_store = MilvusVectorStore(
                collection_name=self.collection_name,
                uri=f"http://{self.milvus_host_IP}:{self.milvus_port}/",
                overwrite=False  # Avoid overwriting the existing collection
            )
        else:
            # Initialize a new collection if it does not exist
            print(f"Milvus collection '{self.collection_name}' does not exist. Initializing a new collection.")
            self.milvus_store = MilvusVectorStore(
                dim=dim,
                collection_name=self.collection_name,
                uri=f"http://{self.milvus_host_IP}:{self.milvus_port}/",
                overwrite=True  
            )
        
        print(f"Initialized Milvus store at {self.milvus_store.uri} with {self.milvus_store.dim} dimensions")
        
   
    def reset_milvus_store(self):
        """
        Resets the milvus store by dropping the collection and recreating empty collection
        """
        connections.connect(host=self.milvus_host_IP, port=self.milvus_port)

        try:
            collection = Collection(name=self.milvus_store.collection_name)
            collection.drop()
            print(f"Deleted {self.milvus_store.collection_name} from milvus store, please re-run the indexing pipeline")
            self.milvus_store = None

        except Exception as e:
            print(f"Error deleting collection: {e}")


    def delete_milvus_indexes_using_filename(self, filename: str):
        """
        Deletes the indexes from the Milvus store based on the filename metadata
        """
        connections.connect(host=self.milvus_host_IP, port=self.milvus_port)
        
        try:
            # Initialize the collection
            collection = Collection(name=self.collection_name)
            
            # Use a filter expression to delete all entries with the specific filename metadata
            expr = f"file_name == '{filename}'"
            collection.delete(expr)
            collection.compact()
        
            print(f"Deleted indexes for {filename} from Milvus store")
            
            # Success message for FastAPI response
            return {"status": "success", "message": f"Deleted indexes for {filename} from Milvus store"}
        
        except Exception as e:
            print("Error deleting from Milvus:", e)
            return {"status": "error", "message": str(e)}
        
    def run(self, path: List[str]) -> VectorStoreIndex:
        """
        Runs the indexing pipeline to index the documents

        Args:
            path (List[str]): List of paths to the files (pdf)

        Returns:
            VectorStoreIndex: VectorStoreIndex object containing the indexed documents
        """
        documents = self.read_document(path)
        chunks = self.chunk_document(documents, chunk_size=self.chunk_size)

        # Initialize Milvus store based on the embedding model
        if not self.milvus_store:
            self.initialize_milvus_store(dim=int(self.embedder_dims))

        # Initialize storage context with Milvus vector store
        storage_context = StorageContext.from_defaults(vector_store=self.milvus_store)

        # Add documents (or chunks) to the index
        index = VectorStoreIndex.from_documents(
            [Document(text=chunk.text) for chunk in chunks], storage_context=storage_context, embed_model=self.embedder
        )

        print(f"Indexed {len(chunks)} chunks into Milvus.")
        return index





        

