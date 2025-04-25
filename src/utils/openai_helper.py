from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def get_openai_response(prompt, product_id=None, use_file_search=False, selected_model="gpt-4o-mini"):
    """
    Generate a response from OpenAI API
    
    Args:
        prompt (str): The prompt to send to the API
        product_id (str, optional): Product ID to include in search
        use_file_search (bool, optional): Whether to use file search tool
        selected_model (str, optional): The model to use for the API call
        
    Returns:
        str: The generated response text
    """
    try:
        # Map selected_model value from frontend to actual API model names
        model_mapping = {
            "GPT-4o-MINI": "gpt-4o-mini",
            "GPT-4": "gpt-4",
            "GPT-4 32k": "gpt-4-32k",
            # Default to gpt-4o-mini if not in mapping
        }
        
        # Get the correct model name or default to gpt-4o-mini
        model_name = model_mapping.get(selected_model, "gpt-4o-mini")
        
        # Nếu có product_id và dùng file search, thêm vào prompt để cải thiện tìm kiếm
        if product_id and use_file_search:
            search_prompt = f"{prompt} ProductId: {product_id}"
            
            response = client.responses.create(
                model=model_name,
                input=search_prompt,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": ["vs_6804ef31d9cc8191a9041b697b24a0cc"]
                }]
            )
            
            # Trích xuất nội dung trả về từ response
            if hasattr(response, 'output') and len(response.output) > 1:
                output_message = response.output[1]
                if hasattr(output_message, 'content') and len(output_message.content) > 0:
                    content_item = output_message.content[0]
                    if hasattr(content_item, 'text'):
                        return content_item.text
            
            # Nếu không thể trích xuất được text, trả về toàn bộ nội dung
            return str(response)
        else:
            # Sử dụng API chat.completions thông thường
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def get_openai_streaming_response(messages_history, product_id=None, use_file_search=False, selected_model="gpt-4o-mini"):
    """
    Generate a streaming response from OpenAI API using conversation history
    
    Args:
        messages_history (list): List of message dictionaries with 'role' and 'content' keys
                               representing the conversation history
        product_id (str, optional): Product ID to include in search
        use_file_search (bool, optional): Whether to use file search tool
        selected_model (str, optional): The model to use for the API call
    
    Yields:
        str: Chunks of the generated response
    """
    
    try:
        # Map selected_model value from frontend to actual API model names
        model_mapping = {
            "GPT-4o-MINI": "gpt-4o-mini",
            "GPT-4": "gpt-4",
            "GPT-4 32k": "gpt-4-32k",
            # Default to gpt-4o-mini if not in mapping
        }
        
        # Get the correct model name or default to gpt-4o-mini
        model_name = model_mapping.get(selected_model, "gpt-4o-mini")
        
        # Format the messages for OpenAI API
        formatted_messages = []
        for msg in messages_history:
            if isinstance(msg, tuple):
                role, content = msg
                formatted_messages.append({"role": role, "content": content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
        
        # Get the last user message to check if we need to append product_id
        last_user_message = None
        for msg in reversed(formatted_messages):
            if msg.get('role') == 'user':
                last_user_message = msg
                break
        
        # Append product_id to the last user message if needed
        if product_id and use_file_search and last_user_message:
            last_user_message['content'] += f" ProductId: {product_id}"
        
        # Call OpenAI API with the full conversation history
        response = client.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
            
    except Exception as e:
        yield f"Error: {str(e)}"