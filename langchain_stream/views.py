from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import json
from dotenv import load_dotenv

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, ChatMessage,UploadedFile
from django.http import JsonResponse, HttpResponseBadRequest
from django.http import FileResponse
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.chains import create_retrieval_chain
import os
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Qdrant
from langchain.chains.combine_documents import create_stuff_documents_chain
load_dotenv('.env')

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
import os
from langchain_community.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from django.conf import settings

chatbotmemory = {}
rag_chain_store = {}
previous_uploaded_files_counter = 0

# def get_session_history(session_id: str) -> BaseChatMessageHistory:
#     if session_id not in chatbotmemory:
#         chatbotmemory[session_id] = ChatMessageHistory()
#     return chatbotmemory[session_id]    

# llm = ChatGroq(model="llama-3.1-70b-versatile")

# system_prompt = '''
#                     You are an assistant for question-answering tasks. 
#                     Use the following pieces of retrieved context to answer 
#                     the question. If you don't know the answer, say that you 
#                     don't know.
#                     {context}
#         '''

# prompt = ChatPromptTemplate.from_messages(
#             [
#                 ('system',system_prompt),
#                 ('human','{input}')
#             ]
#         )
# runnable_with_history = RunnableWithMessageHistory(
#     llm,
#     get_session_history,
# )

# qa_chain = create_stuff_documents_chain(llm, prompt)
# output_parser = StrOutputParser()

# Chain
# chain = prompt | llm.with_config({"run_name": "model"}) | output_parser.with_config({"run_name": "Assistant"})

class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.previous_file_count = 0
        self.conversational_rag_chain = None
        await self.accept()

        # Send a message confirming connection
        await self.send(text_data=json.dumps({
            "message": "WebSocket connected."
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Parse the incoming message
        text_data_json = json.loads(text_data)
        
        # Check if the message contains conversation info (sent by the client after choosing a conversation)
        if 'conversation_id' in text_data_json:
            print('CONVERSATION ID IS:',text_data_json['conversation_id'])
            self.conversation_id = text_data_json['conversation_id']

            # Check if the RAG chain is already created and available
            # print(rag_chain_store[int(self.conversation_id)])
            if int(self.conversation_id) in rag_chain_store:
                self.conversational_rag_chain = rag_chain_store[int(self.conversation_id)]
                print('self.conversational_rag_chain passed to websocket')
            else:
                await self.send(text_data=json.dumps({
                    'message': 'RAG chain not available. Please upload files to create one.',
                    'sender': 'System'
                }))
                return
        else:
            # Handle message from the client
            message = text_data_json['message']
            print(message)
            conversation = await self.get_conversation(self.conversation_id)

            # Save the message to the database asynchronously
            await self.save_message(conversation, self.scope["user"].username, message, is_user=True, is_ai=False)
            # chat_history.add_message({"role": "user", "content": message})
            print('MESSAGE SAVED')
            # Prepare input for the chatbot
            session_config = {
                'configurable': {
                'session_id': str(self.conversation_id),  # Use conversation_id as session_id
                # 'name': conversation.title           # Use the conversation title as the name
                }
            }
            self.chat_history = [
                                ("user", message),
                                ("ai", 'I am here to analyze documents'),
                            ]
            # Send the message back to the WebSocket (only to this connection)
            await self.send(text_data=json.dumps({
                'message': message,
                'sender': self.scope["user"].username
            }))
            print('MESSAGE SENT')
            # Send the assistant's response
            if not self.conversational_rag_chain:
                await self.send(text_data=json.dumps({
                    'event': 'no_loaded_documents',
                    'message': 'No RAG chain loaded. Please ensure files are uploaded.',
                    'sender': "Assistant"
                }))
            else:
                ai_message = ""
                try:
                    print('trying to send message to llm')
                    # Stream the response
                    async for event in self.conversational_rag_chain.astream_events(
                            {
                                'input':message,
                                "chat_history": self.chat_history,
                            }, 
                            config=session_config, version="v1"):
                        if (
                                    event["event"] == "on_chat_model_stream"
                                ):  
                            ai_message_chunk = event["data"]["chunk"]
                            print(f"{ai_message_chunk.content}", end="")
                            ai_message += event['data']['chunk'].content  # Append each chunk to ai_message
                                # print(ai_message)
                                # Send the chunk to the WebSocket with proper structure
                            await self.send(text_data=json.dumps({
                                'message': event['data']['chunk'].content,
                                'sender': 'Assistant',
                                'event': 'on_chat_model_stream',
                                'run_id': 2

                            }))
                        
                            # print(json.dumps(chunk['data']['chunk'].content))
                    # After the full response is accumulated, save the AI message to the database
                    if ai_message:
                        await self.save_message(conversation, "Assistant", ai_message, is_user=False, is_ai=True)
                        # chat_history.add_message({"role": "assistant", "content": ai_message})

                        # Send the full AI message to the WebSocket
                        await self.send(text_data=json.dumps({
                                'message': ai_message,
                                'sender': "Assistant"
                            }))
                        print('MESSAGE SENT TO WEBSOCKET',json.dumps({
                                'message': ai_message,
                                'sender': "Assistant"
                            }))


                except Exception as e:
                    print('Response not working',e)
                    print(f"Failed with input message: {message}")
                    print(f"Failed with input message: {ai_message}")

    # Send messages to the WebSocket client
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    @sync_to_async
    def get_conversation(self, conversation_id):
        return Conversation.objects.get(pk=conversation_id)

    @sync_to_async
    def save_message(self, conversation, sender, message, is_user, is_ai):
        return ChatMessage.objects.create(
            conversation=conversation, 
            sender=sender, 
            message=message, 
            is_user_message=is_user,
            is_ai_message=is_ai
        )

    @sync_to_async
    def get_uploaded_files(self, conversation_id):
        return list(UploadedFile.objects.filter(conversation_id=conversation_id))


    @sync_to_async
    def get_uploaded_file_count(self, conversation_id):
        return UploadedFile.objects.filter(conversation_id=conversation_id).count()
    

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, ChatMessage, UploadedFile
@login_required
def index(request, conversation_id=None):
    global previous_uploaded_files_counter
    conversation = None
    messages = []
    uploaded_files_counter = 0

    # Get all conversations created by the user
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')

    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        messages = ChatMessage.objects.filter(conversation_id=conversation_id).order_by('timestamp')
        uploaded_files = UploadedFile.objects.filter(conversation_id=conversation_id)
        uploaded_files_counter = uploaded_files.count()

        if request.method == "POST" and request.FILES.get('file_upload'):
            file = UploadedFile.objects.create(
                user=request.user,
                conversation=conversation,
                file=request.FILES['file_upload']
            )
            file.save()

        # After uploading the file, update the RAG chain if the file count changes
        print(uploaded_files_counter, previous_uploaded_files_counter)
        if uploaded_files_counter != previous_uploaded_files_counter:
            try:
                print('Creating rag chain')
                print(conversation_id)
                create_rag_chain(conversation_id)  # Trigger RAG chain creation
                previous_uploaded_files_counter = uploaded_files_counter  # Update the file count
                print('rag chain created')
            except Exception as e:
                return render(request, 'langchain_stream/chat.html', {
                        'error_message': f"Error creating RAG chain: {str(e)}",
                        'messages': messages,
                        'conversation': conversation,
                        'conversations': conversations,
                        'uploaded_files': uploaded_files
                    })

            return redirect('langchain_stream:chat', conversation_id=conversation.id)

        # If no uploaded files exist, render without RAG chain creation
        if not uploaded_files.exists():
            return render(request, 'langchain_stream/chat.html', {
                'messages': messages,
                'conversation': conversation,
                'conversations': conversations,
            })

    else:
        # If no conversation exists, create a new one and redirect
        conversation = Conversation.objects.create(user=request.user)
        return redirect('langchain_stream:chat', conversation_id=conversation.id)

    # Render the page with the conversations and messages
    return render(request, 'langchain_stream/chat.html', {
        'conversation': conversation, 
        'messages': messages,
        'conversations': conversations,
        'uploaded_files': uploaded_files
    })


# Helper functions for creating the RAG chain
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create session history for a conversation."""
    if session_id not in chatbotmemory:
        chatbotmemory[session_id] = ChatMessageHistory()  # Initialize history for the session
    return chatbotmemory[session_id]
    

def load_files_for_conversation(conversation_id):
    """Load all files associated with the conversation."""
    uploaded_files = UploadedFile.objects.filter(conversation__id=conversation_id)
    docs = []
    for file in uploaded_files:
        file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
        file_extension = os.path.splitext(file.file.name)[1].lower()
        if file_extension == '.pdf':
            print('pdf loaded')
            loader = PyPDFLoader(file_path)
        elif file_extension == '.txt':
            print('txt loaded')
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            print('Not supported file format')
            continue
        docs.extend(loader.load())  # Load and add the document content
    return docs


def process_files_for_conversation(conversation_id):
    """Process files and create embeddings for a conversation."""
    docs = load_files_for_conversation(conversation_id)
    if not docs:
        raise Exception("No files found for conversation.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore = Chroma.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever()

    return retriever

from langchain.chains import create_history_aware_retriever
def create_rag_chain(conversation_id):
    print('Starting')
    """Create a RAG chain for the conversation."""
    llm = ChatGroq()
    print('llm initialized')


    ### Contextualize question ###
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    retriever = process_files_for_conversation(conversation_id)
    print('retriever created')
    contextualize_q_llm = llm.with_config(tags=["contextualize_q_llm"])
    history_aware_retriever = create_history_aware_retriever(
        contextualize_q_llm, retriever, contextualize_q_prompt
    )
    ### Contextualize question ###


    system_prompt = '''
                    You are an assistant for question-answering tasks. 
                    Use the following pieces of retrieved context to answer 
                    the question. If you don't know the answer, say that you 
                    don't know.
                    {context}
    '''
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         ('system', system_prompt),
    #         # MessagesPlaceholder("chat_history"),
    #         ('human', '{input}')
    #     ]
    # )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    qa_chain = create_stuff_documents_chain(llm, prompt)
    print('qa created')
    # rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    print('rag_chain created')
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="message",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    # print('conversational_rag_chain created')
    rag_chain_store[conversation_id] = rag_chain
    print(rag_chain_store)
    print(rag_chain)

    return rag_chain



























@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'langchain_stream/conversation_list.html', {'conversations': conversations})


@login_required
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.delete()  # Delete the conversation
    return redirect('langchain_stream:conversation_list')  # Redirect to a new chat after deletion


@login_required
def upload_file(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            UploadedFile.objects.create(user=request.user,conversation=conversation, file=file)
        return redirect('langchain_stream:chat', conversation_id=conversation_id)
    return render(request, 'langchain_stream/chat.html')


@login_required
def download_file(request, file_id):
    try:
        uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        file_path = uploaded_file.file.path
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    except UploadedFile.DoesNotExist:
        return HttpResponseBadRequest("File not found.")
