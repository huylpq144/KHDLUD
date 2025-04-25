import streamlit as st
from utils.openai_helper import get_openai_streaming_response
from utils.openai_helper import get_openai_response
from helper.crawl_selenium import get_product_info, extract_product_id, is_product_id_in_list, get_basic_product_info
import time

def main():
    st.set_page_config(layout="wide", page_title="Amazon Chatbot", page_icon="🤖")

    # Sidebar
    st.sidebar.header("Chatbot Configuration")

    # 1) Chọn mô hình
    selected_model = st.sidebar.selectbox(
        "Chọn Model",
        options=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
    )

    # 2) Nhập URL của sản phẩm Amazon
    product_url = st.sidebar.text_input("Nhập Amazon Product URL")

    # Khởi tạo session state cho product data và product id
    if "product_data" not in st.session_state:
        st.session_state.product_data = None
    
    if "product_id" not in st.session_state:
        st.session_state.product_id = None
        
    if "use_file_search" not in st.session_state:
        st.session_state.use_file_search = False
    
    # Khởi tạo session state để theo dõi URL hiện tại và trước đó
    if "current_url" not in st.session_state:
        st.session_state.current_url = ""
    
    if "previous_url" not in st.session_state:
        st.session_state.previous_url = ""

    # Kiểm tra xem URL có thay đổi không
    if product_url != st.session_state.current_url:
        st.session_state.previous_url = st.session_state.current_url
        st.session_state.current_url = product_url
        
        # Reset system message khi URL thay đổi
        if "messages_history" in st.session_state:
            for i, msg in enumerate(st.session_state.messages_history):
                if msg.get("role") == "system":
                    st.session_state.messages_history[i] = {
                        "role": "system", 
                        "content": "Bạn là trợ lý AI hữu ích, thân thiện và trung thực."
                    }
                    break
        
        # Reset conversation khi URL thay đổi và không rỗng
        if product_url and st.session_state.previous_url and product_url != st.session_state.previous_url:
            st.session_state.conversation = []


    # Khi URL thay đổi, kiểm tra product ID tự động
    if product_url:
        product_id = extract_product_id(product_url)
        if product_id:
            is_in_list = is_product_id_in_list(product_id)
            
            if is_in_list:
                st.sidebar.success(f"✅ Sản phẩm có ID {product_id} đã có trong cơ sở dữ liệu!")
                st.session_state.product_id = product_id
                st.session_state.use_file_search = True
            else:
                st.sidebar.info(f"🔍 Sản phẩm có ID {product_id} không có trong cơ sở dữ liệu. Sẽ dùng scraping.")
                st.session_state.product_id = None
                st.session_state.use_file_search = False
        else:
            st.sidebar.warning("⚠️ Không thể trích xuất ID sản phẩm từ URL. Vui lòng kiểm tra lại URL.")

    # 4) Nút scrape
    if st.sidebar.button("Scrape"):
        # Kiểm tra URL trước khi scrape
        if not product_url:
            st.sidebar.error("⚠️ Vui lòng nhập URL sản phẩm trước khi scrape.")
        else:
            # Reset hoàn toàn session state khi scrape sản phẩm mới
            current_product_id = extract_product_id(product_url)
            if current_product_id != st.session_state.get("last_scraped_product_id", None):
                # Reset tất cả session state liên quan đến sản phẩm
                st.session_state.product_data = None
                st.session_state.product_id = None
                st.session_state.use_file_search = False
                st.session_state.product_summary = None
                st.session_state.conversation = []
                st.session_state.messages_history = [
                    {"role": "system", "content": "Bạn là trợ lý AI hữu ích, thân thiện và trung thực."}
                ]
                # Ghi nhớ ID sản phẩm hiện tại để so sánh sau này
                st.session_state.last_scraped_product_id = current_product_id
            
            # Hiển thị loading spinner trung tâm màn hình
            with st.spinner("Đang xử lý dữ liệu sản phẩm..."):
                # Hiển thị progress bar để cập nhật tiến trình scraping
                progress_bar = st.progress(0)
                
                # Thông báo đang bắt đầu quá trình
                progress_status = st.empty()
                progress_status.info("Đang bắt đầu quá trình scraping...")
                
                # Lấy product ID và thiết lập trạng thái
                product_id = extract_product_id(product_url)
                use_file_search = is_product_id_in_list(product_id) if product_id else False
                st.session_state.product_id = product_id
                st.session_state.use_file_search = use_file_search
                
                # Cập nhật progress bar
                progress_bar.progress(10)
                progress_status.info("Đang tìm kiếm thông tin sản phẩm...")
                
                # --- Luôn scrape thông tin cơ bản sản phẩm bất kể đã có trong cơ sở dữ liệu hay chưa ---
                progress_status.info("Đang scrape thông tin cơ bản cho sản phẩm...")
                
                # Scrape thông tin cơ bản từ URL
                basic_product_info = get_basic_product_info(product_url)
                
                # Cập nhật progress bar
                progress_bar.progress(30)
                
                if use_file_search and product_id:
                    # Nếu sản phẩm đã tồn tại, lấy reviews từ cơ sở dữ liệu
                    progress_status.info("Đang tìm kiếm đánh giá trong cơ sở dữ liệu...")
                    
                    # Lấy reviews từ cơ sở dữ liệu thông qua file search
                    reviews_prompt = f"Liệt kê chi tiết tất cả các đánh giá cho sản phẩm có ProductId {product_id}. Cho mỗi đánh giá, bao gồm: tên người dùng, số sao đánh giá, tiêu đề đánh giá, và nội dung đánh giá."
                    reviews_context = get_openai_response(reviews_prompt, product_id, use_file_search=True, selected_model=selected_model)
                    
                    # Đảm bảo lưu dữ liệu vào session state để sử dụng sau này
                    st.session_state.product_data = {
                        "title": basic_product_info.get('title', 'Không rõ'),
                        "price": basic_product_info.get('price', 'Không rõ'),
                        "rating": basic_product_info.get('rating', 'Không rõ'),
                        "review_count": basic_product_info.get('review_count', 'Không rõ'),
                        "description": basic_product_info.get('description', 'Không rõ'),
                        "reviews_context": reviews_context  # Lưu reviews_context vào session
                    }
                else:
                    # Nếu sản phẩm chưa tồn tại, scrape đầy đủ
                    progress_status.info(f"Đang scrape toàn bộ thông tin sản phẩm từ: {product_url}")
                    
                    # Gọi hàm scrape để lấy thông tin sản phẩm đầy đủ
                    product_data = get_product_info(product_url)

                    # Thêm kiểm tra kết quả scrape
                    if product_data and "error" not in product_data and product_data.get("title") != "Title not found":
                        # Lưu dữ liệu vào session state để sử dụng sau
                        st.session_state.product_data = product_data
                        # ... tiếp tục xử lý như bình thường
                                            # Tạo context từ reviews
                        reviews_context = "Dưới đây là các đánh giá của người dùng về sản phẩm:\n\n"
                        for i, review in enumerate(product_data.get("reviews", [])):
                            reviews_context += f"Review #{i+1}:\n"
                            reviews_context += f"- Tiêu đề: {review.get('title', 'Không có tiêu đề')}\n"
                            reviews_context += f"- Người đánh giá: {review.get('author', 'Ẩn danh')}\n"
                            reviews_context += f"- Nội dung: {review.get('text', 'Không có nội dung')}\n"
                            reviews_context += f"- Ngày: {review.get('date', 'Không rõ ngày')}\n\n"
                        
                        # Lưu reviews_context vào product_data để dùng sau này
                        st.session_state.product_data["reviews_context"] = reviews_context
                    else:
                        # Hiển thị thông báo lỗi và không rerun
                        st.error("Không thể lấy thông tin sản phẩm. Vui lòng thử lại.")
                        # Không gọi st.rerun() ở đây
                        return
                
                    

                
                # Cập nhật progress bar
                progress_bar.progress(60)
                progress_status.info("Đang tạo tóm tắt sản phẩm...")
                
                # Tạo prompt để sinh tóm tắt sản phẩm
                summary_prompt = f"""
                Hãy tạo một bản tóm tắt ngắn gọn về sản phẩm này dựa trên thông tin sau:
                
                THÔNG TIN CƠ BẢN:
                Tên sản phẩm: {basic_product_info.get('title', 'Không rõ')}
                Giá: {basic_product_info.get('price', 'Không rõ')}
                Đánh giá: {basic_product_info.get('rating', 'Không rõ')}
                Số lượng đánh giá: {basic_product_info.get('review_count', 'Không rõ')}
                Mô tả: {basic_product_info.get('description', 'Không rõ')}
                
                Tóm tắt nên bao gồm: Đây là sản phẩm gì, các tính năng chính, điểm mạnh, giá cả, và cảm nhận chung của người dùng.
                """
                
                # Gọi OpenAI để tạo tóm tắt
                product_summary = get_openai_response(summary_prompt, selected_model=selected_model)
                
                # Lưu product_summary vào session_state
                st.session_state.product_summary = product_summary
                
                # Cập nhật progress bar
                progress_bar.progress(80)
                progress_status.info("Đang chuẩn bị thông tin cho chatbot...")
                
                # Lấy reviews_context từ session_state.product_data
                reviews_context = st.session_state.product_data.get("reviews_context", reviews_context)
                
                # Cập nhật system message với thông tin sản phẩm
                system_message = f"""Bạn là trợ lý AI hữu ích, thân thiện và trung thực.
                
                THÔNG TIN SẢN PHẨM {f"(ProductId: {product_id})" if product_id else ""}:
                Tên: {basic_product_info.get('title', 'Không rõ')}
                Giá: {basic_product_info.get('price', 'Không rõ')}
                Đánh giá: {basic_product_info.get('rating', 'Không rõ')}
                Số lượng đánh giá: {basic_product_info.get('review_count', 'Không rõ')}
                Mô tả: {basic_product_info.get('description', 'Không rõ')}
                
                TÓM TẮT SẢN PHẨM:
                {product_summary}
                
                ĐÁNH GIÁ NGƯỜI DÙNG:
                {reviews_context}
                
                Hãy sử dụng thông tin trên để trả lời các câu hỏi của người dùng về sản phẩm này.
                Khi được hỏi về đánh giá hoặc cảm nhận về sản phẩm, hãy dựa vào các đánh giá của người dùng đã cung cấp.
                Khi không có thông tin để trả lời, hãy thừa nhận rằng bạn không có đủ thông tin và không tự tạo ra thông tin giả.
                """
                
                # Reset toàn bộ system message
                if "messages_history" in st.session_state:
                    for i, msg in enumerate(st.session_state.messages_history):
                        if msg.get("role") == "system":
                            st.session_state.messages_history[i] = {"role": "system", "content": system_message}
                            break
                    else:
                        # Nếu không tìm thấy system message, thêm vào đầu danh sách
                        st.session_state.messages_history.insert(0, {"role": "system", "content": system_message})
                else:
                    st.session_state.messages_history = [{"role": "system", "content": system_message}]
                
                # Reset conversation và thêm tin nhắn tự động từ hệ thống
                st.session_state.conversation = []
                st.session_state.conversation.append(("assistant", f"Đã tìm thấy thông tin sản phẩm!\n\n**Tóm tắt sản phẩm:**\n\n{product_summary}"))
                
                # Hiển thị tóm tắt sản phẩm ngay trên màn hình với giao diện đẹp
                summary_container = st.container()
                with summary_container:
                    col1, col2 = st.columns([0.05, 0.95])
                    with col1:
                        st.markdown("✅")
                    with col2:
                        st.success("Đã tìm thấy thông tin sản phẩm!")
                    
                    st.markdown("""
                    <div style='margin: 10px; display: flex; align-items: flex-start;'>
                        <div style='width: 36px; height: 36px; border-radius: 50%; background-color: #4285F4; color: white; display: flex; justify-content: center; align-items: center; margin-right: 8px; font-weight: bold;'>
                            <span>🤖</span>
                        </div>
                        <div style='display: inline-block; background-color: #F1F0F0; padding: 8px 12px; border-radius: 8px; max-width: 90%;'>
                            {summary}
                        </div>
                    </div>
                    """.format(summary=product_summary.replace('\n', '<br>')), unsafe_allow_html=True)
                    
                
                # Hoàn thành progress bar
                progress_bar.progress(100)
                progress_status.success("Hoàn tất!")
                time.sleep(0.5)  # Cho người dùng thấy thông báo hoàn tất
                
                # Xóa các thành phần hiển thị progress
                progress_bar.empty()
                progress_status.empty()
            
            # Buộc Streamlit rerun để hiển thị thay đổi
            st.rerun()

    # ------------------------------------------------
    # Phần chính: giao diện chat
    # ------------------------------------------------

    st.title("Amazon Chatbot")

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
            product_id = st.session_state.product_id if st.session_state.use_file_search else None
            use_file_search = st.session_state.use_file_search
            
            for response_chunk in get_openai_streaming_response(
                st.session_state.messages_history, 
                product_id=product_id,
                use_file_search=use_file_search,
                selected_model=selected_model
            ):
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