<div align="center">
  <h1>🚀 EasyDownloader</h1>
  <p><b>A powerful, local web-based downloader for MEGA and Dropbox with proxy rotation, parallel downloads, and bandwidth limit bypass.</b></p>
  
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg" alt="Platform">
</div>

> ⚡ **Fully local processing** – no external servers, no data tracking, 100% privacy.

## 🎥 Demo
<div style="position:relative; width:100%; height:0px; padding-bottom:56.250%"><iframe allow="fullscreen" allowfullscreen height="100%" src="https://streamable.com/e/z2fdya?" width="100%" style="border:none; width:100%; height:100%; position:absolute; left:0px; top:0px; overflow:hidden;"></iframe></div>


## ⭐ Why EasyDownloader?
Tired of hitting the MEGA bandwidth quota? **EasyDownloader** solves this by routing your downloads through rotating proxies, allowing for seamless, uninterrupted file retrieval. Wrapped in a beautiful, responsive, dark-mode web UI, it makes managing bulk downloads from MEGA and Dropbox easier than ever.

## ✨ Key Features
* **🚀 Quota Bypass:** Circumvent MEGA bandwidth limits using smart proxy rotation.
* **📦 Broad Support:** Download individual files, single folders, or bulk multi-folders from both MEGA.nz and Dropbox.
* **🔁 Smart Proxy System:** Automatically validates proxies, removes dead ones, and rotates upon failure. Features a unique **Drag & Drop Proxy Builder** for custom configurations!
* **⚡ High-Speed:** Parallel downloads utilizing multiple threads and proxies simultaneously.
* **🤖 Zero-Config Auto-Setup:** Just run the script! It automatically creates a Python virtual environment (`.venv`) and installs all necessary dependencies.
* **🌐 Modern UI:** Clean web interface with Dark Mode, bilingual support (English/German), and a real-time download log.

## 🛠️ How It Works
1. Parses MEGA/Dropbox links securely.
2. Splits downloads into chunks for efficiency.
3. Distributes traffic across your proxy list.
4. Decrypts (MEGA) and reassembles files entirely locally.

## 📥 Installation & Usage

### 🖥️ Option 1: Windows Executable (.exe) - *Easiest*
1. Go to the **[Releases](../../releases)** section.
2. Download the latest `.exe` file.
3. Run the application. 
4. The web interface will automatically open in your browser at `http://127.0.0.1:5000`.

### 🐍 Option 2: Run via Python
Make sure you have Python 3.10 or higher installed.

```bash
git clone https://github.com/miguelmeier/easy-downloader-mega-dropbox.git
cd easy-downloader-mega-dropbox
python app.py
```

**Magic Auto-Setup:** On the very first launch, `app.py` will automatically create a virtual environment and install required packages (`Flask`, `requests`, `pycryptodome`, `mega.py`). No manual `pip install` required!

## ⚙️ Proxy Configuration
To bypass download limits, you can add proxies manually via the Web UI, or simply create a `proxies.txt` file in the root directory.

**Example `proxies.txt` format:**
```text
192.168.1.1:8080:username:password
10.0.0.1:3128
```
*Tip: Use the Drag & Drop Proxy Builder in the web interface to match your exact text file format (e.g., choosing the correct delimiter or order of IP/Port/User).*

## 🆚 Feature Comparison

| Feature | EasyDownloader | Typical Downloaders |
| :--- | :---: | :---: |
| **Proxy Rotation & Limit Bypass** | ✅ | ❌ |
| **Modern Web Interface** | ✅ | ❌ |
| **Bulk Multi-Link Support** | ✅ | ⚠️ |
| **Local Auto-Decryption** | ✅ | ❌ |
| **Zero-Config Auto-Setup** | ✅ | ❌ |

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](../../issues). 

## ⚠️ Disclaimer
This tool is intended for educational purposes only. Users are solely responsible for complying with the Terms of Service of MEGA and Dropbox. 

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
**If you find this tool helpful, please consider giving it a ⭐! It helps the project grow.**
