#This page has endpoints needs for the leases page
from typing import Annotated, List
from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from sqlmodel import and_
from fastapi import APIRouter
#Imports from other files
from backend.app.db.database import get_db
from backend.app.models.models import ConversationHistoryLeases, UserDetails, SavedApartments
from backend.app.schemas import OutputApartmentDetails, QueryRequest
from backend.apartment_data.data import apartments
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import uuid
from datetime import datetime, timezone
from backend.vector_store.vector_database import upload_pdf_lease
from backend.app.agents.summarize_lease_agent import summarize_lease_agent
from backend.app.agents.lease_agent import lease_agent
from langchain_core.messages import HumanMessage, AIMessage,SystemMessage, BaseMessage, ToolMessage
import json
router = APIRouter()

#GETS LEASE TERMS FOR SAVED APARTMENTS TO DISPLAY IN THE TABLE
@router.get("/lease_terms")
def get_lease_terms(db: Session = Depends(get_db)):
    apartments = db.exec(select(SavedApartments)).all()
    #using json to convert the json string back into a python list
    lease_terms_all_apartments = [
        {"address": apartment.address, "lease_terms": json.loads(apartment.lease_terms)} for apartment in apartments
    ]

#    Example Output
#    [
#        {
#            "address": "7200 Gorden Farms Pkwy, Dublin, OH 43016",
#            "lease_terms": ["Flexible", "One year"]
#        },
#        {
#            "address": "5252 Willow Grove Pl S, Dublin, OH 43017",
#            "lease_terms": ["1 Year"]
#        }
#    ]
    return lease_terms_all_apartments


#This Router is called once the user clicks the sumbit button on the Leases Page
@router.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Create a unique file name and created the unique pdf_id to identify the pdf
    pdf_id = str(uuid.uuid4())
    pdf_path = f"pdf/{pdf_id}.pdf"

    # Save the uploaded PDF
    os.makedirs("pdf", exist_ok=True)
    contents = await file.read()
    with open(pdf_path, "wb") as f:
        f.write(contents)

    # Calls the function to store the pdf to Pinecone vector database
    try:
        message = upload_pdf_lease(pdf_path, pdf_id)
        print(message)
    except Exception as e:
        print(f"Error uploading to vector database: {e}")
        return {"error": str(e)}
#    Returns an id number for that pdf
#   {
#        "pdf_id": "f4a7c0e2-52cb-4d41-9132-9b6a8c3e7c99"
#    }
    return {"pdf_id": pdf_id}

#This Router is called once the user clicks the SUMMARIZE button on the Leases Page
@router.get("/summarize_lease/{pdf_id}")
async def summarize_lease(pdf_id: str):
    #Call the summarize lease agent
    important_sections = summarize_lease_agent(pdf_id)
    #Returns a list of the most important parts of the lease TO BE HIGHLITED
    return {"important_sections": important_sections}


#--------------------------------------------This gets the coversation history for the pdf uploaded----------------------------#
@router.get("/get_lease_conversation/{pdf_id}")
def get_lease_conversation(pdf_id: str, db: Session = Depends(get_db)):
    # Get all messages (human + AI), ordered by timestamp
    statement = (
        select(ConversationHistoryLeases)
        .where(ConversationHistoryLeases.pdf_id == pdf_id)
        .order_by(ConversationHistoryLeases.timestamp)
    )
    messages = db.exec(statement).all()

    # [{"sender": "ai", "content": "How can I help you"}, {"sender": "human", "content": "I want to know....."}...... ]
    return [
        {"sender": msg.sender, "content": msg.content} for msg in messages
    ]


#Gets ai_response to user_question and save both to the database (where the lease_agent is called)
@router.put("/save_lease_conversation/{pdf_id}")
def save_lease_conversation(pdf_id: str, query: QueryRequest, db: Session = Depends(get_db),):
    statement = (
        select(ConversationHistoryLeases)
        .where(ConversationHistoryLeases.pdf_id == pdf_id)
        .order_by(ConversationHistoryLeases.timestamp)
    )
    messages = db.exec(statement).all()
    memory = []
    
    #--------------------------------------------------Gather memory and call agent---------------------------------#
    for msg in messages:
        if msg.sender == 'human':
            memory.append(HumanMessage(content = msg.content))
        elif msg.sender == 'ai':
            memory.append(AIMessage(content = msg.content))
    
    # Add the current user question to memory
    memory.append(HumanMessage(content=query.question))
    
    #call the lease agent to get ai_response to user question
    ai_response = lease_agent(memory, pdf_id)
    
    # Extract the AI response content
    if hasattr(ai_response, 'content'):
        ai_content = ai_response.content
    else:
        ai_content = "I'm sorry, I couldn't process your question at this time."

    #------------------------------------------------------------------------------------------------------------------#

    # Save human message
    human_message = ConversationHistoryLeases(
        pdf_id=pdf_id,
        sender="human",
        content=query.question,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(human_message)
    
    # Save AI response
    ai_message = ConversationHistoryLeases(
        pdf_id=pdf_id,
        sender="ai",
        content=ai_content,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(ai_message)
    
    # Commit the changes to the database
    db.commit()
    return {"message": "Conversation saved successfully!", "ai_response": ai_content}