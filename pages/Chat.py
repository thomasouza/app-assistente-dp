import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model,
    carregar_empresas
)

# --- CONFIGURAÇÃO E VERIFICAÇÃO ---
st.set_page_config(layout="centered", initial_sidebar_state="collapsed")
load_css("style.css")

if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# --- DADOS E MODELO ---
base_conhecimento = carregar_base_conhecimento()
model = get_gemini_model()
lista_de_empresas = carregar_empresas()

# --- TELA PRINCIPAL DA FERRAMENTA ---
st.title("Assistente de Respostas do DP")
st.markdown("Use esta ferramenta para gerar respostas padronizadas e precisas para as dúvidas dos colaboradores.")
st.divider()


# --- SEÇÃO DE INPUTS ---
with st.container(border=True):
    st.subheader("1. Detalhes do Chamado")
    
    col1, col2 = st.columns(2)
    with col1:
        colaborador_solicitante = st.text_input("Nome do Colaborador que perguntou:")

    with col2:
        # NOVIDADE: Trocado st.text_input por st.selectbox
        # Adiciona uma opção em branco no início
        opcoes_empresa = ["Selecione uma empresa..."] + lista_de_empresas
        empresa_solicitante = st.selectbox("Empresa do Colaborador:", options=opcoes_empresa)

    # NOVIDADE: Trocado "Chat Comum" por "Discord"
    canal_comunicacao = st.radio(
        "Selecione o canal da resposta:",
        ["💬 Discord", "📧 E-mail", "📱 WhatsApp"],
        horizontal=True
    )
    
    if base_conhecimento:
        topicos = list(base_conhecimento.keys())
        agente_selecionado = st.selectbox(
            "Selecione o assunto da dúvida (Agente Especialista):", 
            topicos, 
            index=topicos.index("Geral") if "Geral" in topicos else 0
        )
    else:
        agente_selecionado = None

    pergunta_colaborador = st.text_area("Copie e cole aqui a pergunta do colaborador:", height=100)

# --- BOTÃO DE AÇÃO E LÓGICA DA IA ---
if st.button("🤖 Gerar Resposta Sugerida", use_container_width=True, type="primary"):
    # Adicionada validação para o novo campo de seleção
    if empresa_solicitante == "Selecione uma empresa...":
        st.warning("Por favor, selecione a empresa do colaborador.")
    elif base_conhecimento and model:
        with st.spinner("Vivi está personalizando a resposta..."):
            try:
                df_topico = base_conhecimento[agente_selecionado]
                contexto = "\n".join([f"P: {row['Pergunta']}\nR: {row['Resposta_Oficial']}" for _, row in df_topico.iterrows()])
                
                # NOVIDADE: Adicionada instrução para o formato Discord
                instrucao_canal = ""
                if canal_comunicacao == "📧 E-mail":
                    instrucao_canal = "Formate a resposta como um e-mail profissional, começando com 'Prezado(a) {nome_solicitante},' e terminando com 'Atenciosamente, Equipe de DP.'."
                elif canal_comunicacao == "📱 WhatsApp":
                    instrucao_canal = "Formate a resposta para WhatsApp, usando texto em negrito (*texto*) e quebras de linha curtas para melhor leitura. Seja um pouco mais informal, mas ainda profissional."
                elif canal_comunicacao == "💬 Discord":
                    instrucao_canal = "Formate a resposta para Discord. Use markdown do Discord como **para negrito** e *para itálico*. Mantenha a linguagem amigável e use emojis onde for apropriado."

          # CÓDIGO NOVO DO PROMPT (MAIS SEGURO)
prompt_para_ia = (
    f"Você é um assistente de DP. Sua única função é responder à pergunta do colaborador com base estritamente no CONTEXTO fornecido. "
    f"Adapte a formatação da resposta para o canal '{canal_comunicacao}', direcionando-a para '{nome_solicitante}'.\n"
    f"**REGRA CRÍTICA:** Se a resposta para a pergunta não estiver claramente no CONTEXTO, você deve responder EXATAMENTE e APENAS com a frase: 'Resposta não disponível na minha base de conhecimento.'\n"
    f"Não invente, deduza ou use conhecimento externo.\n\n"
    f"CONTEXTO:\n{contexto}\n\n"
    f"PERGUNTA DO COLABORADOR: {pergunta_colaborador}\n\n"
    f"RESPOSTA GERADA:"
)
                
                resposta_texto = model.generate_content(prompt_para_ia).text
                
                st.session_state.ultima_resposta = resposta_texto
                st.session_state.ultima_pergunta = pergunta_colaborador
                st.session_state.dados_solicitante = {"nome": colaborador_solicitante, "empresa": empresa_solicitante}

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a resposta: {e}")
                st.session_state.ultima_resposta = None

# --- EXIBIÇÃO DA RESPOSTA E SISTEMA DE AVALIAÇÃO ---
if 'ultima_resposta' in st.session_state and st.session_state.ultima_resposta:
    st.divider()
    st.subheader("3. Resposta Sugerida pela IA")
    
    # Este é o bloco que trocamos, agora com a indentação correta para o que vem depois
    st.text_area(
        label="Copia a resposta sugerida abaixo:",
        value=st.session_state.ultima_resposta,
        height=200,
        disabled=True,
        label_visibility="visible"
    )

    st.divider()

    st.subheader("4. Avaliação e Registro")
    
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = None

    col1, col2 = st.columns(2)
    if col1.button("👍 Resposta Positiva", use_container_width=True):
        st.session_state.feedback_given = "Positiva"
    if col2.button("👎 Resposta Negativa", use_container_width=True):
        st.session_state.feedback_given = "Negativa"

    # Garante que o estado do comentário seja gerenciado corretamente
    if st.session_state.feedback_given == "Negativa":
        st.session_state.feedback_comment = st.text_area(
            "O que pode ser melhorado? (Obrigatório para avaliação negativa)", 
            key="feedback_comment_input"
        )
    else:
        # Garante que o comentário seja limpo se a avaliação for positiva
        st.session_state.feedback_comment = ""
    
    if st.session_state.feedback_given:
        # Validação para garantir que o comentário negativo não esteja vazio
        if st.session_state.feedback_given == "Negativa" and not st.session_state.get('feedback_comment'):
            st.warning("Por favor, descreva o motivo da avaliação negativa antes de registrar.")
        else:
            # CÓDIGO NOVO DO BOTÃO DE SALVAR (COM APRENDIZADO)
if st.session_state.feedback_given:
    if st.session_state.feedback_given == "Negativa" and not st.session_state.get('feedback_comment'):
        st.warning("Por favor, descreva a resposta correta ou o motivo da avaliação negativa antes de registrar.")
    else:
        if st.button("Salvar Avaliação e Registrar Log", use_container_width=True, type="primary"):
            with st.spinner("Salvando registro e aprendizado..."):
                
                # Salva o log normal
                sucesso_log = salvar_log(
                    matricula_dp=st.session_state.get('matricula'),
                    nome_colaborador=st.session_state.dados_solicitante['nome'],
                    empresa=st.session_state.dados_solicitante['empresa'],
                    pergunta=st.session_state.get('ultima_pergunta'),
                    resposta=st.session_state.get('ultima_resposta'),
                    avaliacao=st.session_state.feedback_given,
                    comentario=st.session_state.get('feedback_comment', "")
                )
                
                # Se a avaliação foi negativa, salva o aprendizado na outra planilha
                if st.session_state.feedback_given == "Negativa":
                    sucesso_aprendizado = salvar_aprendizado(
                        assunto=st.session_state.get('agente_usado', agente_selecionado),
                        pergunta=st.session_state.get('ultima_pergunta'),
                        resposta_ia=st.session_state.get('ultima_resposta'),
                        comentario_humano=st.session_state.get('feedback_comment')
                    )
                    # Limpa o cache para que a IA leia o novo aprendizado na próxima vez
                    if sucesso_aprendizado:
                        st.cache_data.clear()
                
                if sucesso_log:
                    st.success("Atendimento registrado e feedback salvo com sucesso!")
                else:
                    st.error("Falha ao registrar o log do atendimento.")

                # Limpa os dados para o próximo atendimento
                for key in ['ultima_resposta', 'ultima_pergunta', 'dados_solicitante', 'feedback_given', 'feedback_comment', 'agente_usado']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Sair da Sessão", use_container_width=True):
    st.session_state.clear()
    st.switch_page("Login.py")
