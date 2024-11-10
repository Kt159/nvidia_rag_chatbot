from dotenv import load_dotenv
from typing import Union
import os

from pydantic import BaseModel, Field
from llama_index.core import PromptTemplate
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import VectorStoreIndex

from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import connections, utility


load_dotenv()

class Query_Pipeline():

    """Pipeline for querying the vector store. 
       Current implementation supports querying the vector store using Azure OpenAI and NVIDIA models.

    Args:
        model_host (Optional[str], optional): Host of the model (E.g. Azure, NVIDIA). Defaults to "NVIDIA".
        model_name (Optional[str], optional): Name of the model (E.g. gpt-35-turbo, mistralai/mistral-7b-instruct-v0.2). Defaults to "mistralai/mistral-7b-instruct-v0.2".
    
    """
    def __init__(self):
        self.model_host = os.getenv("MODEL_HOST", "NVIDIA")
        self.collection_name = os.getenv("MILVUS_COLLECTION_NAME", "test")
        self.embedder = self.initialize_embedder()  
        self.llm_model = self.initialize_llm_model()

    def initialize_embedder(self):
        if self.model_host == "NVIDIA":
            os.environ["NVIDIA_API_KEY"] = os.getenv("NVIDIA_API_KEY")
            embedder = NVIDIAEmbedding(
                model=os.getenv('EMBEDDING_MODEL', 'nvidia/nv-embedqa-e5-v5'),
                truncate="END")

        elif self.model_host == "AZURE":
            embedder = AzureOpenAIEmbedding(
                model=os.getenv('EMBEDDING_MODEL'),
                engine=os.getenv('EMBEDDING_MODEL'),
                api_version=os.getenv('LLM_API_VERSION'),
                azure_endpoint=os.getenv('LLM_ENDPOINT'),
                api_key=os.getenv('LLM_API_KEY')
            )  

        return embedder
    
    def connect_to_milvus_store(self):
        """
        Connects to an existing Milvus collection if it exists.

        Returns:
            str: Message indicating the status of the connection
        """
        
        # Establish a connection to Milvus
        milvus_host = os.getenv("MILVUS_HOST", "localhost")
        milvus_port = os.getenv("MILVUS_PORT", 19530)

        connections.connect(host=milvus_host, port=milvus_port)
        
        # Check if the collection already exists
        if utility.has_collection(self.collection_name):
            print(f"Milvus collection '{self.collection_name}' exists. Querying from collection.")
            milvus_store = MilvusVectorStore(
                collection_name=self.collection_name,
                uri=f"http://{milvus_host}:{milvus_port}/",
                overwrite=False,
                consistency_level="Strong"
            )
            
            return milvus_store
        
        else:
            raise Exception(f"Milvus collection '{self.collection_name}' does not exist. Please index documents before querying.")
        
    def initalize_retriever(self):
        milvus_store = self.connect_to_milvus_store()
        index = VectorStoreIndex.from_vector_store(vector_store=milvus_store, embed_model=self.embedder)
        retriever = index.as_retriever(
            similarity_top_k=5,
        )

        return retriever

    def initialize_llm_model(self):
        if self.model_host == "AZURE":
            llm_model = AzureOpenAI(model=os.getenv('LLM_MODEL'),
                                    engine=os.getenv('LLM_MODEL'),
                                    api_version=os.getenv('LLM_API_VERSION'),
                                    azure_endpoint=os.getenv('LLM_ENDPOINT'),
                                    api_key=os.getenv('LLM_API_KEY')
                                    )

        elif self.model_host == "NVIDIA":
            llm_model = NVIDIA(model=os.getenv('LLM_MODEL'))

        else:
            raise ValueError("Unsupported model host specified in configuration.")

        return llm_model
    
    
    def run(self, query:str):
        
        """Run the query pipeline.

        Args:
            query (str): Query

        Returns:
            response: Response to query
        """

        qa_prompt = PromptTemplate( "You are a chatbot assisting a user with a question specific to the provided context. Keep your answers concise and straight to the point.\n"
                                "The context below is retreived from the user's documents. You SHOULD ONLY USE THE USER'S CONTEXT BELOW.\n"
                                "---------------------\n"
                                "User's context: {context_str}\n"
                                "---------------------\n"
                                "If the user's context is not provided or is irrelevant to the query, say I don't have the required context, please upload documents on the left.\n"
                                "DO NOT USE YOUR OWN PRIOR KNOWLEDGE.\n"
                                "Query: {query_str}\n"
                                "You can help the user by formatting your response if the response is long.\n"
                                "Answer: "
                                )
        
        
        # Set up retriever, LLM, and query engine
        retriever = self.initalize_retriever()
        llm = self.llm_model

        query_engine = RAGStringQueryEngine(
            retriever=retriever,
            llm=llm,
            qa_prompt=qa_prompt,
        )

        response = query_engine.custom_query(query_str=query)

        return response
    

class RAGStringQueryEngine(CustomQueryEngine, BaseModel):
    """Custom RAG String Query Engine."""
    
    retriever: BaseRetriever = Field(...)
    llm: Union[NVIDIA, AzureOpenAI] = Field(...)
    qa_prompt: PromptTemplate = Field(...)

    def custom_query(self, query_str: str) -> str:
        # Retrieve relevant nodes
        nodes = self.retriever.retrieve(query_str)
        
        # Generate context string from nodes
        context_str = "\n\n".join([n.node.get_content() for n in nodes])
        
        # Format prompt and query LLM
        formatted_prompt = self.qa_prompt.format(context_str=context_str, query_str=query_str)
        
        if isinstance(self.llm, NVIDIA):
            # NVIDIA chat model requires messages in a specific format
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant. If your output is very long, return the response in shorter point forms"),
                ChatMessage(role=MessageRole.USER, content=formatted_prompt),
            ]
            response = self.llm.chat(messages)

        elif isinstance(self.llm, AzureOpenAI):
            # AzureOpenAI model can directly handle the prompt
            response = self.llm.complete(prompt=formatted_prompt)
     
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        return response_text.replace("assistant: ", "", 1) if response_text.startswith("assistant: ") else response_text
