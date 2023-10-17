import json
import time
from tempfile import NamedTemporaryFile
import os


import streamlit as st
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

import configs
from model import get_response
from split import load_file


# langchain embedding
embedding = HuggingFaceEmbeddings(model_name=configs.embedding_model_address)


st.set_page_config(page_title="LLM-RAG-WEB")
st.title("LLM-RAG-WEB")



def clear_chat_history1():
    del st.session_state.messages
    st.session_state.history1 = [st.session_state.history1[0]]  # 保留初始记录
    # placeholder.empty()

def clear_chat_history2():
    del st.session_state.messages
    st.session_state.history2 = []  

def init_chat_history1():
    with st.chat_message("assistant", avatar='🤖'):
        st.markdown("您好，我是AI助手，很高兴为您服务🥰")

    if "messages1" in st.session_state:
        for message in st.session_state.messages1:
            avatar = '🧑‍💻' if message["role"] == "user" else '🤖'
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
    else:
        st.session_state.messages1 = []

    return st.session_state.messages1

def init_chat_history2():
    with st.chat_message("assistant", avatar='🤖'):
        st.markdown("您好，我是AI助手，很高兴为您服务🥰")

    if "messages2" in st.session_state:
        for message in st.session_state.messages2:
            avatar = '🧑‍💻' if message["role"] == "user" else '🤖'
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
    else:
        st.session_state.messages2 = []

    return st.session_state.messages2


# 初始化变量
if 'history1' not in st.session_state:
    st.session_state.history1 = [["Human","你的昵称为小杰"],["Assistant","好的，小杰明白"]]

# 初始化变量
if 'history2' not in st.session_state:
    st.session_state.history2 = []

# 初始化 session_state
if "enter_pressed" not in st.session_state:
    st.session_state.enter_pressed = False



def main():

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = configs.vector_store
    
    if "faiss_key" not in st.session_state:
        st.session_state.faiss_key = configs.faiss_key
    print("first faiss_key:",configs.faiss_key)

    # 创建侧边栏布局
    sidebar_selection = st.sidebar.selectbox("选择对话类型", ("模型对话", "文件对话"))


    if sidebar_selection == "模型对话":
        st.session_state.faiss_key = False
        messages1 = init_chat_history1()
        print("history1:",st.session_state.history1)
        if prompt := st.chat_input("Shift + Enter 换行, Enter 发送"):
            with st.chat_message("user", avatar='🧑‍💻'):
                st.markdown(prompt)
            messages1.append({"role": "user", "content": prompt})
            print(f"[user] {prompt}", flush=True)
            with st.chat_message("assistant", avatar='🤖'):
                placeholder = st.empty()

                
                st.session_state.history1.append(["Human",prompt])
                st.session_state.history1.append(["Assistant",None])
                print("history1:",st.session_state.history1)
                start=time.time()
                results = get_response(st.session_state.history1)
                for chunk in results.iter_lines(chunk_size=1024,decode_unicode=False, delimiter=b"\0"):
                    if chunk:
                        # print(chunk.decode("utf-8"))
                        response = json.loads(chunk.decode("utf-8"))["text"]
                        # print(response) 

                        placeholder.markdown(response[(len(prompt)+1):])
                end=time.time()
                cost = end-start
                length = len(response[(len(prompt)+1):])
                print(f"{length/cost}tokens/s")
                # print(prompt,response[(len(prompt)+1):])
                st.session_state.history1[-1][1] =response[(len(prompt)+1):]
                
                
                messages1.append({"role": "assistant", "content": response[(len(prompt)+1):]})


                print(json.dumps(messages1, ensure_ascii=False), flush=True)
            

            st.button("清空对话", on_click=clear_chat_history1)

    elif  sidebar_selection == "文件对话":
        ## uploaded_file
        uploaded_file = st.file_uploader("Choose a file")  

        print("st.session_state.faiss_key:",st.session_state.faiss_key)
        if not st.session_state.faiss_key:
            st.session_state.messages2 = []
            messages2 = init_chat_history2()
        else:
            messages2 = init_chat_history2()
        
             
        if uploaded_file is not None:
             
            if not st.session_state.faiss_key:
                print("faiss_key1:",st.session_state.faiss_key)

                # 临时文件保留原文件格式比如pdf后缀
                temp_file = NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
                temp_file.write(uploaded_file.getvalue())
                # 构造包含扩展名的临时文件路径
                file_path = temp_file.name 
                with st.spinner('Reading file...'):
                    text_loader, texts = load_file(file_path)
                st.success('Finished reading file.')
                temp_file.close()
                ## 保存文件向量
                
                st.session_state.vector_store = FAISS.from_documents(texts, embedding)
                st.success('Finished save embedding.')
                st.session_state.faiss_key = True
                

            if st.session_state.faiss_key:
                print("faiss_key2:",st.session_state.faiss_key)
                
                if prompt := st.chat_input("Shift + Enter 换行, Enter 发送"):
                    with st.chat_message("user", avatar='🧑‍💻'):
                        st.markdown(prompt)
                    messages2.append({"role": "user", "content": prompt})
                    print(f"[user] {prompt}", flush=True)
                    with st.chat_message("assistant", avatar='🤖'):
                        placeholder = st.empty() 
                        sim_result = st.session_state.vector_store.similarity_search(prompt)[0].page_content
                        new_prompt = f"""请根据下面单引号内信息简短回答：{prompt}？   '{sim_result}' \n"""
                        # new_prompt =f"""基于以下已知信息，简洁和专业的来回答用户的问题。
                                        
                        #                 已知内容:
                        #                 {sim_result}
                        #                 问题:{prompt}"""
                        st.session_state.history2 = [["Human","你的昵称为小杰"],["Assistant","好的，小杰明白"]]
                        st.session_state.history2.append(["Human",new_prompt])
                        st.session_state.history2.append(["Assistant",None])
                        print("history2:",st.session_state.history2)
                        start=time.time()
                        results = get_response(st.session_state.history2)
                        for chunk in results.iter_lines(chunk_size=1024,decode_unicode=False, delimiter=b"\0"):
                            if chunk:
                                # print(chunk.decode("utf-8"))
                                response = json.loads(chunk.decode("utf-8"))["text"]
                                # print(response) 

                                placeholder.markdown(response[(len(new_prompt)+1):])
                        end=time.time()
                        cost = end-start
                        length = len(response[(len(new_prompt)+1):])
                        print(f"{length/cost}tokens/s")
                        # print(prompt,response[(len(prompt)+1):])
                        st.session_state.history1[-1][1] =response[(len(new_prompt)+1):]
                        
                        
                        messages2.append({"role": "assistant", "content": response[(len(new_prompt)+1):]})
                        print(json.dumps(messages2, ensure_ascii=False), flush=True)

                    st.button("清空对话", on_click=clear_chat_history2)
                


if __name__ == "__main__":
    main()
