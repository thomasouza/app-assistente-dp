import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model
)

# --- CONFIGURAÇÃO E VERIFICAÇÃO DE LOGIN ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
load_css("style.css")

if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página."); st.stop()

# --- DADOS E MODELO ---
base_conhecimento = carregar_base_conhecimento()
model = get_gemini_model()

# --- MENSAGENS DE BOAS-VINDAS ---
WELCOME_MESSAGES = {
    "Geral": "Olá! Sou a Vivi, sua assistente para dúvidas gerais do DP na VIVA. Como posso te ajudar hoje?",
    "Salário": "Olá! Sou a especialista em Salários da Vivi. Pront@ para falar de pagamentos e holerites?",
    "Ponto": "Oi! Sou a especialista em Ponto da Vivi. Posso ajudar com suas horas, batidas e banco de horas.",
    "Plano de Saúde": "Oi! Sou a especialista em Plano de Saúde da Vivi. Posso ajudar com dúvidas sobre convênio, reembolsos, etc."
}

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"**Usuário:** {st.session_state.get('matricula', '')}")
    st.divider()

    st.page_link("pages/2_Menu_Principal.py", label="⬅️ Voltar ao Menu Principal")
    
    st.markdown("### Agentes Especialistas")
    if base_conhecimento:
        for topico in base_conhecimento.keys():
            if st.button(f"{topico}  🟢", use_container_width=True, key=f"topic_{topico}"):
                st.session_state.current_topic = topico
                st.rerun() # Apenas define o tópico e recarrega, a inicialização será feita na função principal
    
    st.divider()
    
    st.markdown("### Histórico do Agente")
    current_topic = st.session_state.get('current_topic')
    if current_topic and st.session_state.get('messages', {}).get(current_topic):
        with st.container(height=200, border=False):
            for msg in st.session_state.messages[current_topic]:
                if msg["role"] == "user":
                    st.markdown(f"▪️ *{msg['content'][:35]}...*")
    
    st.divider()
    if st.button("Sair da Sessão", use_container_width=True):
        st.session_state.clear()
        st.switch_page("1_Login.py")


# --- FUNÇÃO E LÓGICA PRINCIPAL DO CHAT ---
def exibir_chat(topic: str):
    st.header(f"Conversando com Vivi ❤️, especialista em {topic}")
    
    # Exibe o histórico de mensagens
    for message in st.session_state.messages.get(topic, []):
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        st.session_state.messages[topic].append({"role": "user", "content": prompt})
        
        with st.spinner("Vivi está digitando..."):
            if base_conhecimento and model:
                # (Lógica da IA permanece a mesma)
                df_topico = base_conhecimento[topic]
                contexto = "\n".join([f"P: {row['Pergunta']}\nR: {row['Resposta_Oficial']}" for _, row in df_topico.iterrows()])
                prompt_ia = (f"Você é Vivi, especialista em '{topic}'. Responda de forma natural. Se não souber, encaminhe para um chamado no DP.\n\nContexto:\n{contexto}\n\nPergunta: {prompt}")
                try:
                    response = model.generate_content(prompt_ia)
                    resposta_texto = response.text
                    st.session_state.messages[topic].append({"role": "assistant", "content": resposta_texto})
                    salvar_log(st.session_state.get('matricula', ''), prompt, resposta_texto)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocorreu um erro ao gerar a resposta: {e}")
            else:
                st.error("Modelo de IA ou base de conhecimento não carregados.")

# --- PONTO DE ENTRADA DA PÁGINA ---
# Garante que o estado da sessão esteja sempre pronto
st.session_state.setdefault('messages', {})

# Define 'Geral' como o tópico padrão se nenhum estiver selecionado
if 'current_topic' not in st.session_state or st.session_state.current_topic is None:
    st.session_state.current_topic = 'Geral'

# Pega o tópico atual
topic = st.session_state.current_topic

# Garante que a lista de mensagens para o tópico exista e adiciona boas-vindas se for nova
if topic not in st.session_state.messages:
    st.session_state.messages[topic] = []
    welcome_message = WELCOME_MESSAGES.get(topic, f"Olá! Sou a especialista em {topic}. Como posso te ajudar?")
    st.session_state.messages[topic].append({"role": "assistant", "content": welcome_message})

# Finalmente, exibe o chat
exibir_chat(topic)