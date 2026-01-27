# 03_search_test.py
import chromadb

client = chromadb.PersistentClient(path=r"C:/Users/USER/rag/src/data/chroma_db")
collection = client.get_collection(name="indonesia_pdt_docs")

# 표 데이터 수치를 묻는 질문
res = collection.query(query_texts=["인도네시아 PDT 사업성 분석 Case 3 환자 수"], n_results=1)
print(res['documents'][0][0])
