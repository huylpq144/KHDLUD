from openai import OpenAI
from dotenv import load_dotenv
import os
from helper.crawl_selenium import extract_product_id, is_product_id_in_list


# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(prompt, product_id=None):
    """
    Gets a response from OpenAI using file search
    
    Args:
        prompt (str): The user query
        product_id (str, optional): Product ID to include in the search query
        
    Returns:
        Response: OpenAI API response
    """
    # Nếu có product_id, thêm vào prompt để cải thiện tìm kiếm
    if product_id:
        search_prompt = f"{prompt} ProductId: {product_id}"
    else:
        search_prompt = prompt
        
    response = client.responses.create(
        model="gpt-4o-mini",
        input=search_prompt,
        tools=[{
            "type": "file_search",
            "vector_store_ids": ["vs_6804ef31d9cc8191a9041b697b24a0cc"]
        }]
    )
    return response

if __name__ == "__main__":
    test_url = "https://www.amazon.com/dp/B000084F6F"
    product_id = extract_product_id(test_url)
    
    if product_id:
        print(f"Product ID extracted: {product_id}")
        is_in_list = is_product_id_in_list(product_id)
        print(f"Product ID in list: {is_in_list}")
        
        if is_in_list:
            prompt = f"Đánh giá của sản phẩm có ProductId: {product_id} như thế nào?"
            response = get_openai_response(prompt, product_id)
            print("=== Response ===")
            print(response)
            output = response.output[1]
            content_item = output.content[0]
            text_content = getattr(content_item, "content", getattr(content_item, "text", ""))
            annotations = getattr(content_item, "annotations", [])
            print("\n=== Content ===")
            print(text_content)
            print("\n=== Annotations ===")
            for ann in annotations:
                print(vars(ann))
    else:
        print("Không thể trích xuất Product ID từ URL")