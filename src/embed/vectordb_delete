DB_DIR = "./chroma_db"
COLLECTION = "my_company_analy"


def delete_all_docs(collection, batch_size=5000):
    """
    Chroma 버전 호환:
    - 어떤 버전은 include=["ids"] 불가
    - ids는 get() 결과에 기본 포함되는 경우가 많음
    """
    deleted = 0

    while True:
        # include를 비우거나 최소한으로(메모리 절약)
        res = collection.get(limit=batch_size)  #  include 지정하지 않음
        ids = res.get("ids") or []

        if not ids:
            break

        collection.delete(ids=ids)
        deleted += len(ids)

    return deleted

# 앱 시작 시 1회만 생성/오픈 (중요)
client = chromadb.PersistentClient(path=DB_DIR)
vector_store = Chroma(
    client=client,
    collection_name=COLLECTION,
    embedding_function=embeddings,
)


def lcDocument_chroma_vector_embedding(lc_docs):

    #  문서만 전부 삭제 / 갱신
    deleted = delete_all_docs(vector_store._collection)
    print("deleted =", deleted)

    # 다시 적재
    vector_store.add_documents(lc_docs)

    print("count =", vector_store._collection.count())
    return vector_store
