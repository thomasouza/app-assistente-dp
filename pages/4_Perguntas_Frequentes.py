import streamlit as st
from helpers import load_css, carregar_base_conhecimento

# Carrega o CSS e verifica o login
load_css("style.css")
if not st.session_state.get('logged_in', False):
    st.switch_page("Login.py")

# --- CONTEÚDO DA PÁGINA DE FAQ ---
st.header("Perguntas Frequentes (FAQ)")

if st.button("⬅️ Voltar ao Menu"):
    st.switch_page("pages/2_Menu_Principal.py")

st.markdown("Encontre aqui respostas rápidas para as dúvidas mais comuns, separadas por tópico.")

base_conhecimento = carregar_base_conhecimento()

if base_conhecimento:
    for topico, df_topico in base_conhecimento.items():
        with st.expander(f"**Tópico: {topico}**"):
            if not df_topico.empty:
                for index, row in df_topico.iterrows():
                    st.markdown(f"**P:** {row['Pergunta']}")
                    st.write(f"R: {row['Resposta_Oficial']}")
                    st.markdown("---")
            else:
                st.write("Nenhuma pergunta encontrada para este tópico.")
else:
    st.warning("Não foi possível carregar o FAQ no momento.")
