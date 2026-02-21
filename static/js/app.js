/* ═══════════════════════════════════════════════════════════
   Unified AI Chatbot – app.js
═══════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────
const state = {
  mode:       'chat',        // 'chat' | 'code' | 'image'
  provider:   '',
  model:      '',
  providers:  [],
  loading:    false,
  darkTheme:  true,
};

// ── DOM refs ───────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const messagesEl   = $('messages');
const chatInput    = $('chatInput');
const sendBtn      = $('sendBtn');
const providerSel  = $('providerSelect');
const modelSel     = $('modelSelect');
const tempSlider   = $('tempSlider');
const tempValue    = $('tempValue');
const systemPrompt = $('systemPrompt');

// ── Initialise ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadProviders();
  initTheme();
  bindEvents();
});

// ── Load providers from API ────────────────────────────────
async function loadProviders() {
  try {
    const res  = await fetch('/api/providers');
    state.providers = await res.json();
    renderProviders();
  } catch (e) {
    showToast('Failed to load providers', 'error');
  }
}

function renderProviders() {
  providerSel.innerHTML = '';
  const chat = state.providers.filter(p => p.id !== 'image');
  const img  = state.providers.find(p => p.id === 'image');

  // Only show providers relevant to current mode
  const relevant = state.mode === 'image' ? (img ? [img] : []) : chat;
  if (!relevant.length) {
    providerSel.innerHTML = '<option>No providers available</option>';
    return;
  }

  relevant.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    const lock  = p.configured ? '✅' : '🔑';
    const tier  = p.tier === 'free' ? ' [FREE]' : ' [Paid]';
    opt.textContent = `${lock} ${p.name}${tier}`;
    providerSel.appendChild(opt);
  });

  // Default to first configured free provider
  const firstFree = relevant.find(p => p.configured && p.tier === 'free');
  const firstAny  = relevant.find(p => p.configured);
  const selected  = firstFree || firstAny || relevant[0];
  providerSel.value = selected.id;
  updateModels(selected.id);
  updateTopbar();
}

function updateModels(providerId) {
  const p = state.providers.find(x => x.id === providerId);
  modelSel.innerHTML = '';
  if (!p || !p.models?.length) {
    modelSel.innerHTML = '<option value="">Default</option>';
    return;
  }
  p.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name;
    modelSel.appendChild(opt);
  });
  state.model = p.models[0].id;
}

function updateTopbar() {
  const modeLabels = { chat: '💬 Chat', code: '💻 Code Assist', image: '🎨 Image Generation' };
  $('topbarMode').textContent = modeLabels[state.mode] || state.mode;
  const p = state.providers.find(x => x.id === providerSel.value);
  $('topbarProvider').textContent = p
    ? `${p.name}${p.configured ? '' : ' — add API key in ⚙️ Settings'}`
    : '';
}

// ── Events ─────────────────────────────────────────────────
function bindEvents() {

  // Mode buttons
  $$('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.mode = btn.dataset.mode;

      $$('.panel').forEach(p => p.classList.remove('active'));
      $(`${state.mode}Panel`).classList.add('active');

      renderProviders();
    });
  });

  // Provider / model change
  providerSel.addEventListener('change', () => {
    updateModels(providerSel.value);
    updateTopbar();
  });
  modelSel.addEventListener('change', () => { state.model = modelSel.value; });

  // Temperature
  tempSlider.addEventListener('input', () => {
    tempValue.textContent = tempSlider.value;
  });

  // Chat send
  sendBtn.addEventListener('click', sendChat);
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
  });

  // Code run
  $('runCodeBtn').addEventListener('click', runCode);

  // Image generate
  $('generateBtn').addEventListener('click', generateImage);

  // Clear
  $('clearBtn').addEventListener('click', clearChat);

  // Config modal
  $('configBtn').addEventListener('click', () => {
    $('configModal').classList.add('open');
  });
  $('modalClose').addEventListener('click', closeModal);
  $('modalCancel').addEventListener('click', closeModal);
  $('configModal').addEventListener('click', e => {
    if (e.target === $('configModal')) closeModal();
  });
  $('saveConfig').addEventListener('click', saveConfig);

  // Theme toggle
  $('themeToggle').addEventListener('click', toggleTheme);

  // Sidebar
  $('sidebarToggle').addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('collapsed');
  });
  $('mobileToggle').addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('open');
  });
}

// ── Chat ───────────────────────────────────────────────────
async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg || state.loading) return;

  const provider = providerSel.value;
  if (!provider) { showToast('Select a provider first', 'error'); return; }

  // Clear welcome screen
  const welcome = messagesEl.querySelector('.welcome-msg');
  if (welcome) welcome.remove();

  appendMessage('user', msg);
  chatInput.value = '';
  chatInput.style.height = 'auto';

  const typing = appendTyping();
  setLoading(true);

  try {
    const res  = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message:       msg,
        provider:      provider,
        model:         modelSel.value || '',
        system_prompt: systemPrompt.value.trim(),
        temperature:   parseFloat(tempSlider.value),
        use_history:   true,
      }),
    });
    const data = await res.json();
    typing.remove();

    if (data.success) {
      appendMessage('assistant', data.response);
    } else {
      appendError(data.error || 'Unknown error');
    }
  } catch (e) {
    typing.remove();
    appendError('Network error: ' + e.message);
  } finally {
    setLoading(false);
  }
}

// ── Code ───────────────────────────────────────────────────
async function runCode() {
  const code = $('codeInput').value.trim();
  if (!code) { showToast('Enter code first', 'error'); return; }
  if (state.loading) return;

  const provider = providerSel.value;
  setLoading(true);
  $('codeOutput').innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

  try {
    const res  = await fetch('/api/code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        task:     $('codeTask').value,
        language: $('codeLang').value,
        provider,
        model:    modelSel.value || '',
      }),
    });
    const data = await res.json();
    if (data.success) {
      $('codeOutput').innerHTML = renderMarkdown(data.response);
      highlightCode($('codeOutput'));
    } else {
      $('codeOutput').innerHTML = `<div class="error-msg">${escHtml(data.error)}</div>`;
    }
  } catch (e) {
    $('codeOutput').innerHTML = `<div class="error-msg">Network error: ${escHtml(e.message)}</div>`;
  } finally {
    setLoading(false);
  }
}

// ── Image ──────────────────────────────────────────────────
async function generateImage() {
  const prompt = $('imagePrompt').value.trim();
  if (!prompt) { showToast('Enter a prompt first', 'error'); return; }
  if (state.loading) return;

  setLoading(true);
  $('imageOutput').innerHTML = '<div class="typing-indicator" style="margin:40px auto"><span></span><span></span><span></span></div>';

  try {
    const res  = await fetch('/api/image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        model:   $('imageModel').value,
        size:    $('imageSize').value,
        quality: 'standard',
      }),
    });
    const data = await res.json();
    if (data.success) {
      $('imageOutput').innerHTML = `
        <img src="${escHtml(data.image_url)}" alt="${escHtml(prompt)}"
             onerror="this.src=''; this.alt='Image load failed'"/>
        <div class="image-caption">
          <strong>Prompt:</strong> ${escHtml(prompt)}<br/>
          <small>Model: ${escHtml(data.model || 'unknown')}${data.note ? ' · ' + escHtml(data.note) : ''}</small>
        </div>`;
    } else {
      $('imageOutput').innerHTML = `<div class="error-msg">${escHtml(data.error)}</div>`;
    }
  } catch (e) {
    $('imageOutput').innerHTML = `<div class="error-msg">Network error: ${escHtml(e.message)}</div>`;
  } finally {
    setLoading(false);
  }
}

// ── Clear ──────────────────────────────────────────────────
async function clearChat() {
  await fetch('/api/clear', { method: 'POST' });
  messagesEl.innerHTML = `
    <div class="welcome-msg">
      <div class="welcome-icon">🤖</div>
      <h2>Chat cleared!</h2>
      <p>Start a new conversation.</p>
    </div>`;
  showToast('Conversation cleared');
}

// ── Config ─────────────────────────────────────────────────
async function saveConfig() {
  const body = {
    groq_key:         $('groqKey').value.trim(),
    gemini_key:       $('geminiKey').value.trim(),
    huggingface_key:  $('hfKey').value.trim(),
    openai_key:       $('openaiKey').value.trim(),
    anthropic_key:    $('anthropicKey').value.trim(),
  };
  try {
    const res  = await fetch('/api/configure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      closeModal();
      await loadProviders(); // refresh
    } else {
      showToast(data.error || 'Save failed', 'error');
    }
  } catch (e) {
    showToast('Network error', 'error');
  }
}

function closeModal() {
  $('configModal').classList.remove('open');
}

// ── Helpers ────────────────────────────────────────────────
function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="msg-bubble">${renderMarkdown(content)}</div>`;
  messagesEl.appendChild(div);
  highlightCode(div);
  scrollBottom();
}

function appendTyping() {
  const div = document.createElement('div');
  div.className = 'msg';
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="typing-indicator"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(div);
  scrollBottom();
  return div;
}

function appendError(msg) {
  const div = document.createElement('div');
  div.className = 'msg';
  div.innerHTML = `
    <div class="msg-avatar">⚠️</div>
    <div class="error-msg">${escHtml(msg)}</div>`;
  messagesEl.appendChild(div);
  scrollBottom();
}

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setLoading(v) {
  state.loading = v;
  sendBtn.disabled = v;
  $('sendIcon').textContent = v ? '⏳' : '➤';
}

function renderMarkdown(text) {
  if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
    return marked.parse(text);
  }
  // Fallback: basic escaping + newlines
  return escHtml(text).replace(/\n/g, '<br/>');
}

function highlightCode(el) {
  if (typeof hljs !== 'undefined') {
    el.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
  }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Theme ──────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') {
    document.body.classList.add('light');
    state.darkTheme = false;
    $('themeToggle').textContent = '☀️';
  }
}

function toggleTheme() {
  state.darkTheme = !state.darkTheme;
  document.body.classList.toggle('light', !state.darkTheme);
  $('themeToggle').textContent = state.darkTheme ? '🌙' : '☀️';
  localStorage.setItem('theme', state.darkTheme ? 'dark' : 'light');
}

// ── Toast ──────────────────────────────────────────────────
let toastTimer;
function showToast(msg, type = '') {
  const t = $('toast');
  t.textContent = msg;
  t.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.classList.remove('show'); }, 3200);
}
