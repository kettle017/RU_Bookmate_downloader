import webview
import threading
import subprocess
import sys
import os
import json
from pathlib import Path

HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bookmate Downloader</title>
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --bg-color: #f8f9fa;
            --text-color: #333;
            --border-radius: 8px;
        }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            flex-direction: column;
            height: 95vh;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: var(--border-radius);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h2 { 
            color: var(--secondary-color); 
            margin-top: 0;
            text-align: center;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: 600;
            color: var(--secondary-color);
        }
        select, input[type="text"] { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            font-size: 14px;
            box-sizing: border-box;
        }
        select:focus, input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            font-weight: normal;
            cursor: pointer;
        }
        .checkbox-label input {
            margin-right: 8px;
        }
        button { 
            background-color: var(--primary-color); 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            font-size: 16px; 
            border-radius: 4px; 
            cursor: pointer; 
            width: 100%; 
            transition: background-color 0.2s;
            font-weight: 600;
            margin-top: 10px;
        }
        button:hover { 
            background-color: #2980b9; 
        }
        button:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        #output-container {
            flex-grow: 1;
            background: #1e1e1e;
            color: #f0f0f0;
            padding: 15px;
            border-radius: var(--border-radius);
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.5;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }
        .log-line {
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .success { color: #2ecc71; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .info { color: #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📚 Bookmate Downloader</h2>
        <div class="form-group">
            <label for="action">Действие:</label>
            <select id="action">
                <option value="audiobook">🎧 Скачать аудиокнигу</option>
                <option value="author">👤 Скачать все аудиокниги автора</option>
                <option value="series">📚 Скачать серию (книги/аудиокниги)</option>
                <option value="book">📖 Скачать текстовую книгу</option>
                <option value="comicbook">💭 Скачать комикс</option>
                <option value="list-author">📋 Показать список аудиокниг автора</option>
            </select>
        </div>
        <div class="form-group">
            <label for="id">ID или UUID:</label>
            <input type="text" id="id" placeholder="Например: a1b2c3d4">
        </div>
        <div class="checkbox-group">
            <label class="checkbox-label">
                <input type="checkbox" id="max_bitrate" checked> Максимальное качество
            </label>
            <label class="checkbox-label">
                <input type="checkbox" id="no_merge"> Не объединять главы
            </label>
            <label class="checkbox-label">
                <input type="checkbox" id="keep_chapters"> Сохранять главы после объединения
            </label>
        </div>
        <button id="runBtn" onclick="runDownloader()">🚀 Запустить</button>
    </div>
    <div id="output-container"></div>

    <script>
        function appendLog(text) {
            const container = document.getElementById('output-container');
            const div = document.createElement('div');
            div.className = 'log-line';
            div.textContent = text;
            
            // Simple coloring based on content
            if (text.includes('❌') || text.includes('Error') || text.includes('Failed')) {
                div.classList.add('error');
            } else if (text.includes('✅') || text.includes('Successfully')) {
                div.classList.add('success');
            } else if (text.includes('⚠️')) {
                div.classList.add('warning');
            }
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function runDownloader() {
            const btn = document.getElementById('runBtn');
            const action = document.getElementById('action').value;
            const id = document.getElementById('id').value;
            const max_bitrate = document.getElementById('max_bitrate').checked;
            const no_merge = document.getElementById('no_merge').checked;
            const keep_chapters = document.getElementById('keep_chapters').checked;
            
            if (!id) {
                appendLog('❌ Пожалуйста, введите ID или UUID.');
                return;
            }

            btn.disabled = true;
            btn.textContent = '⏳ Выполняется...';
            document.getElementById('output-container').innerHTML = ''; // Clear previous output
            appendLog(`🚀 Запуск: ${action} для ${id}...`);

            var args = {action, id, max_bitrate, no_merge, keep_chapters};
            window.pywebview.api.run_downloader(args).then(function(result) {
                btn.disabled = false;
                btn.textContent = '🚀 Запустить';
                appendLog('🏁 Готово!');
            });
        }

        // Function to be called from Python to update log
        function updateLog(text) {
            appendLog(text);
        }
    </script>
</body>
</html>
'''

class Api:
    def run_downloader(self, args):
        import time
        action = args['action']
        id = args['id'].strip()
        
        # Determine python executable
        python_exec = sys.executable
        # If running in a venv, sys.executable should point to it. 
        # If not, check if venv exists in the project directory
        venv_python = Path('venv/bin/python')
        if venv_python.exists():
            python_exec = str(venv_python)

        cmd = [python_exec, '-u', 'RUBookmatedownloader.py', action, id]
        
        if not args['max_bitrate']: # Note: checkbox logic inverted in args vs script
             # In script: --max_bitrate is store_false (default True). 
             # If user UNCHECKS "Max Quality", we pass --max_bitrate (which sets it to False? No wait)
             # Script: parser.add_argument("--max_bitrate", action='store_false')
             # This means if flag IS present, value is False. Default is True.
             # GUI: Checkbox "Max Quality" (checked by default).
             # If Checked (True) -> We want True. So DO NOT pass flag.
             # If Unchecked (False) -> We want False. So PASS flag.
             cmd.append('--max_bitrate')
             
        if args['no_merge']:
            cmd.append('--no-merge')
        if args['keep_chapters']:
            cmd.append('--keep-chapters')

        try:
            # Use Popen to capture output in real-time
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding='utf-8',
                bufsize=1 # Line buffered
            )
            
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    # Use json.dumps to safely format the string for JS, preserving whitespace
                    safe_line = json.dumps(line.rstrip())
                    webview.evaluate_js(f"updateLog({safe_line})")
                # time.sleep(0.01) # Small delay to prevent UI freezing
            
            return "Done"
        except Exception as e:
            return f'❌ Ошибка запуска: {e}'

def start():
    api = Api()
    window = webview.create_window('Bookmate Downloader', html=HTML, width=800, height=700, js_api=api)
    webview.start()

if __name__ == '__main__':
    start()
