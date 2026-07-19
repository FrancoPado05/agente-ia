from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistence.database import get_session
from src.persistence.queries import (
    create_client,
    delete_client,
    get_client_detail,
    list_clients,
    set_client_tool,
    update_client,
)
from src.persistence.repository import ConversationRepository
from src.tools.registry import ToolRegistry

router = APIRouter()


async def get_db(request: Request):
    async with get_session() as session:
        yield session


def _get_registry(request: Request) -> ToolRegistry:
    return request.app.state.tool_registry


# --- API: Clients ---

class ClientCreate(BaseModel):
    client_id: str
    name: str
    phone_number_id: str
    system_prompt: str = ""
    model_name: str = "gemini-2.5-flash"


class ClientUpdate(BaseModel):
    name: str | None = None
    phone_number_id: str | None = None
    system_prompt: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@router.get("/api/clients")
async def api_clients(db: AsyncSession = Depends(get_db)):
    return await list_clients(db)


@router.get("/api/clients/{client_id}")
async def api_client_detail(client_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_client_detail(db, client_id)
    if not data:
        raise HTTPException(status_code=404)
    return data


@router.post("/api/clients")
async def api_create_client(body: ClientCreate, db: AsyncSession = Depends(get_db)):
    result = await create_client(
        db,
        client_id=body.client_id,
        name=body.name,
        phone_number_id=body.phone_number_id,
        system_prompt=body.system_prompt,
        model_name=body.model_name,
    )
    await db.commit()
    return result


@router.put("/api/clients/{client_id}")
async def api_update_client(client_id: str, body: ClientUpdate,
                             db: AsyncSession = Depends(get_db)):
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    ok = await update_client(db, client_id, **kwargs)
    if not ok:
        raise HTTPException(status_code=404)
    await db.commit()
    return {"updated": True}


@router.delete("/api/clients/{client_id}")
async def api_delete_client(client_id: str, db: AsyncSession = Depends(get_db)):
    ok = await delete_client(db, client_id)
    if not ok:
        raise HTTPException(status_code=404)
    await db.commit()
    return {"deleted": True}


@router.put("/api/clients/{client_id}/tools/{tool_id}")
async def api_toggle_tool(client_id: str, tool_id: str, enabled: bool = True,
                           db: AsyncSession = Depends(get_db)):
    await set_client_tool(db, client_id, tool_id, enabled)
    await db.commit()
    return {"ok": True}


# --- API: Tools registry ---

@router.get("/api/tools/registry")
async def api_tools_registry(request: Request):
    registry = _get_registry(request)
    return registry.list_tools()


# --- API: Conversations ---

@router.get("/api/clients/{client_id}/conversations")
async def api_conversations(client_id: str, db: AsyncSession = Depends(get_db)):
    conn = await db.connection()
    repo = ConversationRepository(conn)
    convs = await repo.list_conversations(client_id)
    result = []
    for c in convs:
        msgs = await repo.get_messages(client_id, c.id)
        preview = msgs[-1].content[:80] if msgs else ""
        result.append({
            "id": c.id,
            "phone_number": c.phone_number,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "message_count": len(msgs),
            "last_message": preview,
        })
    return result


@router.get("/api/conversations/{conv_id}/messages")
async def api_messages(conv_id: str, client_id: str, db: AsyncSession = Depends(get_db)):
    conn = await db.connection()
    repo = ConversationRepository(conn)
    msgs = await repo.get_messages(client_id, conv_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]


@router.delete("/api/conversations/{conv_id}")
async def api_delete_conversation(conv_id: str, client_id: str,
                                   db: AsyncSession = Depends(get_db)):
    conn = await db.connection()
    repo = ConversationRepository(conn)
    deleted = await repo.delete_conversation(client_id, conv_id)
    if not deleted:
        raise HTTPException(status_code=404)
    await db.commit()
    return {"deleted": True}


# --- Dashboard page ---

@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page():
    return HTML_PAGE


HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard - Agente IA</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; height: 100vh; background: #f0f2f5; }

  /* Tabs */
  .tabs { display: flex; background: #fff; border-bottom: 1px solid #e0e0e0; }
  .tab { padding: 12px 24px; cursor: pointer; font-size: 14px; font-weight: 500; color: #666; border-bottom: 2px solid transparent; transition: all 0.15s; }
  .tab:hover { color: #333; }
  .tab.active { color: #1976d2; border-bottom-color: #1976d2; }

  /* Layout */
  .layout { display: flex; flex: 1; overflow: hidden; }
  .sidebar { width: 340px; background: #fff; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; }
  .sidebar-header { padding: 16px; border-bottom: 1px solid #e0e0e0; }
  .sidebar-header h2 { font-size: 15px; margin-bottom: 8px; }
  .sidebar-header select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
  .conv-list { flex: 1; overflow-y: auto; }
  .conv-item { padding: 12px 16px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.15s; }
  .conv-item:hover { background: #f5f5f5; }
  .conv-item.active { background: #e3f2fd; }
  .conv-item .phone { font-weight: 600; font-size: 14px; }
  .conv-item .preview { font-size: 12px; color: #666; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .conv-item .meta { font-size: 11px; color: #999; margin-top: 4px; }
  .main { flex: 1; display: flex; flex-direction: column; }
  .main-header { padding: 16px 24px; background: #fff; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
  .main-header h2 { font-size: 16px; }
  .messages { flex: 1; overflow-y: auto; padding: 24px; }
  .msg { max-width: 70%; margin-bottom: 12px; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
  .msg.user { background: #dcf8c6; align-self: flex-end; margin-left: auto; border-bottom-right-radius: 4px; }
  .msg.assistant { background: #fff; align-self: flex-start; margin-right: auto; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
  .msg .time { font-size: 11px; color: #999; margin-top: 4px; text-align: right; }
  .empty-state { display: flex; flex: 1; align-items: center; justify-content: center; color: #999; font-size: 14px; }
  #messages-container { display: flex; flex-direction: column; }

  /* Agents tab */
  .agent-toolbar { padding: 16px; display: flex; justify-content: flex-end; border-bottom: 1px solid #e0e0e0; }
  .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
  .btn-primary { background: #1976d2; color: #fff; }
  .btn-primary:hover { background: #1565c0; }
  .btn-danger { background: #ef4444; color: #fff; }
  .btn-danger:hover { background: #dc2626; }
  .btn-success { background: #16a34a; color: #fff; }
  .btn-success:hover { background: #15803d; }
  .btn-sm { padding: 4px 12px; font-size: 12px; }
  .btn-outline { background: transparent; border: 1px solid #ccc; color: #333; }
  .btn-outline:hover { background: #f5f5f5; }
  .agent-grid { padding: 16px; overflow-y: auto; flex: 1; display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 12px; align-content: start; }
  .agent-card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 16px; }
  .agent-card h3 { font-size: 15px; margin-bottom: 4px; }
  .agent-card .sub { font-size: 12px; color: #666; margin-bottom: 8px; }
  .agent-card .prompt-preview { font-size: 13px; color: #333; background: #f9f9f9; border-radius: 4px; padding: 8px; margin-bottom: 10px; max-height: 60px; overflow: hidden; }
  .agent-card .actions { display: flex; gap: 8px; }
  .agent-card .badge { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #e3f2fd; color: #1976d2; margin-right: 4px; }

  /* Modal */
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); align-items: center; justify-content: center; z-index: 100; }
  .modal-overlay.open { display: flex; }
  .modal { background: #fff; border-radius: 12px; padding: 24px; width: 560px; max-width: 90vw; max-height: 85vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
  .modal h2 { font-size: 18px; margin-bottom: 16px; }
  .form-group { margin-bottom: 12px; }
  .form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px; color: #333; }
  .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; font-family: inherit; }
  .form-group textarea { min-height: 100px; resize: vertical; }
  .form-row { display: flex; gap: 12px; }
  .form-row .form-group { flex: 1; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
  .tool-switch { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
  .tool-switch:last-child { border-bottom: none; }
  .tool-switch label { font-size: 14px; cursor: pointer; }
  .switch { position: relative; width: 40px; height: 22px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .switch .slider { position: absolute; inset: 0; background: #ccc; border-radius: 22px; cursor: pointer; transition: 0.2s; }
  .switch .slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 2px; bottom: 2px; background: #fff; border-radius: 50%; transition: 0.2s; }
  .switch input:checked + .slider { background: #1976d2; }
  .switch input:checked + .slider::before { transform: translateX(18px); }
  .hidden { display: none !important; }
</style>
</head>
<body>
<div style="display:flex;flex-direction:column;width:100%;">
<div class="tabs">
  <div class="tab active" onclick="switchTab('conversaciones')" id="tab-conversaciones">Conversaciones</div>
  <div class="tab" onclick="switchTab('agentes')" id="tab-agentes">Agentes</div>
</div>

<div class="layout">
  <!-- Sidebar (conversaciones) -->
  <div class="sidebar" id="conv-sidebar">
    <div class="sidebar-header">
      <h2>Conversaciones</h2>
      <select id="client-select" onchange="loadConversations()">
        <option value="">Seleccionar cliente...</option>
      </select>
    </div>
    <div class="conv-list" id="conv-list"></div>
  </div>

  <div class="main">
    <!-- Conversaciones view -->
    <div id="conv-view">
      <div class="main-header">
        <h2 id="conv-title">Seleccioná una conversación</h2>
        <button class="btn btn-danger" id="btn-reset" style="display:none" onclick="deleteConversation()">Resetear</button>
      </div>
      <div class="messages" id="messages-container">
        <div class="empty-state">Seleccioná un cliente y una conversación</div>
      </div>
    </div>

    <!-- Agentes view -->
    <div id="agents-view" class="hidden">
      <div class="agent-toolbar">
        <button class="btn btn-primary" onclick="openAgentForm()">+ Nuevo agente</button>
      </div>
      <div class="agent-grid" id="agent-grid">
        <div class="empty-state">Cargando agentes...</div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="agent-modal">
  <div class="modal">
    <h2 id="modal-title">Nuevo agente</h2>
    <input type="hidden" id="agent-id">
    <div class="form-group">
      <label>Nombre</label>
      <input id="f-name" placeholder="Ej: Demo Client">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>ID del cliente</label>
        <input id="f-client-id" placeholder="Ej: demo">
      </div>
      <div class="form-group">
        <label>Phone Number ID</label>
        <input id="f-phone" placeholder="Ej: 1188097807719916">
      </div>
    </div>
    <div class="form-group">
      <label>System Prompt</label>
      <textarea id="f-prompt" placeholder="Eres un asistente útil..."></textarea>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Modelo</label>
        <select id="f-model">
          <option value="gemini-2.5-flash">gemini-2.5-flash</option>
          <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</option>
        </select>
      </div>
      <div class="form-group">
        <label>Temperature</label>
        <input id="f-temp" type="number" step="0.1" min="0" max="2" value="0.7">
      </div>
    </div>
    <div class="form-group">
      <label>Tools</label>
      <div id="f-tools"></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeAgentForm()">Cancelar</button>
      <button class="btn btn-success" onclick="saveAgent()">Guardar</button>
    </div>
  </div>
</div>

<script>
let selectedClientId = '';
let selectedConvId = '';

// --- Tabs ---
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.getElementById('conv-sidebar').classList.toggle('hidden', tab !== 'conversaciones');
  document.getElementById('conv-view').classList.toggle('hidden', tab !== 'conversaciones');
  document.getElementById('agents-view').classList.toggle('hidden', tab !== 'agentes');
  if (tab === 'agentes') loadAgents();
  if (tab === 'conversaciones') loadClientSelect();
}

// --- Conversaciones ---
async function loadClientSelect() {
  const r = await fetch('/api/clients');
  const clients = await r.json();
  const sel = document.getElementById('client-select');
  sel.innerHTML = '<option value="">Seleccionar cliente...</option>';
  clients.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name + ' (' + c.phone_number_id + ')';
    sel.appendChild(opt);
  });
}

async function loadConversations() {
  selectedClientId = document.getElementById('client-select').value;
  const list = document.getElementById('conv-list');
  const container = document.getElementById('messages-container');
  selectedConvId = '';
  document.getElementById('btn-reset').style.display = 'none';
  document.getElementById('conv-title').textContent = 'Seleccioná una conversación';
  container.innerHTML = '<div class="empty-state">Seleccioná una conversación</div>';
  if (!selectedClientId) { list.innerHTML = ''; return; }
  const r = await fetch('/api/clients/' + selectedClientId + '/conversations');
  const convs = await r.json();
  list.innerHTML = '';
  convs.forEach(c => {
    const div = document.createElement('div');
    div.className = 'conv-item';
    div.innerHTML = '<div class="phone">' + c.phone_number + '</div>' +
      '<div class="preview">' + (c.last_message || 'Sin mensajes') + '</div>' +
      '<div class="meta">' + c.message_count + ' msgs</div>';
    div.onclick = (e) => loadMessages(c.id, e);
    list.appendChild(div);
  });
}

async function loadMessages(convId, event) {
  selectedConvId = convId;
  document.getElementById('btn-reset').style.display = '';
  document.getElementById('conv-title').textContent = 'Conversación';
  document.querySelectorAll('.conv-item').forEach(el => el.classList.remove('active'));
  if (event && event.currentTarget) event.currentTarget.classList.add('active');
  const r = await fetch('/api/conversations/' + convId + '/messages?client_id=' + selectedClientId);
  const msgs = await r.json();
  const container = document.getElementById('messages-container');
  container.innerHTML = '';
  msgs.forEach(m => {
    const div = document.createElement('div');
    div.className = 'msg ' + m.role;
    div.innerHTML = '<div>' + m.content + '</div><div class="time">' + (m.created_at ? new Date(m.created_at).toLocaleString() : '') + '</div>';
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

async function deleteConversation() {
  if (!confirm('¿Resetear esta conversación?')) return;
  const r = await fetch('/api/conversations/' + selectedConvId + '?client_id=' + selectedClientId, { method: 'DELETE' });
  if (r.ok) loadConversations();
  else alert('Error');
}

// --- Agentes ---
async function loadAgents() {
  const grid = document.getElementById('agent-grid');
  try {
    const r = await fetch('/api/clients');
    const agents = await r.json();
    grid.innerHTML = '';
    if (agents.length === 0) {
      grid.innerHTML = '<div class="empty-state">No hay agentes. Creá uno.</div>';
      return;
    }
    agents.forEach(a => {
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML =
        '<h3>' + (a.name || a.id) + '</h3>' +
        '<div class="sub">ID: ' + a.id + ' &middot; Phone: ' + a.phone_number_id + '</div>' +
        '<div class="prompt-preview">' + (a.system_prompt || 'Sin prompt') + '</div>' +
        '<div class="sub">' + a.conv_count + ' conversaciones &middot; Modelo: ' + a.model_name + '</div>' +
        '<div class="actions" style="margin-top:8px"></div>';

      const actions = card.querySelector('.actions');
      const editBtn = document.createElement('button');
      editBtn.className = 'btn btn-primary btn-sm';
      editBtn.textContent = 'Editar';
      editBtn.addEventListener('click', () => openAgentForm(a.id));
      actions.appendChild(editBtn);

      const delBtn = document.createElement('button');
      delBtn.className = 'btn btn-danger btn-sm';
      delBtn.textContent = 'Borrar';
      delBtn.addEventListener('click', () => deleteAgent(a.id));
      actions.appendChild(delBtn);

      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<div class="empty-state">Error al cargar agentes</div>';
  }
}

async function openAgentForm(clientId) {
  document.getElementById('modal-title').textContent = clientId ? 'Editar agente' : 'Nuevo agente';
  document.getElementById('agent-id').value = clientId || '';
  document.getElementById('f-name').value = '';
  document.getElementById('f-client-id').value = '';
  document.getElementById('f-phone').value = '';
  document.getElementById('f-prompt').value = '';
  document.getElementById('f-model').value = 'gemini-2.5-flash';
  document.getElementById('f-temp').value = '0.7';
  document.getElementById('f-client-id').disabled = !!clientId;
  document.getElementById('f-tools').innerHTML = '';

  if (clientId) {
    const r = await fetch('/api/clients/' + clientId);
    const data = await r.json();
    document.getElementById('f-name').value = data.name || '';
    document.getElementById('f-client-id').value = data.id || '';
    document.getElementById('f-phone').value = data.phone_number_id || '';
    document.getElementById('f-prompt').value = data.system_prompt || '';
    document.getElementById('f-model').value = data.model_name || 'gemini-2.5-flash';
    document.getElementById('f-temp').value = data.temperature ?? '0.7';
  }

  // Load tools
  try {
    const tr = await fetch('/api/tools/registry');
    const tools = await tr.json();
    const toolsDiv = document.getElementById('f-tools');
    toolsDiv.innerHTML = '';
    tools.forEach(t => {
      const div = document.createElement('div');
      div.className = 'tool-switch';

      const label = document.createElement('label');
      label.innerHTML = t.name + ' <span style="font-size:12px;color:#666">' + (t.description || '') + '</span>';
      div.appendChild(label);

      const switchLabel = document.createElement('label');
      switchLabel.className = 'switch';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.addEventListener('change', function() { toggleTool(clientId, t.name, this.checked); });
      switchLabel.appendChild(cb);
      const slider = document.createElement('span');
      slider.className = 'slider';
      switchLabel.appendChild(slider);
      div.appendChild(switchLabel);

      toolsDiv.appendChild(div);
    });
  } catch (e) {}

  document.getElementById('agent-modal').classList.add('open');
}

function closeAgentForm() {
  document.getElementById('agent-modal').classList.remove('open');
}

async function saveAgent() {
  const clientId = document.getElementById('agent-id').value;
  const isNew = !clientId;
  const data = {
    name: document.getElementById('f-name').value,
    phone_number_id: document.getElementById('f-phone').value,
    system_prompt: document.getElementById('f-prompt').value,
    model_name: document.getElementById('f-model').value,
  };

  if (isNew) {
    data.client_id = document.getElementById('f-client-id').value;
    const r = await fetch('/api/clients', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    if (!r.ok) { alert('Error al crear'); return; }
  } else {
    const r = await fetch('/api/clients/' + clientId, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    if (!r.ok) { alert('Error al actualizar'); return; }
  }
  closeAgentForm();
  loadAgents();
  loadClientSelect();
}

async function deleteAgent(clientId) {
  if (!confirm('¿Eliminar este agente? Se borrarán también sus conversaciones.')) return;
  const r = await fetch('/api/clients/' + clientId, { method: 'DELETE' });
  if (r.ok) { loadAgents(); loadClientSelect(); }
  else alert('Error al eliminar');
}

async function toggleTool(clientId, toolId, enabled) {
  if (!clientId) return;
  await fetch('/api/clients/' + clientId + '/tools/' + toolId + '?enabled=' + enabled, { method: 'PUT' });
}

// Init
loadClientSelect();
</script>
</body>
</html>
"""
