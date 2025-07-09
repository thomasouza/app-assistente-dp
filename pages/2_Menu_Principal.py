import streamlit as st
from helpers import load_css

# Carrega o CSS customizado
load_css("style.css")

# CSS para esconder o menu apenas nesta página
st.markdown("""
<style>
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# --- VERIFICAÇÃO DE LOGIN (GUARDA DE SEGURANÇA) ---
if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página.")
    st.warning("Por favor, volte para a página de Login.")
    st.stop() # Interrompe a execução da página se não estiver logado

# --- CONTEÚDO DA PÁGINA DE MENU ---

st.title(f"Olá, {st.session_state.get('matricula', '')}! 👋")
st.markdown("#### Como podemos te ajudar hoje?")
st.write("") # Adiciona um espaço vertical

# --- BOTÕES DE NAVEGAÇÃO ---
col1, col2 = st.columns(2)

with col1:
    if st.button("💬 Conversar com um Agente", use_container_width=True):
        st.session_state.current_topic = "Geral" 
        st.switch_page("pages/3_Chat_com_Agentes.py")

with col2:
    if st.button("❓ Ver Perguntas Frequentes", use_container_width=True):
        st.switch_page("pages/4_Perguntas_Frequentes.py")

st.markdown("---")
# Botão de Sair para conveniência
if st.button("Sair da Sessão"):
    # CORREÇÃO APLICADA AQUI: Adicionado o recuo/indentação
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("1_Login.py")