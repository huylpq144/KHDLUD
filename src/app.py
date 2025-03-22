import streamlit as st
from utils.openai_helper import get_openai_streaming_response

def main():
    st.set_page_config(layout="wide", page_title="Chatbot UI")

    # Sidebar
    st.sidebar.header("Chatbot Configuration")

    # 1) Chọn mô hình
    selected_model = st.sidebar.selectbox(
        "Chọn Model",
        options=["GPT-3.5", "GPT-4", "GPT-4 32k", "Model khác..."]
    )

    # 2) Nhập URL của sản phẩm Amazon
    product_url = st.sidebar.text_input("Nhập Amazon Product URL")

    # 3) Slider chọn số lượng review
    num_reviews = st.sidebar.slider("Số lượng review", min_value=1, max_value=50, value=10)

    # 4) Nút scrape
    if st.sidebar.button("Scrape"):
        st.sidebar.write(f"Đang xử lý scrape {num_reviews} reviews từ: {product_url}")
        # reviews_data = scrape_reviews(product_url, num_reviews)
        pass

    # ------------------------------------------------
    # Phần chính: giao diện chat
    # ------------------------------------------------

    st.title("Chatbot UI Demo")

    # Khởi tạo session_state để lưu trữ lịch sử hội thoại
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    
    # Khởi tạo messages_history cho API
    if "messages_history" not in st.session_state:
        st.session_state.messages_history = [
            {"role": "system", "content": "Bạn là trợ lý AI hữu ích, thân thiện và trung thực."}
        ]

    # Hàm hiển thị một tin nhắn trong khu vực chat
    # role: 'user' hoặc 'assistant'
    # text: nội dung tin nhắn
    def display_message(role, text):
        # Người dùng (hiển thị bên phải, 70% độ rộng)
        if role == "user":
            st.markdown(
                f"""
                <div style='text-align: right; margin: 10px; display: flex; justify-content: flex-end; align-items: flex-start;'>
                    <div style='display: inline-block; background-color: #DCF8C6; padding: 8px 12px; border-radius: 8px; max-width: 70%; margin-right: 8px;'>
                        {text}
                    </div>
                    <div style='width: 36px; height: 36px; border-radius: 50%; background-color: #128C7E; color: white; display: flex; justify-content: center; align-items: center; font-weight: bold;'>
                        <span>👤</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        # Bot (hiển thị 100% độ rộng, bên dưới câu hỏi)
        else:
            st.markdown(
                f"""
                <div style='margin: 10px; display: flex; align-items: flex-start;'>
                    <div style='width: 36px; height: 36px; border-radius: 50%; background-color: #4285F4; color: white; display: flex; justify-content: center; align-items: center; margin-right: 8px; font-weight: bold;'>
                        <span>🤖</span>
                    </div>
                    <div style='display: inline-block; background-color: #F1F0F0; padding: 8px 12px; border-radius: 8px; max-width: 90%;'>
                        {text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Hiển thị lịch sử các tin nhắn
    for role, content in st.session_state.conversation:
        display_message(role, content)

    # Input của chat
    user_input = st.chat_input("Nhập câu hỏi của bạn...")

    # Xử lý khi người dùng ấn Enter
    if user_input:
        # Thêm tin nhắn của user vào hội thoại hiển thị UI
        st.session_state.conversation.append(("user", user_input))
        
        # Thêm tin nhắn user vào history cho API
        st.session_state.messages_history.append({"role": "user", "content": user_input})
        
        # Hiển thị tin nhắn của người dùng ngay lập tức
        display_message("user", user_input)
        
        # Tạo placeholder để hiển thị tin nhắn đang typing
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            """
            <div style='margin: 10px; display: flex; align-items: flex-start;'>
                <div style='width: 36px; height: 36px; border-radius: 50%; background-color: #4285F4; color: white; display: flex; justify-content: center; align-items: center; margin-right: 8px; font-weight: bold;'>
                    <span>🤖</span>
                </div>
                <div style='display: inline-block; background-color: #F1F0F0; padding: 8px 12px; border-radius: 8px;'>
                    <i>Đang nhập...</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        try:
            # Gọi OpenAI API và hiển thị kết quả streaming với toàn bộ lịch sử
            full_response = ""
            for response_chunk in get_openai_streaming_response(st.session_state.messages_history):
                if response_chunk:
                    full_response += response_chunk
                    # Cập nhật phản hồi đang xây dựng
                    typing_placeholder.markdown(
                        f"""
                        <div style='margin: 10px; display: flex; align-items: flex-start;'>
                            <div style='width: 36px; height: 36px; border-radius: 50%; background-color: #4285F4; color: white; display: flex; justify-content: center; align-items: center; margin-right: 8px; font-weight: bold;'>
                                <span>🤖</span>
                            </div>
                            <div style='display: inline-block; background-color: #F1F0F0; padding: 8px 12px; border-radius: 8px; max-width: 90%;'>
                                {full_response}▌
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Xóa placeholder typing và thêm tin nhắn hoàn chỉnh vào hội thoại UI
            typing_placeholder.empty()
            st.session_state.conversation.append(("assistant", full_response))
            
            # Thêm phản hồi của bot vào history cho OpenAI API
            st.session_state.messages_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # Xử lý lỗi nếu có
            error_message = f"Có lỗi xảy ra: {str(e)}"
            typing_placeholder.empty()
            st.session_state.conversation.append(("assistant", error_message))
            display_message("assistant", error_message)

        # Reset ô input về rỗng để sẵn sàng cho câu hỏi tiếp theo
        st.rerun()

if __name__ == "__main__":
    main()