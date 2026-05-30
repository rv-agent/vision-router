"""Vision Router Web UI — settings + analyze via browser"""
import os, sys, tempfile, json, requests
from flask import Flask, request, jsonify, render_template_string, Response

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from vision.core.router import route
from vision.core.preprocessor import preprocess_image

app = Flask(__name__)

# Gemini models that support vision
GEMINI_MODELS = [
    "gemini-3.1-flash-lite", "gemini-2.0-flash-001",
    "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.5-flash"
]

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vision Router</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh}
.container{max-width:720px;margin:0 auto;padding:40px 20px}
h1{font-size:26px;margin-bottom:4px;color:#58a6ff}
p.sub{color:#8b949e;font-size:14px;margin-bottom:24px}
.tabs{display:flex;gap:4px;margin-bottom:20px;border-bottom:1px solid #30363d}
.tab{padding:10px 20px;cursor:pointer;border-radius:6px 6px 0 0;font-size:14px;font-weight:600;color:#8b949e;transition:.2s;border-bottom:2px solid transparent}
.tab:hover{color:#c9d1d9}.tab.active{color:#58a6ff;border-bottom-color:#58a6ff}
.page{display:none}.page.active{display:block}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px;margin-bottom:16px}
label{display:block;font-size:13px;font-weight:600;margin-bottom:6px;color:#c9d1d9}
input,textarea,select{width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:14px;margin-bottom:14px;font-family:inherit}
textarea{font-family:monospace;resize:vertical}
input[type=file]{cursor:pointer;margin-bottom:0}
.btn{background:#238636;color:#fff;border:none;padding:10px 24px;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;transition:.2s;margin-top:4px;margin-right:8px;display:inline-block}
.btn:hover{background:#2ea043}.btn:disabled{background:#23863680;cursor:not-allowed}
.btn.test{background:#1f6feb}.btn.test:hover{background:#388bfd}
.preview{max-width:100%;max-height:400px;border-radius:6px;margin-top:8px;display:none}
.result{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:16px;margin-top:12px;display:none;font-size:14px;line-height:1.6}
.result .meta{color:#8b949e;font-size:12px;margin-bottom:8px}
.result .provider{color:#58a6ff;font-weight:600}.error{color:#f85149}
.loading{display:none;text-align:center;padding:20px;color:#8b949e}
.spinner{width:24px;height:24px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 8px}
@keyframes spin{to{transform:rotate(360deg)}}
pre{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;overflow-x:auto;font-size:13px;margin-top:8px;white-space:pre-wrap}
.toast{position:fixed;top:20px;right:20px;background:#238636;color:#fff;padding:12px 20px;border-radius:6px;font-size:14px;display:none;z-index:999}
.toast.error{background:#da3633}
.test-result{margin-top:12px;display:none}
.test-row{padding:6px 10px;border-radius:4px;margin:4px 0;font-size:13px;font-family:monospace;display:flex;justify-content:space-between}
.test-row.ok{background:#23863620;border:1px solid #238636;color:#3fb950}
.test-row.fail{background:#da363320;border:1px solid #da3633;color:#f85149}
.test-row.rate{background:#d2992220;border:1px solid #d29922;color:#d29922}
</style>
</head>
<body>
<div class="container">
  <h1>Vision Router</h1>
  <p class="sub">Multi-provider image analysis with auto-fallback</p>
  <div class="tabs">
    <div class="tab active" onclick="switchTab('analyze')">Analyze</div>
    <div class="tab" onclick="switchTab('settings')">Settings</div>
  </div>

  <div id="page-analyze" class="page active">
    <div class="card">
      <label>Upload Image</label>
      <input type="file" id="image" accept="image/*" onchange="preview(event)">
      <img id="preview" class="preview">
    </div>
    <div class="card">
      <label>Or File Path</label>
      <input type="text" id="path" placeholder="/path/to/screenshot.png" oninput="clearFile()">
    </div>
    <div class="card">
      <label>Prompt</label>
      <input type="text" id="prompt" value="Describe this image in detail">
    </div>
    <button class="btn" id="btn" onclick="analyze()">Analyze</button>
    <div id="loading" class="loading"><div class="spinner"></div>Analyzing...</div>
    <div id="result" class="result"></div>
    <div id="error" class="error"></div>
  </div>

  <div id="page-settings" class="page">
    <div class="card">
      <h3 style="margin-bottom:12px;color:#c9d1d9">Configuration</h3>
      <p style="color:#8b949e;font-size:13px;margin-bottom:16px">Saved to <code>.env</code>. <b>Auto-fallback:</b> tries all keys → switches provider → all exhausted = error.</p>

      <label>Primary Provider</label>
      <select id="set-provider" onchange="updateModelDropdown()">
        <option value="google-ai-studio">Google AI Studio (Gemini)</option>
        <option value="openrouter">OpenRouter</option>
      </select>

      <label id="model-label">Model (Google AI Studio)</label>
      <select id="set-model"></select>

      <label>Google AI Studio API Keys — one per line</label>
      <textarea id="set-gemini" rows="3" placeholder="AIzaSy..."></textarea>
      <label>OpenRouter API Keys — one per line</label>
      <textarea id="set-or" rows="3" placeholder="sk-or-v1-..."></textarea>

      <button class="btn" onclick="saveSettings()">Save</button>
      <button class="btn test" onclick="testKeys()">Test Keys</button>
      <div id="test-result" class="test-result"></div>
    </div>
  </div>
</div>
<div id="toast" class="toast"></div>
<script>
var geminiModels=["gemini-3.1-flash-lite","gemini-2.0-flash-001","gemini-3-flash-preview","gemini-2.5-flash","gemini-3.5-flash"];
function updateModelDropdown(){var p=document.getElementById('set-provider').value,sel=document.getElementById('set-model');sel.innerHTML='';if(p==='google-ai-studio'){document.getElementById('model-label').textContent='Model (Google AI Studio)';geminiModels.forEach(function(m){var o=document.createElement('option');o.value=m;o.textContent=m;sel.appendChild(o)})}else{document.getElementById('model-label').textContent='Model (OpenRouter)';var o=document.createElement('option');o.value='openrouter/free';o.textContent='openrouter/free (auto-pick free)';sel.appendChild(o)}}
function switchTab(t){document.querySelectorAll('.tab').forEach(function(e){e.classList.toggle('active',e.textContent.trim().toLowerCase()===t)});document.querySelectorAll('.page').forEach(function(p){p.classList.toggle('active',p.id==='page-'+t)});if(t==='settings')loadSettings()}
function toast(m,e){var t=document.getElementById('toast');t.textContent=m;t.className='toast'+(e||'');t.style.display='block';setTimeout(function(){t.style.display='none'},3000)}
function preview(e){var f=e.target.files[0];if(!f)return;var r=new FileReader();r.onload=function(ev){document.getElementById('preview').style.display='block';document.getElementById('preview').src=ev.target.result};r.readAsDataURL(f);document.getElementById('path').value=''}
function clearFile(){document.getElementById('image').value='';document.getElementById('preview').style.display='none'}
async function analyze(){var btn=document.getElementById('btn'),p=document.getElementById('prompt').value,path=document.getElementById('path').value,file=document.getElementById('image').files[0],ld=document.getElementById('loading'),r=document.getElementById('result'),e=document.getElementById('error');r.style.display='none';e.style.display='none';btn.disabled=true;ld.style.display='block';var f=new FormData();file?f.append('file',file):f.append('path',path);f.append('prompt',p);try{var resp=await fetch('/analyze',{method:'POST',body:f});var d=await resp.json();ld.style.display='none';btn.disabled=false;d.success?(r.innerHTML='<div class="meta">Provider: <span class="provider">'+d.provider+'</span></div><pre>'+d.result+'</pre>',r.style.display='block'):(e.innerHTML='<strong>ERROR:</strong> '+d.error,e.style.display='block')}catch(ex){ld.style.display='none';btn.disabled=false;e.innerHTML='<strong>ERROR:</strong> '+ex.message,e.style.display='block'}}
async function loadSettings(){try{var r=await fetch('/api/env');var d=await r.json();d.gemini&&(document.getElementById('set-gemini').value=d.gemini);d.or_&&(document.getElementById('set-or').value=d.or_);document.getElementById('set-provider').value=d.provider||'google-ai-studio';updateModelDropdown();var sel=document.getElementById('set-model');if(d.model){for(var i=0;i<sel.options.length;i++){if(sel.options[i].value===d.model){sel.selectedIndex=i;break}}}}catch(e){}}
async function saveSettings(){var g=document.getElementById('set-gemini').value.trim(),o=document.getElementById('set-or').value.trim(),m=document.getElementById('set-model').value,p=document.getElementById('set-provider').value;var fallback=p==='google-ai-studio'?'gemini,openrouter':'openrouter,gemini';try{var r=await fetch('/api/save-env',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gemini:g,or:o,model:m,fallback:fallback,provider:p})});var d=await r.json();toast(d.success?'Saved!':'Error','')}catch(e){toast('Error','error')}}
async function testKeys(){var btn=event.target;btn.disabled=true;var d=document.getElementById('test-result');d.style.display='block';d.innerHTML='<div class="loading" style="display:block"><div class="spinner"></div>Testing keys...</div>';var es=new EventSource('/api/test-keys');es.onmessage=function(e){var data=JSON.parse(e.data);if(data.done){es.close();return}var cls='ok';if(data.status.includes('invalid')||data.status.includes('disabled')||data.status.includes('error')||data.status==='timeout')cls='fail';if(data.status==='rate_limited')cls='rate';var row=document.createElement('div');row.className='test-row '+cls;row.innerHTML='<span>'+data.label+'</span><span>'+data.status+'</span>';d.appendChild(row)};es.onerror=function(){es.close();btn.disabled=false}}
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/env")
def get_env():
    env_path = os.path.join(ROOT, ".env")
    gemini, or_keys, model, fallback = [], [], "openrouter/free", "gemini,openrouter"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_APIKEY_"):
                    gemini.append(line.split("=", 1)[1])
                elif line.startswith("OPENROUTER_APIKEY_"):
                    or_keys.append(line.split("=", 1)[1])
                elif line.startswith("OPENROUTER_MODEL="):
                    model = line.split("=", 1)[1]
                elif line.startswith("FALLBACK_ORDER="):
                    fallback = line.split("=", 1)[1]
    provider = "google-ai-studio" if fallback.startswith("gemini") else "openrouter"
    return jsonify(gemini="\n".join(gemini), or_="\n".join(or_keys), model=model,
                   fallback=fallback, provider=provider)

@app.route("/api/save-env", methods=["POST"])
def save_env():
    data = request.get_json() or {}
    env_path = os.path.join(ROOT, ".env")
    lines = ["# GOOGLE AI STUDIO"]
    for i, k in enumerate([x.strip() for x in data.get("gemini", "").split("\n") if x.strip()], 1):
        lines.append(f"GEMINI_APIKEY_{i}={k}")
    if not any(l.startswith("GEMINI_APIKEY_") for l in lines):
        lines.append("GEMINI_APIKEY_=")
    lines.append(f"GEMINI_MODEL={data.get('model', 'gemini-3.1-flash-lite')}")
    lines.append("")
    lines.append("# OPENROUTER")
    for i, k in enumerate([x.strip() for x in data.get("or", "").split("\n") if x.strip()], 1):
        lines.append(f"OPENROUTER_APIKEY_{i}={k}")
    if not any(l.startswith("OPENROUTER_APIKEY_") for l in lines):
        lines.append("OPENROUTER_APIKEY_=")
    or_model = "openrouter/free"
    lines.append(f"OPENROUTER_MODEL={or_model}")
    lines.append(f"FALLBACK_ORDER={data.get('fallback', 'gemini,openrouter')}")
    lines.append("")
    with open(env_path, "w") as f:
        f.write("\n".join(lines))
    return jsonify(success=True)

@app.route("/api/test-keys")
def test_keys():
    env_path = os.path.join(ROOT, ".env")

    def generate():
        gemini_keys, or_keys = [], []
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_APIKEY_"):
                        val = line.split("=", 1)[1]
                        if val: gemini_keys.append(val)
                    elif line.startswith("OPENROUTER_APIKEY_"):
                        val = line.split("=", 1)[1]
                        if val: or_keys.append(val)

        g_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
        for i, key in enumerate(gemini_keys):
            try:
                resp = requests.post(f"{g_url}?key={key}", json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=8)
                if resp.status_code == 200:
                    yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': 'ok'})}\n\n"
                elif resp.status_code == 429:
                    yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': 'rate_limited'})}\n\n"
                elif resp.status_code == 400:
                    yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': 'invalid'})}\n\n"
                elif resp.status_code == 403:
                    yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': 'disabled (403)'})}\n\n"
                else:
                    yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': f'error ({resp.status_code})'})}\n\n"
            except:
                yield f"data: {json.dumps({'label': f'Gemini key {i+1}', 'status': 'timeout'})}\n\n"

        or_url = "https://openrouter.ai/api/v1/chat/completions"
        for i, key in enumerate(or_keys):
            try:
                resp = requests.post(or_url, headers={"Authorization": f"Bearer {key}"},
                                    json={"model": "openrouter/free", "messages": [{"role": "user", "content": "hi"}]}, timeout=8)
                if resp.status_code == 200:
                    yield f"data: {json.dumps({'label': f'OR key {i+1}', 'status': 'ok'})}\n\n"
                elif resp.status_code == 429:
                    yield f"data: {json.dumps({'label': f'OR key {i+1}', 'status': 'rate_limited'})}\n\n"
                elif resp.status_code == 401:
                    yield f"data: {json.dumps({'label': f'OR key {i+1}', 'status': 'invalid'})}\n\n"
                else:
                    yield f"data: {json.dumps({'label': f'OR key {i+1}', 'status': f'error ({resp.status_code})'})}\n\n"
            except:
                yield f"data: {json.dumps({'label': f'OR key {i+1}', 'status': 'timeout'})}\n\n"

        if not gemini_keys and not or_keys:
            yield f"data: {json.dumps({'label': 'No keys', 'status': 'add keys first'})}\n\n"
        yield "data: {\"done\": true}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/analyze", methods=["POST"])
def handle_analyze():
    prompt = request.form.get("prompt", "Describe this image in detail")
    if "file" in request.files and request.files["file"].filename:
        f = request.files["file"]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        f.save(tmp.name)
        img_path = tmp.name
    elif request.form.get("path"):
        img_path = request.form["path"]
        if not os.path.exists(img_path):
            return jsonify(success=False, error=f"File not found: {img_path}")
    else:
        return jsonify(success=False, error="No image provided")
    try:
        b64, mime = preprocess_image(img_path)
        result = route(b64, mime, prompt)
        return jsonify(success=result["success"], provider=result["provider"],
                       result=result["result"], error=result["error"])
    except Exception as e:
        return jsonify(success=False, error=str(e))
    finally:
        if "file" in request.files and request.files["file"].filename:
            try: os.remove(img_path)
            except: pass

def run_server(host="0.0.0.0", port=5050):
    print(f"🌐 http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
