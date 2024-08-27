
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from dotenv import load_dotenv
from .models import ChatMessage, Conversation
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

load_dotenv('.env')


chatbotmemory = {}

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{input}")
])

llm = ChatGroq(model="llama-3.1-70b-versatile")

output_parser = StrOutputParser()
# Chain
chain = prompt | llm.with_config({"run_name": "model"}) | output_parser.with_config({"run_name": "Assistant"})


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Handle WebSocket disconnection
        pass

    async def receive(self, text_data):
        # Parse the incoming message
        text_data_json = json.loads(text_data)
        
        if "file_name" in text_data_json:
            # If a file is uploaded, process the file asynchronously
            file_name = text_data_json["file_name"]
            await self.process_uploaded_file(file_name)
        else:
            # Handle regular text message
            message = text_data_json["message"]
            await self.handle_message(message)

    async def handle_message(self, message):
        """Handle text messages."""
        try:
            # Simulate streaming response (you can use your LLM logic here)
            async for chunk in chain.astream_events({'input': message}, version="v1", include_names=["Assistant"]):
                if chunk["event"] in ["on_parser_start", "on_parser_stream"]:
                    await self.send(text_data=json.dumps(chunk))
        except Exception as e:
            print(e)

    async def process_uploaded_file(self, file_name):
        """Process uploaded file when informed via WebSocket."""
        try:
            # Perform any file processing (in this example, we're just confirming the file exists)
            file_path = default_storage.path(file_name)
            # Do something with the file here (e.g., process its contents)
            
            # Send a success response back to the WebSocket client
            await self.send(text_data=json.dumps({
                'message': f'File {file_name} has been successfully processed.'
            }))
        except Exception as e:
            print(f"Error processing file: {e}")
            await self.send(text_data=json.dumps({
                'message': 'Error processing the uploaded file.'
            }))

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import UploadedFile, Conversation
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # For simplicity, exempting CSRF, but in production, you should handle it properly
def upload_file(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Validate file type
        file_instance = UploadedFile(conversation=conversation, file=uploaded_file)
        file_instance.save()

        return JsonResponse({'message': 'File uploaded successfully', 'file_name': file_instance.file.name})
    
    return JsonResponse({'message': 'File upload failed'}, status=400)
