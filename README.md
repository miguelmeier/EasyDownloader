# 🚀 EasyDownloader – MEGA & Dropbox Downloader

A powerful **local web-based downloader** for MEGA and Dropbox with **proxy rotation, parallel downloads, and bandwidth bypass**.

> ⚡ Fully local – no external servers, no data tracking

---

## 🎥 Demo

https://streamable.com/z2fdya

---

## ⭐ Why EasyDownloader?

- 🚀 Bypass MEGA bandwidth limits using proxy rotation
- 📦 Download files & folders (MEGA + Dropbox)
- 🔁 Automatic proxy switching on failure
- 🌐 Clean, modern web interface
- ⚡ Parallel downloads for maximum speed
- 🔐 100% local processing (no third-party APIs)

---

## ✨ Features

### 📦 Supported Services
- MEGA.nz (files & folders)
- Dropbox (files & folders)

---

### ⚙️ Download Modes
- Single File
- Single Folder
- Multi-Folder (bulk download)
- Mixed Mode (files + folders together)

---

### 🔁 Smart Proxy System
- Drag & Drop Proxy Builder (supports custom formats)
- Automatic proxy validation (removes dead proxies)
- Auto-rotation when limits are hit
- Manual proxy input via UI

---

### 🌐 Web Interface
- Modern dark-mode UI
- Live download log
- Responsive design

---

### 🔐 Privacy
- Local MEGA decryption
- No external services involved

---

## 🛠️ How it works

- Parses MEGA/Dropbox links
- Splits downloads into chunks
- Uses proxies to distribute traffic
- Reassembles files locally

---

## 📥 Installation

### 🖥️ Option 1 – Windows (.exe)

1. Go to the **Releases** section
2. Download the latest `.exe`
3. Run the application

➡ Opens automatically at:
http://127.0.0.1:5000

---

### 🐍 Option 2 – Python

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
python app.py
```
On first launch:
- Creates a virtual environment (.venv)
- Installs all dependencies automatically

---

### 📋 Requirements
- Python 3.10+
- Windows / Linux

---

### ⚙️ Proxy Setup
Create a file named:
``proxies.txt``

Example format:
``IP:PORT:USERNAME:PASSWORD``

Use the Drag & Drop Builder in the UI to match your proxy format.

---

### 🧠 Use Cases
- Bypass MEGA bandwidth limits
- Bulk download cloud storage files
- Automate downloads using proxy lists
- High-speed parallel downloading

---

### 🆚 Comparison
Feature	            EasyDownloader	Typical Downloaders
Proxy Rotation	    ✅	            ❌
Web Interface	      ✅            	❌
Multi-Link Support	✅	            ⚠️
Local Decryption	  ✅	            ❌

---

### ⚠️ Disclaimer
This tool is intended for educational purposes only.
Users are responsible for complying with the terms of service of MEGA and Dropbox.

--- 

### 🛡️ License
MIT License – see LICENSE file.

---

### ⭐ Support
If you like this project, consider giving it a star ⭐
