#Imports
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Define the model and embeddings
from langchain_openai import OpenAIEmbeddings
import os
import dotenv

dotenv.load_dotenv()
#INITIALIZE VECTOR DATABASE
#Embeddings model
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Define Pinecone index name
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone client
pinecone_api_key = os.getenv("PINECONE_API_KEY")

print(f"Pinecone API Key: {'Set' if pinecone_api_key else 'NOT SET'}")
print(f"Pinecone Index Name: {pinecone_index_name or 'NOT SET'}")

if not pinecone_api_key or not pinecone_index_name:
    raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in environment variables")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(pinecone_index_name)

# Initialize the vector store
vector_store = PineconeVectorStore(embedding=embeddings, index=index)

#--------------------------------------------------------------------------------------------------------------------------------------#
#UPLOADS THE LEASE TO VECTOR DATABASE
def upload_pdf_lease(pdf_path: str, pdf_id: str):
    print(f"Starting upload for PDF: {pdf_path} with ID: {pdf_id}")
    
    # Load the single PDF document
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from PDF")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    all_splits = text_splitter.split_documents(documents)
    print(f"Created {len(all_splits)} chunks from PDF")

    # And metadata to the split documents
    for doc in all_splits:
        #Add id to pdf so that if the user decides to upload multiple pdf's, the pdf id can be used to only search 
        #for that pdf in the vector database and not the other pdf's
        doc.metadata["pdf_id"] = pdf_id
    
    #Store the split documents in the vector database
    try:
        print("Attempting to upload to Pinecone...")
        vector_store.add_documents(all_splits)
        print("Successfully uploaded to Pinecone!")
    except Exception as e:
        print(f"Error uploading to Pinecone: {e}")
        raise RuntimeError(f"Failed to upload documents to Pinecone: {e}")
    
    return "Pdf successfully uploaded"