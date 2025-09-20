# 📸 Instagram Posts Downloader

A **Python-based application** to download Instagram posts from public or private accounts (with login).  
This tool is powered by [`instaloader`](https://instaloader.github.io/) and includes a **time delay** mechanism to reduce the chance of being detected as a bot by Instagram.

---

## ✨ Features
- Login to Instagram with username & password.
- Download all posts from any target account.
- Works with both public and private accounts (if you follow them).
- Automatically saves posts into a folder based on the target username.
- Built-in time delay to lower the risk of being blocked.
- Can run smoothly from terminal or **VS Code Debug**.

---

## 🛠️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/username/instagram-posts-downloader.git
   cd instagram-posts-downloader

## Create a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

## Install dependencies:
pip install -r requirements.txt

## Usage
Run the application:
python insta_posts_downloader.py

Enter your Instagram username & password.
Once logged in, input the target username.
For private accounts, make sure you already follow them.

Downloaded posts will be saved in:
./downloaded_posts/<target_username>/

⚠️ Important Notes

It’s recommended to use a secondary Instagram account to avoid potential blocks.
Even with time delay, avoid excessive logins or scraping.
This project is intended for learning & personal use only.
Do not use it in violation of Instagram’s policies.

---------- PapaBear 2025 ------------------------
