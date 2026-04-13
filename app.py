import sys
import os


def _ensure_venv():
    if getattr(sys, "frozen", False):
        return  # already bundled as exe

    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir   = os.path.join(script_dir, ".venv")

    if sys.prefix != sys.base_prefix:
        return

    if os.name == "nt":
        py  = os.path.join(venv_dir, "Scripts", "python.exe")
        pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        py  = os.path.join(venv_dir, "bin", "python3")
        pip = os.path.join(venv_dir, "bin", "pip")

    import subprocess

    if not os.path.isfile(py):
        print("[setup] No .venv found – creating one ...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        print("[setup] Installing packages (this takes a moment) ...")
        subprocess.check_call(
            [pip, "install", "-q", "--upgrade", "pip"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        packages = ["flask", "requests", "pycryptodome", "mega.py"]
        subprocess.check_call([pip, "install", "-q"] + packages)
        print("[setup] All done – restarting inside venv ...\n")
    else:
        print("[setup] Using existing .venv\n")

    os.execv(py, [py] + sys.argv)

_ensure_venv()

import webbrowser
import re
import json
import base64
import struct
import queue
import threading
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string, request, Response
from Crypto.Cipher import AES
from Crypto.Util import Counter
from mega import Mega

app = Flask(__name__)

def _print_banner():
    lines = [
        "",
        "  ┌──────────────────────────────┐",
        "  │  MEGA & Dropbox Downloader   │",
        "  ├──────────────────────────────┤",
        "  │  http://127.0.0.1:5000       │",
        "  │  Press Ctrl+C to quit        │",
        "  └──────────────────────────────┘",
        "",
    ]
    for l in lines:
        print(l)

HTML_INDEX = r'''<!DOCTYPE html>
<html lang="de" data-lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEGA & Dropbox Downloader</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:           #0d1117;
  --surface:      #161b22;
  --surface-2:    #21262d;
  --border:       #30363d;
  --border-focus: #58a6ff;
  --text:         #e6edf3;
  --muted:        #7d8590;
  --accent:       #1f6feb;
  --accent-h:     #388bfd;
  --accent-db:    #0061FE;
  --accent-db-h:  #0050d1;
  --green:        #3fb950;
  --orange:       #e3b341;
  --red:          #f85149;
  --r:            5px;
  --f:            'Figtree', sans-serif;
  --mono:         'JetBrains Mono', monospace;
}

html { font-size: 14px; }

body {
  font-family: var(--f);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.5;
}

.wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 20px 80px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.app-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}
.app-title span {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 400;
  color: var(--muted);
  margin-left: 8px;
}

.lang-sw {
  display: flex;
  align-items: center;
  gap: 4px;
}
.lang-btn {
  background: none;
  border: 1px solid transparent;
  border-radius: var(--r);
  padding: 3px 8px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  transition: color .12s, border-color .12s;
  letter-spacing: .05em;
}
.lang-btn:hover { color: var(--text); border-color: var(--border); }
.lang-btn.active { color: var(--text); border-color: var(--border); background: var(--surface-2); }
.lang-sep { color: var(--border); font-size: 13px; }

section {
  margin-bottom: 28px;
}
.sec-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
  margin-bottom: 12px;
}

/* Service Tabs (Mega / Dropbox) */
.service-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.srv-btn {
  flex: 1;
  padding: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  color: var(--muted);
  font-family: var(--f);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all .15s;
}
.srv-btn:hover { background: var(--surface-2); color: var(--text); }
.srv-btn.active[data-srv="mega"] { background: rgba(229, 9, 20, 0.1); border-color: #e50914; color: #fff; }
.srv-btn.active[data-srv="dropbox"] { background: rgba(0, 97, 254, 0.1); border-color: var(--accent-db); color: #fff; }

.mode-tabs {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--r);
  overflow: hidden;
  margin-bottom: 14px;
}
.mode-tab {
  flex: 1;
  padding: 8px 10px;
  background: var(--surface);
  border: none;
  border-right: 1px solid var(--border);
  color: var(--muted);
  font-family: var(--f);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background .12s, color .12s;
  text-align: center;
}
.mode-tab:last-child { border-right: none; }
.mode-tab:hover { background: var(--surface-2); color: var(--text); }
.mode-tab.active { background: var(--surface-2); color: var(--text); }

.field { margin-bottom: 12px; }
.field label {
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 5px;
  font-weight: 500;
}
.field input,
.field select {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 8px 11px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 12.5px;
  outline: none;
  transition: border-color .12s;
}
.field input:focus,
.field select:focus { border-color: var(--border-focus); }
.field input::placeholder { color: var(--muted); opacity: .7; }
.field select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='5'%3E%3Cpath fill='%237d8590' d='M0 0l5 5 5-5z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 11px center;
  padding-right: 28px;
  font-family: var(--f);
}
.field select option { background: #161b22; font-family: var(--f); }

.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.path-row { display: flex; gap: 8px; }
.path-row input { flex: 1; }
.browse-btn {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 8px 14px;
  color: var(--text);
  font-family: var(--f);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background .12s, border-color .12s;
}
.browse-btn:hover { background: var(--border); }

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.toggle-row:first-of-type { border-top: 1px solid var(--border); }
.toggle-info .tname { font-size: 13.5px; font-weight: 500; color: var(--text); }
.toggle-info .tdesc { font-size: 11.5px; color: var(--muted); margin-top: 1px; }

.sw { position: relative; width: 36px; height: 20px; flex-shrink: 0; }
.sw input { opacity: 0; width: 0; height: 0; }
.sw-track {
  position: absolute; inset: 0;
  border-radius: 20px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background .15s, border-color .15s;
}
.sw-track::before {
  content: '';
  position: absolute;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--muted);
  top: 3px; left: 3px;
  transition: transform .15s, background .15s;
}
.sw input:checked + .sw-track { background: rgba(31,111,235,.2); border-color: var(--accent); }
.sw input:checked + .sw-track::before { background: var(--accent); transform: translateX(16px); }

.url-list { display: flex; flex-direction: column; gap: 7px; }
.url-row { display: flex; gap: 7px; }
.url-row input { flex: 1; }
.url-del, .proxy-del {
  width: 30px; height: 30px;
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--r);
  color: var(--muted);
  cursor: pointer;
  font-size: 17px;
  line-height: 1;
  transition: color .12s, border-color .12s;
  flex-shrink: 0;
  align-self: center;
}
.url-del:hover, .proxy-del:hover { color: var(--red); border-color: var(--red); }
.add-btn {
  margin-top: 7px;
  width: 100%;
  padding: 7px;
  background: none;
  border: 1px dashed var(--border);
  border-radius: var(--r);
  color: var(--muted);
  font-family: var(--f);
  font-size: 12.5px;
  cursor: pointer;
  transition: color .12s, border-color .12s;
}
.add-btn:hover { color: var(--text); border-color: var(--muted); }


#autoProxyBox { margin-top: 12px; }
.proxy-avail, .proxy-dropzone {
    display: flex;
    gap: 8px;
    min-height: 45px;
    padding: 10px;
    background: var(--surface-2);
    border: 1px dashed var(--border);
    border-radius: var(--r);
    align-items: center;
    flex-wrap: wrap;
    transition: background 0.2s;
}
.proxy-dropzone {
    border-color: var(--accent);
    background: rgba(31, 111, 235, 0.05);
}
.proxy-block {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 12px;
    font-size: 12px;
    cursor: grab;
    user-select: none;
    color: var(--text);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: opacity 0.2s, transform 0.2s;
}
.proxy-block:active { cursor: grabbing; }
.proxy-block.dragging { opacity: 0.5; transform: scale(0.95); }



#manualProxyBox { margin-top: 12px; }
.proxy-boxes { display: flex; flex-direction: column; gap: 8px; }
.proxy-row {
  display: grid;
  grid-template-columns: 85px 2fr 80px 1.5fr 1.5fr 30px;
  gap: 6px;
  background: var(--surface-2);
  padding: 6px;
  border-radius: var(--r);
  border: 1px solid var(--border);
}
.proxy-row input, .proxy-row select {
    padding: 6px 8px;
    font-size: 11.5px;
}
.proxy-header {
  display: grid;
  grid-template-columns: 85px 2fr 80px 1.5fr 1.5fr 30px;
  gap: 6px;
  padding: 0 6px;
  margin-bottom: 4px;
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  font-weight: 600;
}

.submit-wrap { margin-top: 32px; }
.submit-btn {
  width: 100%;
  padding: 12px;
  background: var(--accent);
  border: none;
  border-radius: var(--r);
  color: #fff;
  font-family: var(--f);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: .02em;
  transition: background .12s;
}
.submit-btn:hover { background: var(--accent-h); }
.submit-btn:active { opacity: .9; }

@media (max-width: 650px) {
  .row-2 { grid-template-columns: 1fr; }
  .mode-tabs { flex-direction: column; }
  .mode-tab { border-right: none; border-bottom: 1px solid var(--border); }
  .mode-tab:last-child { border-bottom: none; }
  .proxy-row, .proxy-header {
      display: flex; flex-direction: column; gap: 4px; padding: 10px;
  }
  .proxy-header { display: none; }
  .proxy-del { width: 100%; margin-top: 4px; border-color: var(--red); color: var(--red); }
}

</style>
</head>
<body>
<div class="wrap">

  <div class="app-header">
    <div class="app-title">
      MEGA & Dropbox <span>Downloader v1</span>
    </div>
    <div class="lang-sw">
      <button class="lang-btn active" id="btn-de" onclick="setLang('de')">DE</button>
      <span class="lang-sep">/</span>
      <button class="lang-btn" id="btn-en" onclick="setLang('en')">EN</button>
    </div>
  </div>

  <form method="POST" action="/download" id="dlForm">


    <input type="hidden" name="service" id="serviceInput" value="mega">
    <div class="service-tabs">
      <button type="button" class="srv-btn active" data-srv="mega" onclick="setService('mega')">MEGA</button>
      <button type="button" class="srv-btn" data-srv="dropbox" onclick="setService('dropbox')">Dropbox</button>
    </div>


    <section>
      <div class="sec-title" data-i18n="src_title">Quelle</div>

      <div class="mode-tabs">
        <button type="button" class="mode-tab active" onclick="setMode('single_file')"   id="tab_single_file"   data-i18n="mode_file">Datei</button>
        <button type="button" class="mode-tab"        onclick="setMode('single_folder')" id="tab_single_folder" data-i18n="mode_folder">Ordner</button>
        <button type="button" class="mode-tab"        onclick="setMode('multi_folder')"  id="tab_multi_folder"  data-i18n="mode_multi">Multi-Ordner</button>
        <button type="button" class="mode-tab"        onclick="setMode('mixed')"         id="tab_mixed"         data-i18n="mode_mixed">Gemischt</button>
      </div>

      <input type="hidden" name="mode" id="modeInput" value="single_file">


      <div id="panel_single_file">
        <div class="field">
          <label data-i18n="lbl_url">URL</label>
          <input type="text" name="url_single" data-dyn-ph="ph_file" placeholder="https://mega.nz/file/XXXXXXXX#YYYYYYYY">
        </div>
      </div>


      <div id="panel_single_folder" style="display:none">
        <div class="field">
          <label data-i18n="lbl_folder_url">Ordner-URL</label>
          <input type="text" name="url_folder" data-dyn-ph="ph_folder" placeholder="https://mega.nz/folder/XXXXXXXX#YYYYYYYY">
        </div>
      </div>


      <div id="panel_multi_folder" style="display:none">
        <div class="field">
          <label data-i18n="lbl_folder_urls">Ordner-URLs</label>
          <div class="url-list" id="multiFolderList">
            <div class="url-row">
              <input type="text" name="urls_multi[]" data-dyn-ph="ph_folder" placeholder="https://mega.nz/folder/...">
              <button type="button" class="url-del" onclick="delRow(this)">×</button>
            </div>
          </div>
          <button type="button" class="add-btn" onclick="addRow('multiFolderList','urls_multi[]','ph_folder')" data-i18n="btn_add_folder">+ Ordner hinzufügen</button>
        </div>
      </div>


      <div id="panel_mixed" style="display:none">
        <div class="field">
          <label data-i18n="lbl_mixed_urls">URLs (Dateien &amp; Ordner)</label>
          <div class="url-list" id="mixedList">
            <div class="url-row">
              <input type="text" name="urls_mixed[]" data-dyn-ph="ph_mixed" placeholder="https://mega.nz/file/... oder /folder/...">
              <button type="button" class="url-del" onclick="delRow(this)">×</button>
            </div>
          </div>
          <button type="button" class="add-btn" onclick="addRow('mixedList','urls_mixed[]','ph_mixed')" data-i18n="btn_add_url">+ URL hinzufügen</button>
        </div>
      </div>
    </section>


    <section>
      <div class="sec-title" data-i18n="dst_title">Zielordner</div>
      <div class="field">
        <label data-i18n="lbl_path">Speicherpfad</label>
        <div class="path-row">
          <input type="text" name="output_path" id="outputPath"
            value="{{ default_path }}" data-i18n-ph="ph_path" placeholder="/pfad/zum/ordner">
          <button type="button" class="browse-btn" onclick="browseFolder()" data-i18n="btn_browse">Durchsuchen …</button>
        </div>
      </div>
    </section>


    <section>
      <div class="sec-title" data-i18n="proxy_title">Proxy</div>

      <div class="row-2">
        <div class="field">
          <label data-i18n="lbl_proxy_mode">Proxy-Modus</label>
          <select name="proxy_mode" onchange="updateProxyUI(this.value)">
            <option value="auto"   data-i18n="pm_auto">Auto (proxies.txt)</option>
            <option value="manual" data-i18n="pm_manual">Manuell (Kästchen)</option>
            <option value="none"   data-i18n="pm_none">Kein Proxy</option>
          </select>
        </div>
        <div class="field">
          <label data-i18n="lbl_timeout">Timeout (s)</label>
          <input type="number" name="timeout" value="20" min="5" max="120">
        </div>
      </div>


      <div id="autoProxyBox" style="display:block">
        <div class="field">
          <label data-i18n="lbl_auto_template">Format für proxies.txt (Kästchen reinziehen)</label>
          
          <div style="font-size:11px; color:var(--muted); margin-bottom: 6px;">Verfügbare Blöcke:</div>
          <div class="proxy-avail" id="availZone">
              <div class="proxy-block" draggable="true" data-val="proto">Protokoll</div>
          </div>
          
          <div style="font-size:11px; color:var(--muted); margin-bottom: 6px; margin-top: 12px;">Aktuelles Format (Reihenfolge ändern möglich):</div>
          <div class="proxy-dropzone" id="templateDropzone">
              <div class="proxy-block" draggable="true" data-val="ip">IP / Host</div>
              <div class="proxy-block" draggable="true" data-val="port">Port</div>
              <div class="proxy-block" draggable="true" data-val="user">Username</div>
              <div class="proxy-block" draggable="true" data-val="pass">Passwort</div>
          </div>
          
          <div style="margin-top:12px; display:flex; align-items:center; gap:8px;">
              <label style="margin:0; font-size:12px;" data-i18n="lbl_delim">Trennzeichen (Delimiter):</label>
              <input type="text" name="auto_proxy_delim" value=":" style="width: 50px; padding: 6px; text-align:center;">
          </div>
          <!-- Hidden input to store the final template string -->
          <input type="hidden" name="auto_proxy_template" id="autoProxyTemplate" value="ip,port,user,pass">
        </div>
      </div>


      <div id="manualProxyBox" style="display:none">
        <div class="field">
          <label data-i18n="lbl_manual_proxy">Manuelle Proxies</label>
          <div class="proxy-header">
              <span>Protokoll</span><span>IP / Hostname</span><span>Port</span><span>Benutzer (opt)</span><span>Passwort (opt)</span><span></span>
          </div>
          <div class="proxy-boxes" id="proxyBoxList">
            <!-- First Row Default -->
            <div class="proxy-row">
                <select name="prox_proto[]"><option value="http">HTTP</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option></select>
                <input type="text" name="prox_host[]" placeholder="127.0.0.1">
                <input type="number" name="prox_port[]" placeholder="8080">
                <input type="text" name="prox_user[]" placeholder="user">
                <input type="password" name="prox_pass[]" placeholder="pass">
                <button type="button" class="proxy-del" onclick="delProxyRow(this)">×</button>
            </div>
          </div>
          <button type="button" class="add-btn" onclick="addProxyRow()" data-i18n="btn_add_proxy">+ Proxy hinzufügen</button>
        </div>
      </div>

      <div class="toggle-row">
        <div class="toggle-info">
          <div class="tname" data-i18n="tog_validate">Proxy-Validierung</div>
          <div class="tdesc" data-i18n="tog_validate_d">Inaktive Proxies vorher aussortieren</div>
        </div>
        <label class="sw">
          <input type="checkbox" name="validate_proxies" value="1" checked>
          <span class="sw-track"></span>
        </label>
      </div>
      <div class="toggle-row">
        <div class="toggle-info">
          <div class="tname" data-i18n="tog_rotate">Rotation bei Fehler</div>
          <div class="tdesc" data-i18n="tog_rotate_d">Automatisch auf nächsten Proxy wechseln</div>
        </div>
        <label class="sw">
          <input type="checkbox" name="proxy_rotate" value="1" checked>
          <span class="sw-track"></span>
        </label>
      </div>
    </section>

    <div class="submit-wrap">
      <button type="submit" id="submitBtn" class="submit-btn" data-i18n="btn_start">Download starten</button>
    </div>

  </form>
</div>

<script>

const T = {
  de: {
    src_title:      'Quelle',
    mode_file:      'Datei',
    mode_folder:    'Ordner',
    mode_multi:     'Multi-Ordner',
    mode_mixed:     'Gemischt',
    lbl_url:        'URL',
    lbl_folder_url: 'Ordner-URL',
    lbl_folder_urls:'Ordner-URLs',
    lbl_mixed_urls: 'URLs (Dateien & Ordner)',
    btn_add_folder: '+ Ordner hinzufügen',
    btn_add_url:    '+ URL hinzufügen',
    btn_add_proxy:  '+ Proxy Kästchen hinzufügen',
    ph_file_mega:   'https://mega.nz/file/XXXXXXXX#YYYYYYYY',
    ph_folder_mega: 'https://mega.nz/folder/XXXXXXXX#YYYYYYYY',
    ph_mixed_mega:  'https://mega.nz/file/... oder /folder/...',
    ph_file_dp:     'https://www.dropbox.com/s/XXXXXXXX/file.ext?dl=0',
    ph_folder_dp:   'https://www.dropbox.com/sh/XXXXXXXX/YYYYYYYY?dl=0',
    ph_mixed_dp:    'Dropbox Links (Datei oder Ordner)',
    dst_title:      'Zielordner',
    lbl_path:       'Speicherpfad',
    btn_browse:     'Durchsuchen …',
    ph_path:        '/pfad/zum/ordner',
    proxy_title:    'Proxy',
    lbl_proxy_mode: 'Proxy-Modus',
    pm_auto:        'Auto (proxies.txt)',
    pm_manual:      'Manuell (Kästchen)',
    pm_none:        'Kein Proxy',
    lbl_manual_proxy:'Manuelle Proxies',
    lbl_auto_template:'Format für proxies.txt (Kästchen reinziehen)',
    lbl_delim:      'Trennzeichen (Delimiter):',
    lbl_timeout:    'Timeout (s)',
    tog_validate:   'Proxy-Validierung',
    tog_validate_d: 'Inaktive Proxies vorher aussortieren',
    tog_rotate:     'Rotation bei Fehler',
    tog_rotate_d:   'Automatisch auf nächsten Proxy wechseln',
    btn_start:      'Download starten',
  },
  en: {
    src_title:      'Source',
    mode_file:      'File',
    mode_folder:    'Folder',
    mode_multi:     'Multi-Folder',
    mode_mixed:     'Mixed',
    lbl_url:        'URL',
    lbl_folder_url: 'Folder URL',
    lbl_folder_urls:'Folder URLs',
    lbl_mixed_urls: 'URLs (files & folders)',
    btn_add_folder: '+ Add folder',
    btn_add_url:    '+ Add URL',
    btn_add_proxy:  '+ Add Proxy box',
    ph_file_mega:   'https://mega.nz/file/XXXXXXXX#YYYYYYYY',
    ph_folder_mega: 'https://mega.nz/folder/XXXXXXXX#YYYYYYYY',
    ph_mixed_mega:  'https://mega.nz/file/... or /folder/...',
    ph_file_dp:     'https://www.dropbox.com/s/XXXXXXXX/file.ext?dl=0',
    ph_folder_dp:   'https://www.dropbox.com/sh/XXXXXXXX/YYYYYYYY?dl=0',
    ph_mixed_dp:    'Dropbox Links (File or Folder)',
    dst_title:      'Destination',
    lbl_path:       'Save path',
    btn_browse:     'Browse …',
    ph_path:        '/path/to/folder',
    proxy_title:    'Proxy',
    lbl_proxy_mode: 'Proxy mode',
    pm_auto:        'Auto (proxies.txt)',
    pm_manual:      'Manual (Boxes)',
    pm_none:        'No proxy',
    lbl_manual_proxy:'Manual Proxies',
    lbl_auto_template:'Format for proxies.txt (Drag & Drop)',
    lbl_delim:      'Separator (Delimiter):',
    lbl_timeout:    'Timeout (s)',
    tog_validate:   'Proxy validation',
    tog_validate_d: 'Filter out dead proxies before downloading',
    tog_rotate:     'Rotate on error',
    tog_rotate_d:   'Automatically switch to the next proxy on failure',
    btn_start:      'Start download',
  }
};

let _lang = localStorage.getItem('dl_lang') || 'de';
let _srv = 'mega';

function setLang(l) {
  _lang = l;
  localStorage.setItem('dl_lang', l);
  document.documentElement.lang = l;
  document.getElementById('btn-de').classList.toggle('active', l === 'de');
  document.getElementById('btn-en').classList.toggle('active', l === 'en');

  const dict = T[l];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.dataset.i18n;
    if (dict[k] !== undefined) {
      if (el.tagName === 'OPTION') el.textContent = dict[k];
      else el.textContent = dict[k];
    }
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const k = el.dataset.i18nPh;
    if (dict[k] !== undefined) el.placeholder = dict[k];
  });
  updateDynPlaceholders();
}

function updateDynPlaceholders() {
    const dict = T[_lang];
    const srvKey = _srv === 'mega' ? '_mega' : '_dp';
    document.querySelectorAll('[data-dyn-ph]').forEach(inp => {
        const baseKey = inp.dataset.dynPh;
        const fullKey = baseKey + srvKey;
        if (dict[fullKey]) inp.placeholder = dict[fullKey];
    });
}

function setService(s) {
    _srv = s;
    document.getElementById('serviceInput').value = s;
    document.querySelectorAll('.srv-btn').forEach(b => b.classList.toggle('active', b.dataset.srv === s));
    
    // Change button color
    const btn = document.getElementById('submitBtn');
    if(s === 'dropbox') {
        btn.style.background = 'var(--accent-db)';
    } else {
        btn.style.background = 'var(--accent)';
    }
    updateDynPlaceholders();
}


const MODES = ['single_file','single_folder','multi_folder','mixed'];
function setMode(m) {
  MODES.forEach(id => {
    document.getElementById('panel_' + id).style.display = id === m ? 'block' : 'none';
    document.getElementById('tab_' + id).classList.toggle('active', id === m);
  });
  document.getElementById('modeInput').value = m;
}


function addRow(listId, name, phBase) {
  const div = document.createElement('div');
  div.className = 'url-row';
  div.innerHTML = `<input type="text" name="${name}" data-dyn-ph="${phBase}"><button type="button" class="url-del" onclick="delRow(this)">×</button>`;
  document.getElementById(listId).appendChild(div);
  updateDynPlaceholders();
  div.querySelector('input').focus();
}
function delRow(btn) {
  const list = btn.closest('.url-list');
  if (list.children.length > 1) btn.closest('.url-row').remove();
}


function updateProxyUI(v) {
  document.getElementById('manualProxyBox').style.display = v === 'manual' ? 'block' : 'none';
  document.getElementById('autoProxyBox').style.display = v === 'auto' ? 'block' : 'none';
}
function addProxyRow() {
    const div = document.createElement('div');
    div.className = 'proxy-row';
    div.innerHTML = `
        <select name="prox_proto[]"><option value="http">HTTP</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option></select>
        <input type="text" name="prox_host[]" placeholder="IP / Hostname">
        <input type="number" name="prox_port[]" placeholder="Port">
        <input type="text" name="prox_user[]" placeholder="User (opt)">
        <input type="password" name="prox_pass[]" placeholder="Pass (opt)">
        <button type="button" class="proxy-del" onclick="delProxyRow(this)">×</button>
    `;
    document.getElementById('proxyBoxList').appendChild(div);
}
function delProxyRow(btn) {
    const list = document.getElementById('proxyBoxList');
    if (list.children.length > 1) btn.closest('.proxy-row').remove();
}


function initDragAndDrop() {
    let draggedEl = null;

    document.querySelectorAll('.proxy-block').forEach(el => {
        el.addEventListener('dragstart', (e) => {
            draggedEl = el;
            setTimeout(() => el.classList.add('dragging'), 0);
        });
        el.addEventListener('dragend', () => {
            draggedEl.classList.remove('dragging');
            draggedEl = null;
            updateAutoProxyTemplate();
        });
    });

    document.querySelectorAll('.proxy-avail, .proxy-dropzone').forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(zone, e.clientX);
            const draggable = document.querySelector('.dragging');
            if (draggable) {
                if (afterElement == null) {
                    zone.appendChild(draggable);
                } else {
                    zone.insertBefore(draggable, afterElement);
                }
            }
        });
    });

    function getDragAfterElement(container, x) {
        const draggableElements = [...container.querySelectorAll('.proxy-block:not(.dragging)')];
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = x - box.left - box.width / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
}

function updateAutoProxyTemplate() {
    const dropzone = document.getElementById('templateDropzone');
    const vals = Array.from(dropzone.children).map(el => el.dataset.val);
    document.getElementById('autoProxyTemplate').value = vals.join(',');
}


async function browseFolder() {
  try {
    const res  = await fetch('/browse');
    const data = await res.json();
    if (data.path) document.getElementById('outputPath').value = data.path;
  } catch(e) {
    console.warn('browse failed', e);
  }
}


document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter')
    document.getElementById('dlForm').submit();
});


setLang(_lang);
initDragAndDrop();
updateProxyUI(document.querySelector('select[name="proxy_mode"]').value);
</script>
</body>
</html>
'''



#  MEGA BASE64 / INT HELPERS
def _b64decode(s):
    if isinstance(s, bytes): s = s.decode('ascii')
    s = s.strip().rstrip('=')
    pad = (4 - len(s) % 4) % 4
    s = s + '=' * pad
    s = s.replace('-', '+').replace('_', '/')
    return base64.b64decode(s)

def _str_to_a32(b):
    if isinstance(b, str): b = b.encode('latin-1')
    if len(b) % 4: b += b'\x00' * (4 - len(b) % 4)
    return struct.unpack(f'>{len(b)//4}I', b)

def _a32_to_str(a):
    return struct.pack(f'>{len(a)}I', *a)

def _b64_to_a32(s):
    return _str_to_a32(_b64decode(s))



#  MEGA KEY DECRYPTION
def _xor_blocks(enc, master):
    ml = len(master)
    return tuple(enc[i] ^ master[i % ml] for i in range(len(enc)))

def _get_node_aes_key_and_iv(k):
    if len(k) >= 8:
        aes_key = (k[0]^k[4], k[1]^k[5], k[2]^k[6], k[3]^k[7])
        iv      = (k[4], k[5], 0, 0)
    else:
        aes_key = tuple(k[:4])
        iv      = (0, 0, 0, 0)
    return aes_key, iv



#  MEGA ATTRIBUTE DECRYPTION
def _decrypt_attr(attr_b64, aes_key_tuple):
    try:
        raw = _b64decode(attr_b64)
        if len(raw) % 16: raw += b'\x00' * (16 - len(raw) % 16)
        key_bytes = _a32_to_str(aes_key_tuple[:4])
        cipher    = AES.new(key_bytes, AES.MODE_CBC, iv=b'\x00' * 16)
        dec       = cipher.decrypt(raw)
        m = re.search(rb'MEGA(\{.+?\})', dec, re.DOTALL)
        if m: return json.loads(m.group(1).decode('utf-8', errors='replace'))
        m = re.search(rb'\{[^{}]{2,}\}', dec)
        if m:
            try: return json.loads(m.group(0).decode('utf-8', errors='replace'))
            except Exception: pass
        return {}
    except Exception:
        return {}



#  MEGA API
def _api_call(payload, node_id=None, proxy=None, timeout=20):
    import random
    seq  = random.randint(0, 10**9)
    url  = f'https://g.api.mega.co.nz/cs?id={seq}'
    if node_id: url += f'&n={node_id}'
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    resp    = requests.post(url, data=json.dumps([payload]),
                            proxies=proxies, timeout=timeout)
    result  = resp.json()
    return result[0] if isinstance(result, list) else result



#  MEGA FOLDER PARSING
def parse_folder_url(url):
    m = re.search(r'/folder/([^#\s/]+)#([^\s&/]+)', url)
    if not m: raise ValueError(f'Not a valid folder link: {url}')
    return m.group(1), _b64_to_a32(m.group(2))

def _try_resolve_node(node, folder_key):
    raw_k = node.get('k', '')
    if not raw_k: return None
    candidates = []
    for entry in raw_k.split('/'):
        part = entry.split(':', 1)[1] if ':' in entry else entry
        if part: candidates.append(part)
    for cand in candidates:
        try: enc = _b64_to_a32(cand)
        except Exception: continue
        for try_fn in [
            lambda e: _xor_blocks(e, folder_key),
            lambda e: _str_to_a32(AES.new(_a32_to_str(folder_key[:4]), AES.MODE_ECB).decrypt(
                _a32_to_str(e) + b'\x00' * ((16 - len(_a32_to_str(e)) % 16) % 16)
            )),
        ]:
            try:
                dec = try_fn(enc)
                aes_key, iv = _get_node_aes_key_and_iv(dec)
                for test_key in [aes_key, dec[:4]]:
                    attr = _decrypt_attr(node['a'], test_key)
                    if attr.get('n'):
                        return {'name': attr['n'], 'handle': node['h'],
                                'aes_key': aes_key, 'iv': iv, 'size': node.get('s', 0)}
            except Exception:
                pass
    return None

def list_folder_files(folder_url, proxy=None, timeout=20):
    folder_id, folder_key = parse_folder_url(folder_url)
    data = _api_call({'a': 'f', 'c': 1, 'ca': 1, 'r': 1},
                     node_id=folder_id, proxy=proxy, timeout=timeout)
    if isinstance(data, int):
        raise RuntimeError(f'Mega API error code: {data}')
    files = []
    for node in data.get('f', []):
        if node.get('t') != 0: continue
        resolved = _try_resolve_node(node, folder_key)
        if resolved:
            files.append(resolved)
        else:
            files.append({
                'name': node.get('h', '???'), 'handle': node.get('h', ''),
                'aes_key': None, 'iv': None, 'size': node.get('s', 0),
                'error': 'Key/attribute error',
            })
    return files, folder_id



#  MEGA FILE DOWNLOAD
def download_folder_file(folder_id, file_info, dest_path, proxy=None,
                         timeout=120, chunk_kb=2048, conflict='rename'):
    data = _api_call({'a': 'g', 'g': 1, 'n': file_info['handle']},
                     node_id=folder_id, proxy=proxy)
    if isinstance(data, int):
        raise RuntimeError(f'API error: {data}')
    dl_url = data.get('g')
    if not dl_url: raise RuntimeError('No download URL received')

    k      = _a32_to_str(file_info['aes_key'])
    iv_int = int.from_bytes(_a32_to_str(file_info['iv']), 'big')
    ctr    = Counter.new(128, initial_value=iv_int)
    cipher = AES.new(k, AES.MODE_CTR, counter=ctr)

    proxies  = {'http': proxy, 'https': proxy} if proxy else None
    filepath = os.path.join(dest_path, file_info['name'])

    if os.path.exists(filepath):
        if conflict == 'skip': return filepath, True
        elif conflict == 'rename':
            base, ext = os.path.splitext(file_info['name'])
            filepath  = os.path.join(dest_path, f"{base}_{file_info['handle']}{ext}")

    resp = requests.get(dl_url, stream=True, proxies=proxies, timeout=timeout)
    resp.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=chunk_kb * 1024):
            if chunk: f.write(cipher.decrypt(chunk))
    return filepath, False



#  DROPBOX DOWNLOAD LOGIC
def download_dropbox_url(url, dest_path, proxy=None, timeout=120, chunk_kb=2048):
    # Ensure URL forces download
    url = url.replace('?dl=0', '')
    if '?' in url: url += '&dl=1'
    else: url += '?dl=1'

    proxies = {'http': proxy, 'https': proxy} if proxy else None
    resp = requests.get(url, stream=True, proxies=proxies, timeout=timeout)
    resp.raise_for_status()

    fname = "dropbox_download"
    cd = resp.headers.get('content-disposition')
    if cd:
        m = re.search(r'filename\*?=(?:UTF-8\'\')?([^;]+)', cd, re.IGNORECASE)
        if m:
            fname = m.group(1).strip("'\"")
            fname = urllib.parse.unquote(fname)
    
    if fname == "dropbox_download":
        parsed = urllib.parse.urlparse(url)
        path_parts = parsed.path.split('/')
        if path_parts[-1]: fname = path_parts[-1]


    if 'zip' in resp.headers.get('Content-Type', '').lower() and not fname.endswith('.zip'):
        fname += '.zip'

    filepath = os.path.join(dest_path, fname)
    

    if os.path.exists(filepath):
        base, ext = os.path.splitext(fname)
        import time
        filepath = os.path.join(dest_path, f"{base}_{int(time.time())}{ext}")

    with open(filepath, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=chunk_kb * 1024):
            if chunk: f.write(chunk)
            
    return filepath, False



#  PROXY HELPERS
def load_proxies(template_str="ip,port,user,pass", delim=":"):
    if not os.path.exists('proxies.txt'):
        return []
    
    proxies = []
    fields = [f.strip() for f in template_str.split(',')] if template_str else []
    if not delim: delim = ":"

    with open('proxies.txt', 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip()
            if not p or p.startswith('#'): continue
            
            if 'proto' not in fields:
                p = re.sub(r'^[a-zA-Z0-9]+://', '', p)
            else:
                p = p.replace('://', f"{delim}")

            parts = p.split(delim)
            
            parsed = dict(zip(fields, parts))
            
            ip = parsed.get('ip', '').strip()
            port = parsed.get('port', '').strip()
            user = parsed.get('user', '').strip()
            pwd = parsed.get('pass', '').strip()
            proto = parsed.get('proto', 'http').strip()
            
            if not ip: continue

            proto = proto.replace('://', '')
            if not proto: proto = 'http'

            if user and pwd:
                user_enc = urllib.parse.quote(user)
                pwd_enc = urllib.parse.quote(pwd)
                proxies.append(f'{proto}://{user_enc}:{pwd_enc}@{ip}:{port}')
            elif ip and port:
                proxies.append(f'{proto}://{ip}:{port}')
            else:
                proxies.append(f'http://{p}')
                
    return proxies

def check_proxy(proxy_url, service='mega', timeout=8):
    test_url = 'https://www.dropbox.com' if service == 'dropbox' else 'https://g.api.mega.co.nz/cs'
    try:
        r = requests.get(test_url,
                         proxies={'http': proxy_url, 'https': proxy_url},
                         timeout=timeout)
        return True
    except Exception:
        return False

def get_live_proxies(proxy_list, service='mega'):
    live, dead = [], []
    lock = threading.Lock()
    def test(p):
        ok = check_proxy(p, service)
        with lock:
            (live if ok else dead).append(p)
    with ThreadPoolExecutor(max_workers=min(50, len(proxy_list))) as ex:
        list(ex.map(test, proxy_list))
    return live, dead


#  PARALLEL DOWNLOAD POOL (For MEGA folders & Dropbox Multi-Links)
def run_parallel_downloads(queue_items, process_func, live_proxies, log_queue,
                           max_workers=None):
    if not live_proxies: live_proxies = [None]
    n_workers = max_workers or len(live_proxies)
    dl_queue  = queue.Queue()
    for item in queue_items: dl_queue.put(item)

    ok_count = fail_count = skip_count = 0
    lock = threading.Lock()

    def worker(proxy):
        nonlocal ok_count, fail_count, skip_count
        while True:
            try: item = dl_queue.get_nowait()
            except queue.Empty: break
            
            try:
                path, skipped, name, size_mb = process_func(item, proxy)
                if skipped:
                    log_queue.put(f"<span class='cm'>[SKIP] {name} – already exists</span><br>")
                    with lock: skip_count += 1
                else:
                    log_queue.put(f"<span class='cg'>[OK] {name} ({size_mb})</span><br>")
                    with lock: ok_count += 1
            except Exception as e:
                err = str(e)
                name = item.get('name', 'URL') if isinstance(item, dict) else item
                if 'ProxyError' in err or '402' in err or 'tunnel' in err.lower():
                    dl_queue.put(item)
                    log_queue.put(f"<span class='co'>[PROXY] {proxy} dead – requeueing {name}</span><br>")
                    dl_queue.task_done(); break
                else:
                    log_queue.put(f"<span class='cr'>[FAIL] {name} – {err}</span><br>")
                    with lock: fail_count += 1
            dl_queue.task_done()

    threads = [threading.Thread(target=worker,
               args=(live_proxies[i % len(live_proxies)],), daemon=True)
               for i in range(n_workers)]
    for t in threads: t.start()
    for t in threads: t.join()

    leftover = 0
    while not dl_queue.empty():
        try: dl_queue.get_nowait(); leftover += 1
        except queue.Empty: break
    return ok_count, fail_count, skip_count, leftover


#  FLASK ROUTES
@app.route('/')
def index():
    default_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'CloudDownloads')
    return render_template_string(HTML_INDEX, default_path=default_path)


@app.route('/browse')
def browse():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory(title='Select download folder')
        root.destroy()
        return {'path': path or ''}
    except Exception as e:
        return {'path': '', 'error': str(e)}


@app.route('/download', methods=['POST'])
def download():
    service          = request.form.get('service', 'mega')
    mode             = request.form.get('mode', 'single_file')
    output_path      = request.form.get('output_path', '').strip() or \
                       os.path.join(os.path.expanduser('~'), 'Downloads', 'CloudDownloads')
    proxy_mode       = request.form.get('proxy_mode', 'auto')
    validate_proxies = request.form.get('validate_proxies') == '1'
    timeout          = int(request.form.get('timeout', 20))
    chunk_kb         = 2048


    auto_delim       = request.form.get('auto_proxy_delim', ':')
    auto_template    = request.form.get('auto_proxy_template', 'ip,port,user,pass')

    urls = []
    if mode == 'single_file':
        u = request.form.get('url_single', '').strip()
        if u: urls.append(u)
    elif mode == 'single_folder':
        u = request.form.get('url_folder', '').strip()
        if u: urls.append(u)
    elif mode == 'multi_folder':
        for u in request.form.getlist('urls_multi[]'):
            if u.strip(): urls.append(u.strip())
    elif mode == 'mixed':
        for u in request.form.getlist('urls_mixed[]'):
            if u.strip(): urls.append(u.strip())

    os.makedirs(output_path, exist_ok=True)


    LOG_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Download log – Downloader</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Figtree:wght@400;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--s:#161b22;--b:#30363d;--t:#e6edf3;--m:#7d8590;
      --g:#3fb950;--o:#e3b341;--r:#f85149;--a:#58a6ff;--db:#0061FE}
body{font-family:'JetBrains Mono',monospace;background:var(--bg);color:var(--t);
     padding:32px;font-size:12px;line-height:1.75}
.hd{border-bottom:1px solid var(--b);padding-bottom:16px;margin-bottom:20px;
    font-family:'Figtree',sans-serif}
.hd h1{font-size:16px;font-weight:600;color:var(--t)}
.hd p{font-size:12px;color:var(--m);margin-top:4px;font-family:'JetBrains Mono',monospace}
.meta{background:var(--s);border:1px solid var(--b);border-radius:5px;
      padding:12px 14px;margin-bottom:18px;display:grid;
      grid-template-columns:110px 1fr;gap:3px 10px}
.mk{color:var(--m);font-size:11px}.mv{color:var(--a);font-size:11px;word-break:break-all}
.mv.db{color:var(--db)}
.log{background:var(--s);border:1px solid var(--b);border-radius:5px;padding:14px;min-height:160px}
.cg{color:var(--g)}.co{color:var(--o)}.cr{color:var(--r)}.cm{color:var(--m)}.ca{color:var(--a)}
.banner{margin-top:14px;padding:10px 14px;border-radius:5px;font-family:'Figtree',sans-serif;
        font-size:13px;font-weight:600}
.back{display:inline-block;margin-top:16px;padding:8px 18px;
      background:var(--s);border:1px solid var(--b);border-radius:5px;
      color:var(--t);text-decoration:none;font-family:'Figtree',sans-serif;font-size:13px}
.back:hover{border-color:var(--m)}
</style>
</head><body>
<div class="hd">
  <h1>Cloud Downloader</h1>
  <p>// download log</p>
</div>
'''

    def gen():
        yield LOG_PAGE
        url_display = urls[0] if len(urls) == 1 else f'{len(urls)} URLs'
        srv_class = "db" if service == "dropbox" else ""
        yield f'''<div class="meta">
  <span class="mk">Service</span><span class="mv {srv_class}" style="text-transform:uppercase;font-weight:bold;">{service}</span>
  <span class="mk">Mode</span><span class="mv">{mode}</span>
  <span class="mk">URL(s)</span><span class="mv">{url_display}</span>
  <span class="mk">Destination</span><span class="mv">{output_path}</span>
  <span class="mk">Proxy mode</span><span class="mv">{proxy_mode}</span>
</div><div class="log">'''

        if not urls:
            yield "<span class='cr'>[error] No URLs given.</span><br>"
            yield '</div><a href="/" class="back">← Back</a></body></html>'
            return

        live_proxies = []
        if proxy_mode == 'none':
            yield "[info] No proxy – direct connection.<br>"
        elif proxy_mode == 'manual':
            protos = request.form.getlist('prox_proto[]')
            hosts = request.form.getlist('prox_host[]')
            ports = request.form.getlist('prox_port[]')
            users = request.form.getlist('prox_user[]')
            passes = request.form.getlist('prox_pass[]')
            
            raw_lines = []
            for i in range(len(hosts)):
                host = hosts[i].strip()
                if not host: continue
                port = ports[i].strip()
                proto = protos[i]
                user = users[i].strip()
                pwd = passes[i].strip()
                if user and pwd:
                    raw_lines.append(f"{proto}://{user}:{pwd}@{host}:{port}")
                else:
                    raw_lines.append(f"{proto}://{host}:{port}")

            if validate_proxies and raw_lines:
                yield f"[info] Validating {len(raw_lines)} manual proxy boxes …<br>"
                live_proxies, dead = get_live_proxies(raw_lines, service)
                yield (f"<span class='cg'>[ok] {len(live_proxies)} live</span> / "
                       f"<span class='cr'>{len(dead)} dead</span><br><br>")
                if len(live_proxies) == 0 and len(dead) > 0:
                    yield "<span class='co'>[warn] Alle manuellen Proxies sind tot! Stimmen die Logindaten?</span><br><br>"
            else:
                live_proxies = raw_lines
                yield f"[info] {len(live_proxies)} manual proxies loaded.<br>"
        else:
            raw_proxies = load_proxies(template_str=auto_template, delim=auto_delim)
            
            if not raw_proxies:
                yield "[warn] proxies.txt not found (or empty) – using direct connection.<br><br>"
            else:
                fmt_display = auto_template.replace(',', auto_delim)
                yield f"[info] Loaded {len(raw_proxies)} proxies based on format: <span class='ca'>{fmt_display}</span>.<br>"
                
                if validate_proxies:
                    yield "[info] Validating …<br>"
                    live_proxies, dead = get_live_proxies(raw_proxies, service)
                    yield (f"<span class='cg'>[ok] {len(live_proxies)} live</span>  "
                           f"<span class='cr'>[dead] {len(dead)}</span><br><br>")
                    if len(live_proxies) == 0 and len(dead) > 0:
                        yield "<span class='co'>[warn] Alle Proxies sind tot! Hast du evtl. Username & Passwort im Kästchen-Format vertauscht?</span><br><br>"
                else:
                    live_proxies = raw_proxies
                    yield f"[info] {len(live_proxies)} proxies (unvalidated).<br>"

        n_w = len(live_proxies) if live_proxies else 1
        yield f"[info] Ready with {n_w} worker thread(s).<br><br>"

        total_ok = total_fail = total_skip = 0

        if service == 'dropbox':
            lq = queue.Queue()
            rb = [None]
            
            def db_process(url, proxy):
                path, skipped = download_dropbox_url(url, output_path, proxy=proxy, timeout=timeout, chunk_kb=chunk_kb)
                name = os.path.basename(path)
                size_mb = f"{os.path.getsize(path) / 1024 / 1024:.1f} MB" if os.path.exists(path) else "? MB"
                return path, skipped, name, size_mb

            def _run():
                ok, fail, skip, left = run_parallel_downloads(
                    urls, db_process, live_proxies, lq, max_workers=len(live_proxies) if live_proxies else 1
                )
                rb[0] = (ok, fail, skip, left)
                lq.put(None)

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            while True:
                try: msg = lq.get(timeout=90)
                except queue.Empty:
                    yield "[warn] No progress for 90s – aborting wait.<br>"
                    break
                if msg is None: break
                yield msg
                yield '<script>window.scrollTo(0,document.body.scrollHeight)</script>'
            t.join()
            ok, fail, skip, left = rb[0] or (0, 0, 0, 0)
            total_ok += ok; total_fail += fail; total_skip += skip


        elif service == 'mega':
            for idx, raw_url in enumerate(urls):
                is_folder = '/folder/' in raw_url
                yield (f"<br><span class='ca'>── [{idx+1}/{len(urls)}] "
                       f"{raw_url[:72]}{'…' if len(raw_url)>72 else ''}</span><br>")

                if is_folder:
                    try:
                        yield "[info] Fetching file list …<br>"
                        proxy_for_api = live_proxies[0] if live_proxies else None
                        files, folder_id = list_folder_files(
                            raw_url, proxy=proxy_for_api, timeout=timeout)
                        ok_k  = sum(1 for f in files if not f.get('error'))
                        bad_k = len(files) - ok_k
                        yield (f"[info] {len(files)} file(s) found – "
                               f"<span class='cg'>{ok_k} decrypted</span>"
                               + (f", <span class='co'>{bad_k} error(s)</span>" if bad_k else "")
                               + "<br><br>")

                        lq = queue.Queue()
                        rb = [None]
                        
                        def mega_process(fi, proxy):
                            if fi.get('error') or not fi.get('aes_key'):
                                raise Exception(fi.get('error','no key'))
                            path, skipped = download_folder_file(
                                folder_id, fi, output_path, proxy=proxy,
                                timeout=timeout, chunk_kb=chunk_kb, conflict='rename')
                            return path, skipped, fi['name'], f"{fi.get('size', 0) / 1024 / 1024:.1f} MB"

                        def _run():
                            ok, fail, skip, left = run_parallel_downloads(
                                files, mega_process, live_proxies, lq
                            )
                            rb[0] = (ok, fail, skip, left)
                            lq.put(None)

                        t = threading.Thread(target=_run, daemon=True)
                        t.start()
                        while True:
                            try: msg = lq.get(timeout=90)
                            except queue.Empty:
                                yield "[warn] No progress for 90s – aborting wait.<br>"
                                break
                            if msg is None: break
                            yield msg
                            yield '<script>window.scrollTo(0,document.body.scrollHeight)</script>'
                        t.join()
                        ok, fail, skip, left = rb[0] or (0, 0, 0, 0)
                        total_ok += ok; total_fail += fail; total_skip += skip
                    except Exception as e:
                        yield f"<span class='cr'>[error] {e}</span><br>"
                else:
                    proxy = live_proxies[0] if live_proxies else None
                    if proxy:
                        os.environ['http_proxy']  = proxy
                        os.environ['https_proxy'] = proxy
                    else:
                        os.environ.pop('http_proxy',  None)
                        os.environ.pop('https_proxy', None)
                    try:
                        Mega().login().download_url(raw_url, dest_path=output_path)
                        yield "<span class='cg'>[ok] File downloaded.</span><br>"
                        total_ok += 1
                    except Exception as e:
                        err = str(e)
                        if 'Bandwidth limit' in err:
                            yield "<span class='co'>[limit] Bandwidth exhausted.</span><br>"
                        else:
                            yield f"<span class='cr'>[error] {err}</span><br>"
                        total_fail += 1


        yield "<br>"
        if total_fail == 0 and total_ok > 0:
            bg, bc = '#0d2818', '#3fb950'
            label  = f"✓ Done – {total_ok} OK" + (f"  ·  {total_skip} skipped" if total_skip else "")
        elif total_ok > 0:
            bg, bc = '#2c1f0a', '#e3b341'
            label  = f"⚠ Partial – {total_ok} OK  ·  {total_fail} failed"
        else:
            bg, bc = '#2c0d0e', '#f85149'
            label  = f"✗ Failed – {total_fail} error(s)"

        yield (f'<div class="banner" style="background:{bg};border:1px solid {bc}">{label}</div>')


        if total_ok > 0:
            try:
                if os.name == 'nt': os.startfile(output_path)
                else:
                    import subprocess
                    cmd = 'xdg-open' if os.uname().sysname == 'Linux' else 'open'
                    subprocess.Popen([cmd, output_path])
            except Exception: pass

        yield '</div>'
        yield '<a href="/" class="back">← New download</a>'
        yield '<script>window.scrollTo(0,document.body.scrollHeight)</script>'
        yield '</body></html>'

    return Response(gen(), mimetype='text/html')

if __name__ == '__main__':
    _print_banner()
    threading.Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(port=5000, threaded=True, use_reloader=False)