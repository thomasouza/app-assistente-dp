# pages/2_Menu_Principal.py - Versão Simplificada

import streamlit as st
from helpers import load_css

load_css("style.css")

# Guarda de Segurança
if not st.session_state.get('logged_in', False):
    # Se o usuário não está logado, redireciona para a página de login
    st.switch_page("Login.py")

# Conteúdo da Página
st.title(f"Bem-vindo(a), {st.session_state.get('matricula', '')}! 👋")
st.markdown("#### Ferramenta de Assistência de Respostas para o DP")
st.write("") 

# Botão único que leva direto para a ferramenta principal
if st.button("🚀 Iniciar Atendimento", use_container_width=True, type="primary"):
    st.session_state.current_topic = "Geral" 
    st.switch_page("pages/Chat.py")

st.markdown("---")
if st.button("Sair da Sessão"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("Login.py")
