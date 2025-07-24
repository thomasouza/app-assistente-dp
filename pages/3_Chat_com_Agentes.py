import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model
)

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
load_css("style.css")

if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página."); st.stop()

base_conhecimento = carregar_base_conhecimento()
model = get_gemini_model()

WELCOME_MESSAGES = {
    "Geral": "Olá! Sou a Vivi, e vou te ajudar com as dúvidas que você tem na nossa empresa relacionadas a departamento pessoal. Caso queira tirar dúvidas mais específicas, temos outros especialistas disponíveis.",
    "Salário": "Olá! Sou a especialista em Salários. Posso te ajudar com dúvidas sobre seu holerite, pagamentos e descontos.",
    "Ponto": "Oi! Sou a especialista em Ponto. Se sua dúvida é sobre banco de horas ou marcações, estou aqui para ajudar.",
    "Plano de Saúde": "Bem-vindo(a)! Sou a especialista em Planos de Saúde. Como posso te auxiliar com seu convênio?"
}

# Lógica para atualizar o agente via clique (usando query params, uma técnica web padrão)
query_params = st.query_params
if "topic" in query_params:
    st.session_state.current_topic = query_params["topic"]
    st.query_params.clear()
    st.rerun()

# --- BARRA LATERAL (SIDEBAR) COM NOVO DESIGN ---
with st.sidebar:
    st.markdown(f"Olá, **{st.session_state.get('matricula', '')}**! 👋")
    st.divider()

    st.markdown("##### Agentes Online")
    if base_conhecimento:
        for topico in base_conhecimento.keys():
            card_class = "agent-card selected" if st.session_state.get("current_topic") == topico else "agent-card"
            st.markdown(
                f"""
                <a href="?topic={topico}" target="_self" class="agent-card-link">
                    <div class="{card_class}">
                        <div class="agent-avatar">🤖</div>
                        <div class="agent-info">
                            <div class="agent-name">{topico}</div>
                            <div class="agent-status">Online</div>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True
            )
    
    st.divider()
    st.markdown("##### Histórico de Conversas")
    current_topic = st.session_state.get('current_topic')
    if current_topic and current_topic in st.session_state.get('messages', {}):
        with st.container(height=150):
            for msg in st.session_state.messages[current_topic]:
                if msg["role"] == "user":
                    st.markdown(f"<div class='history-item'>▪️ {msg['content']}</div>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Sair da Sessão", use_container_width=True, key="logout_button"):
        st.session_state.clear(); st.switch_page("1_Login.py")


# --- TELA PRINCIPAL DO CHAT ---
current_topic = st.session_state.get('current_topic')
if not current_topic:
    st.info("Por favor, selecione um agente na barra à esquerda para começar.")
else:
    topic = current_topic
    
    if topic not in st.session_state.get('messages', {}):
        st.session_state.setdefault('messages', {})[topic] = []
        boas_vindas = WELCOME_MESSAGES.get(topic, f"Olá! Sou a especialista em {topic}. Como posso ajudar?")
        st.session_state.messages[topic].insert(0, {"role": "assistant", "content": boas_vindas})

    st.header(f"Conversando com Vivi ❤️, especialista em {topic}")
    for message in st.session_state.messages.get(topic, []):
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua mensagem..."):
        st.session_state.messages[topic].append({"role": "user", "content": prompt})
        
        with st.spinner("Vivi está digitando..."):
            # (Lógica da IA permanece a mesma...)
            if base_conhecimento and model:
                try:
                    # ... (código que gera a resposta da IA)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")