from dotenv import load_dotenv
from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.faiss import FAISS
from askari.guardrails import PolicyGuardrails

pdf_path = "kinondoni_school.pdf"

def main():
    load_dotenv()

    # Initialize the guardrails from the YAML file
    guardrails = PolicyGuardrails()

    # User input (this would typically come from a user interacting with the chatbot)
    user_input = "mention 10 islamic school names in kinondoni?"

    # Check the policy guardrails before proceeding
    policy_check_result = guardrails.enforce_policy(user_input)
    if "Input rejected" in policy_check_result:
        print('This is our check on policy', policy_check_result)
        return

    loader = PyPDFLoader(file_path=pdf_path)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(
        chunk_size=1000, chunk_overlap=50, separator="\n"
    )
    docs = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("vector_db")

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

    llm = ChatOpenAI()

    combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)

    retriever = FAISS.load_local("vector_db", embeddings).as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    response = retrieval_chain.invoke(
        {"input": user_input}
    )

    print(response["answer"])


if __name__ == "__main__":
    main()
