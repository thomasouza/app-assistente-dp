import streamlit as st
from helpers import verificar_login, carregar_acessos
import base64

# --- CONFIGURAÇÃO DA PÁGINA DE LOGIN ---
st.set_page_config(
    page_title="Login - Assistente VIVA",
    page_icon="img/quokka_logo.png",
    layout="centered"
)

# --- CSS Específico para a Página de Login ---
login_page_css = f"""
<style>
    /* Esconde o cabeçalho e a barra lateral para uma tela de login imersiva */
    [data-testid="stHeader"], [data-testid="stSidebar"] {{
        display: none;
    }}
    /* Fundo da página */
    [data-testid="stAppViewContainer"] > .main {{
        background-color: #F0F2F5; /* Fundo cinza claro */
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100vw;
        height: 100vh;
    }}
    
    /* Card de Login */
    .login-card {{
        background-color: white;
        padding: 2.5rem;
        border-radius: 10px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        width: 100%;
        max-width: 400px;
        text-align: center;
    }}
    /* Centraliza a imagem do logo */
    .login-card img {{
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 1.5rem;
    }}
    /* Diminui o espaçamento entre os campos de Matrícula e Senha */
    .login-card div[data-testid="stTextInput"] {{
        margin-bottom: 0.5rem;
    }}
    /* Estiliza o botão de entrar */
    .login-card .stButton>button {{
        margin-top: 1rem;
    }}
</style>
"""
st.markdown(login_page_css, unsafe_allow_html=True)


# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.matricula = ""
    st.session_state.messages = {}

# --- LÓGICA DA PÁGINA DE LOGIN ---
df_acessos = carregar_acessos()

# Colunas para ajudar na centralização
col1, col2, col3 = st.columns([1, 1.2, 1])
with col2:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    try:
        st.image("img/quokka_logo.png", width=150)
    except FileNotFoundError:
        st.title("VIVA Company")

    st.subheader("Acesse sua conta")
    
    matricula_input = st.text_input("Matrícula", label_visibility="collapsed", placeholder="Matrícula", key="login_matricula")
    senha_input = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Senha", key="login_senha")
    
    if st.button("Entrar", use_container_width=True, type="primary"):
        if df_acessos is None:
            st.error("Sistema de login indisponível.")
        elif verificar_login(matricula_input, senha_input, df_acessos):
            st.session_state.logged_in = True
            st.session_state.matricula = matricula_input
            st.switch_page("pages/2_Menu_Principal.py")
        else:
            st.error("Matrícula ou senha incorreta.")

    st.markdown('</div>', unsafe_allow_html=True)