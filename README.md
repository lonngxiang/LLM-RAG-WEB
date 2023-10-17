# LLM-RAG-WEB
LLM Model connection LangChain RAG Connection to Streamlit Web


## 1、Brief description

Technology stack:

- Large Language Model: chatglm2
- File processing + faiss: langchain
- Visual interface: streamlit

## 2、Running steps:

1) Modify configuration

  Add embedding model local address to the configs.py file
  
  ```
  ##model address：line 8
  embedding_model_address = "" ## "shibing624/text2vec-base-chinese"
  llm_service_url_address = "" ## fschat address, http://*****:21002
  ```

2) Deploy the model

model deploy : faschat
  run:
    1.python -m fastchat.serve.controller
    2.python -m fastchat.serve.model_worker --model-path ./chatglm2-6b --num-gpus 2 --host=0.0.0.0 --port=21002

3) Run the web
  
  streamlit run  web.py 


![alt text](https://github.com/lonngxiang/LLM-RAG-WEB/blob/main/web.png)

