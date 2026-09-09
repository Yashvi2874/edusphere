import sys
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import torch
import streamlit as st
from crawl4ai import *

# -------------------------------
# Step 1: Crawl and clean multiple URLs recursively
# -------------------------------
extracted_urls = []

async def crawl_sites(urls):
    all_markdown = ""
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            result = await crawler.arun(
                url=url,
                depth=2,
                same_domain=True,
            )
            cleaned = clean_markdown_links(result.markdown)
            all_markdown += f"\n\n# Source: {url}\n\n" + cleaned
    with open("result_combined.md", "w", encoding="utf-8") as f:
        f.write(all_markdown)
    return all_markdown

def clean_markdown_links(text):
    matches = re.findall(r"https?://[^<]*<((https?:/[^>]*)>)", text)
    for full_match, correct_url in matches:
        extracted_urls.append(correct_url)
        text = text.replace(full_match, correct_url)
    return text

# -------------------------------
# Step 2: Markdown to nested folder tree
# -------------------------------
def parse_markdown_to_tree(markdown):
    class HeadingNode:
        def __init__(self, level, title, parent=None):
            self.level = level
            self.title = title
            self.content = ""
            self.children = []
            self.parent = parent

    lines = markdown.splitlines()
    root = HeadingNode(0, "root")
    current = root

    for line in lines:
        heading_match = re.match(r'^(#+)\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            node = HeadingNode(level, title)

            while current.level >= level:
                current = current.parent

            current.children.append(node)
            node.parent = current
            current = node
        else:
            current.content += line + "\n"

    return root

def save_tree_to_folders(node, base_path, folder_content_map):
    if node.title != "root":
        folder_name = re.sub(r"[^a-zA-Z0-9_-]", "_", node.title.strip())
        folder_path = base_path / folder_name
        folder_path.mkdir(exist_ok=True)
        with open(folder_path / "content.md", "w", encoding="utf-8") as f:
            f.write(node.content.strip())
        folder_content_map[str(folder_path)] = node.content.strip()
        base_path = folder_path

    for child in node.children:
        save_tree_to_folders(child, base_path, folder_content_map)

# -------------------------------
# Step 3: Embedding preparation
# -------------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')
corpus_embeddings = None
folder_names = None
folder_to_content = {}
feedback_map = {}

async def prepare_rag():
    urls = [
        "https://kjsce.somaiya.edu/en/admission/btech",
        "https://scholarships.somaiya.edu/en/",
    ]
    content = await crawl_sites(urls)
    tree = parse_markdown_to_tree(content)

    base_dir = Path("./db")
    base_dir.mkdir(exist_ok=True)

    folder_content_map = {}
    save_tree_to_folders(tree, base_dir, folder_content_map)

    corpus_embeddings = []
    folder_names = []

    for folder, text in folder_content_map.items():
        emb = model.encode(text, convert_to_tensor=True)
        corpus_embeddings.append(emb)
        folder_names.append(folder)

    global folder_to_content
    folder_to_content = folder_content_map

    return torch.stack(corpus_embeddings), folder_names

# -------------------------------
# Step 4: Async setup
# -------------------------------
async def setup():
    global corpus_embeddings, folder_names
    corpus_embeddings, folder_names = await prepare_rag()

# -------------------------------
# Step 5: Rank query and retrieve answers
# -------------------------------
def rank_query(query, top_k=5):
    if corpus_embeddings is None:
        return []
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)[0]
    results = []
    for hit in hits:
        folder = folder_names[hit["corpus_id"]]
        score = float(hit["score"])
        content = folder_to_content.get(folder, "")
        results.append({"folder": folder, "score": score, "content": content})
    return results

# -------------------------------
# Step 6: Streamlit interface
# -------------------------------
st.set_page_config(page_title="RAG Folder Search", layout="centered")
st.title("📁 RAG Directory Ranker")
st.markdown("Enter a question and we'll show you the most relevant sections and their content.")

user_query = st.text_input("🔎 Ask something:", placeholder="e.g. What is the process of international student admission?")

if corpus_embeddings is None:
    with st.spinner("🚀 Crawling and preparing content..."):
        asyncio.run(setup())

if user_query:
    ranked = rank_query(user_query)
    st.subheader("📂 Top Relevant Answers:")
    for i, item in enumerate(ranked):
        st.markdown(f"### 📁 {item['folder']}")
        st.markdown(f"**Score:** `{item['score']:.4f}`")
        st.markdown("---")
        st.markdown(item['content'][:1500] + ("..." if len(item['content']) > 1500 else ""), unsafe_allow_html=True)

        # Feedback options
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"👍 Helpful #{i}"):
                feedback_map[item['folder']] = "helpful"
                st.success("Marked as helpful ✅")
        with col2:
            if st.button(f"👎 Not Helpful #{i}"):
                feedback_map[item['folder']] = "not helpful"
                st.warning("Marked as not helpful ❌")

        st.markdown("---")
