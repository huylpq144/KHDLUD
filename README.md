# Amazon Chatbot

## Overview
The **Amazon Chatbot** is a smart solution designed to help users quickly review products on Amazon by leveraging AI technologies and the power of Streamlit. It scrapes product information and reviews directly from Amazon, offering an efficient way to make informed purchase decisions. The chatbot utilizes **Retrieval-Augmented Generation (RAG)** to extract key information and provide insightful summaries to users.

## Features
- **Product Information Scraping**: The chatbot scrapes detailed product information from Amazon, including titles, descriptions, prices, and specifications.
- **Review Analysis**: It collects user reviews and analyzes them to provide sentiment-based summaries. This allows users to gauge product quality and performance quickly.
- **AI-Powered Summaries**: By using **RAG** (Retrieval-Augmented Generation), the chatbot generates concise and relevant information from both the product details and customer reviews, making it easier for users to decide on a purchase.
- **Interactive User Interface**: Built with **Streamlit**, the chatbot provides an intuitive and interactive user interface, making it accessible even for non-technical users.
  
## How It Works
1. **User Interaction**: The user interacts with the chatbot via a simple Streamlit interface, providing product links or names.
2. **Scraping**: The chatbot uses web scraping techniques to fetch product information and user reviews from Amazon's product pages.
3. **RAG Processing**: The **Retrieval-Augmented Generation** model is employed to extract and summarize the most relevant content from both the product descriptions and reviews.
4. **Result Delivery**: The chatbot delivers a clean, readable summary with key insights about the product, helping users to make quick decisions.

## Video Guide
To learn how to use the Amazon Chatbot, watch the step-by-step video guide here:

[Watch the video guide](https://studenthcmusedu-my.sharepoint.com/:f:/g/personal/21127616_student_hcmus_edu_vn/Emyyjn0PGKtHidtIMXZ38tgBtyc7upnt-XJAQvP7_ip35Q?e=AT9Iob)

## Live Deployment
You can interact with the deployed version of the **Amazon Chatbot** at the following link:

[Amazon Chatbot - Live Deployment](https://khdlud-684432473097.us-central1.run.app/)

![image](https://github.com/user-attachments/assets/7e022c56-78f5-46b6-b661-c3f2d7a7d2ec)



## Installation

To run the **Amazon Chatbot**, follow these steps:

### Prerequisites
- Python 3.7+
- Required libraries: Streamlit, BeautifulSoup, Requests, OpenAI (for AI processing), and others.

### Steps:
1. Clone the repository:

    ```bash
    git clone https://github.com/your-repository-link/amazon-chatbot.git
    cd amazon-chatbot
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Streamlit app:

    ```bash
    streamlit run app.py
    ```

4. The chatbot interface will be available in your browser. Follow the instructions on the screen to start interacting with the chatbot.

## Dependencies
- **Streamlit**: To create the user interface.
- **BeautifulSoup4**: To scrape the product information and reviews from Amazon.
- **Requests**: For handling HTTP requests.
- **OpenAI API**: For processing natural language through RAG (Retrieval-Augmented Generation) techniques.
- **pandas**: For managing and displaying product and review data.

## Usage
Once the app is running, the user can input a product name or Amazon product URL into the chatbot interface. The chatbot will then:
- Scrape the product details and reviews.
- Use **RAG** to summarize the data.
- Present the user with a quick, easy-to-read summary of the product and its reviews.

### Example:

1. Input a product name like "iPhone 13".
2. The chatbot scrapes information from Amazon and provides:
   - Product title, specifications, price, and description.
   - A sentiment analysis summary of customer reviews (positive, negative, or mixed).
   - A summary of pros and cons mentioned by users.

## RAG Process
- **RAG** (Retrieval-Augmented Generation) uses a combination of a retrieval mechanism (finding the most relevant information) and a generative model (creating a concise summary) to provide a high-quality output for the user. This is especially useful in product review analysis, where the chatbot needs to identify key points from numerous reviews and present them in a useful way.

## Contributing
Feel free to contribute to this project by:
- Forking the repository.
- Creating issues and pull requests for new features or bug fixes.
- Providing feedback to improve the chatbot’s functionality.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
