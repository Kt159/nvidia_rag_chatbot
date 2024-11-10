# RAG-Chatbot built using NVIDIA NIM Microservices and LlamaIndex Framework
--------------------------------------------------------------------------------
```plaintext
|── root
     |─── src                     
     |      |── app 
     |          |── components/ui 
     |          |       |── button.tsx           
     |          |       |── card.tsx           
     |          |       |── input.tsx                
     |          |       |── scroll-area.tsx                
     |          |
     |          |── fonts
     |          |── lib
     |          |── global.css
     |          |── layout.tsx
     |          |── page.tsx 
     |
     |── FastAPI                  # FastAPI backend service           
     |     |── indexing.py        # Indexing pipeline (NVIDIA NIM Microservices --> Embedding model: nvidia/nv-embedqa-e5-v5)  
     |     |── querying.py        # Query pipeline    (NVIDIA NIM Microservices --> LLM: meta/llama3-8b-instruct)
     |     |── requirements.txt   # Dependencies needed for FastAPI service
     |
     |── main.py                  # Backend routes hosted on uvicorn
     |── data                     # Test document to upload and test out chatbot (you can upload your own documents also)
     |── docker-compose.yml       # Run milvus/minio docker images
     |── .env                     # Env file for project (See template provided)
     |── package.json             # Dependencies needed for Next.js application
     |── README.md
```

## Project Architecture Overview

### Indexing Documents:
![image](https://github.com/user-attachments/assets/3e91f1c2-5987-4b48-bd59-06d81a889e3a)

1. User uploads document on frontend chatbot
2. Document is stored into MinIO Object Store
3. Document enters indexing pipeline where it is chunked and embedded into vectors
4. Vectors are stored in Milvus Vector Store

### Querying Documents:
![image](https://github.com/user-attachments/assets/39893436-81b7-41a0-960e-40519ca87b4f)

5. User queries the chatbot
6. Query enters query pipeline where it is embedded and used to retreive chunks from Milvus
7. Retrieved chunks are passed into Large Langugage Model which answers the query via chatbot


## Instructions to run chatbot
1. Clone repo to local device
2. Input custom parameters in .env file (NVIDIA API key etc.)
3. Set up venv and install dependencies for FastAPI (`pip install -r "FastAPI/requirements.txt"`) 
4. Set up local milvus/minio store (`docker-compose up`)
5. Start FastAPI server (`uvicorn main:app --reload`)
6. Upload and query documents on ([Vercel Deployment](https://nvidia-rag-chatbot.vercel.app/))



