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
├── README.md                   # Project README file
```
