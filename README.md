## RAG-Chatbot built using NVIDIA NIM Microservices and LlamaIndex Framework
--------------------------------------------------------------------------------
```plaintext
├── src                     
|   |── app 
|          |── components\ui 
|          |   |── button.tsx           
|          |   |── card.tsx           
|          |   |── input.tsx                
|          |   |── scroll-area.tsx                
|          |   
|          |── FastAPI                # FastAPI backend service
|          |   |── main.py            # Backend routes hosted on uvicorn
|          |   |── indexing.py        # Indexing pipeline (NVIDIA NIM Microservices --> NV-Embed-QA)  
|          |   |── querying.py        # Query pipeline    (NVIDIA NIM Microservices --> NV-Embed-QA + mistralai/mistral-7b-instruct-v0.2) 
|          |   |── Dockerfile         # Dockerfile for FastAPI service
|          |   |── requirements.txt   # Dependencies needed for FastAPI service
|
|── fonts    
|── layout.tsx
|── page.tsx
|── Dockerfile                  # Dockerfile for Next.js application
|── docker-compose.yml          # Docker compose file for easy deployment
|── package.json                # Dependencies needed for Next.js application
|
|── .env                        # Env file for project (See template provided)
├── README.md                   
```

### Project Architecture Overview
![image](https://github.com/user-attachments/assets/3e91f1c2-5987-4b48-bd59-06d81a889e3a)

1. User uploads document on frontend chatbot
2. Document is stored into MinIO Object Store
3. Document enters indexing pipeline where it is chunked and embedded into vectors
4. Vectors are stored in Milvus Vector Store

![image](https://github.com/user-attachments/assets/39893436-81b7-41a0-960e-40519ca87b4f)
1. User queries the chatbot
2. Query enters query pipeline where it is embedded and used to retreive chunks from Milvus
3. Retrieved chunks are passed into Large Langugage Model which answers the query via chatbot
