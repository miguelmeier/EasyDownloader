# MEGA & Dropbox Downloader v1

A powerful, local web service for automated and parallel downloading of files and folders from MEGA and Dropbox. The tool offers a modern web interface, supports extensive proxy management, and reliably bypasses bandwidth limits.

## 🚀 Features

- Multi-Service Support: Supports downloading from MEGA.nz (files & folders) and Dropbox (files & folders).

- Various Download Modes:

- Single File

- Single Folder

- Multi-Folder (Multiple links simultaneously)

- Mixed (Mix files and folders in one list)

- Smart Proxy Management:

- Drag & Drop Template-Builder: Configure the format of your proxies.txt dynamically using Drag & Drop!

- Manual Proxy Boxes: Quickly add proxies directly within the user interface.

- Proxy Validation: Automatically filters out dead proxies before the download starts (tests directly against MEGA/Dropbox servers).

- Auto-Rotation: Seamlessly switches to the next proxy on failure (e.g., when hitting a bandwidth limit).

- Modern Web Interface: Dark-Mode UI, Responsive Design, and a live download log directly in your browser.

- Local Decryption: MEGA files are decrypted locally on your machine without relying on third-party servers.

## 📥 Installation & Usage

- Option 1: Standalone .exe (Windows)

> Navigate to the Releases section on the GitHub page.

> Download the latest .exe file.

> Run the application. The tool will automatically open in your default browser at http://127.0.0.1:5000

- Option 2: Python Source Code

> Ensure you have Python 3 installed.

> Clone or download this repository.

> Run the script:

> ```python app.py```

**On its first launch, the script will automatically create a virtual environment (.venv) and install all required dependencies.**


## ⚙️ Proxy Setup

If you choose the automatic proxy mode ("Auto"), place a file named proxies.txt in the same folder as the executable/script.

Thanks to the built-in Drag & Drop Builder, you can use almost any format! For example, if your proxy file looks like this:
198.23.239.134:6540:user:pass
... simply drag and drop the boxes in the UI into the order IP, Port, Username, Password and set the delimiter to :.

## 🛡️ License

**This project is licensed under the MIT License. See the LICENSE file for more details.**
