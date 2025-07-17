import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
from collections import Counter
from PyPDF2 import PdfReader
import requests

# --- Page Setup ---
st.set_page_config(page_title="🧬 Bioinformatics Research Helper")
st.title("🧬 Bioinformatics Research Helper")

st.markdown("""
Upload your **abstracts (CSV or PDF)** and explore biomedical terms, trends, and summaries:
- ☁️ Word Cloud
- 📊 Top Keywords
- 🔍 Keyword Search
- 🧠 AI Summarizer
""")

# --- Functions ---
def extract_text_from_pdf(uploaded_pdf):
    text = ""
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def hf_summarize(text, token):
    API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": text[:1000], "parameters": {"max_length": 100, "min_length": 30}}
    res = requests.post(API_URL, headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()[0]["summary_text"]
    else:
        return None

# --- Upload Section ---
file_type = st.radio("Choose file type to upload:", ["CSV with Abstracts", "PDF File"])
raw_text = ""

if file_type == "CSV with Abstracts":
    uploaded_file = st.file_uploader("📄 Upload CSV file with an 'abstract' column", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "abstract" not in df.columns:
            st.error("❌ CSV must contain an 'abstract' column.")
        else:
            st.success(f"✅ Loaded {len(df)} abstracts.")
            raw_text = " ".join(df['abstract'].dropna().astype(str))

elif file_type == "PDF File":
    uploaded_pdf = st.file_uploader("📄 Upload a PDF file", type=['pdf'])
    if uploaded_pdf:
        raw_text = extract_text_from_pdf(uploaded_pdf)
        st.success("✅ PDF text extracted.")

# --- Tabs Only When Text Available ---
if raw_text:
    cleaned = clean_text(raw_text)
    words = cleaned.split()
    word_counts = Counter(words).most_common(20)

    tab1, tab2, tab3, tab4 = st.tabs(["☁️ Word Cloud", "📊 Keywords", "🔍 Search", "🧠 Summarizer"])

    with tab1:
        st.subheader("☁️ Word Cloud")
        wc = WordCloud(width=600, height=300, background_color="white").generate(cleaned)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

    with tab2:
        st.subheader("📊 Top 20 Keywords")
        common_df = pd.DataFrame(word_counts, columns=["Word", "Frequency"])
        st.dataframe(common_df)

    with tab3:
        st.subheader("🔍 Search for a Biomedical Keyword")
        search_term = st.text_input("Enter a keyword (e.g., crispr, genome, mutation):").lower()
        if search_term:
            matches = [s for s in raw_text.split(". ") if search_term in s.lower()]
            if matches:
                st.write(f"Found {len(matches)} matching sentences:")
                for sent in matches[:5]:
                    st.markdown(f"- {sent.strip()}")
            else:
                st.info("No matches found.")

    with tab4:
        st.subheader("🧠 Summarizer (Hugging Face API)")

        hf_token = st.secrets.get("HF_TOKEN", None)

        if not hf_token:
            st.warning("🔐 Please set your Hugging Face API token in Streamlit secrets as `HF_TOKEN`.")
        else:
            if st.button("🧠 Summarize"):
                with st.spinner("Summarizing via Hugging Face..."):
                    try:
                        summary = hf_summarize(raw_text, hf_token)
                        if summary:
                            st.success("✅ Summary:")
                            st.write(summary)
                            st.download_button("💾 Download Summary", summary, file_name="summary.txt")
                        else:
                            st.error("❌ Summarization failed. Try again or check your API key.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

