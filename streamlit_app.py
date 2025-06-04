import streamlit as st
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar a classe com fallback
try:
    from src.lead_generator.crew import LeadGenerator, is_crewai_available, get_import_error
except ImportError as e:
    st.error(f"Erro ao importar módulo: {e}")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Lead Generator AI",
    page_icon="🎯",
    layout="wide"
)

# Título principal
st.title("🎯 Lead Generator AI")
st.markdown("Gerador inteligente de leads usando IA")

# Verificar status do CrewAI
if not is_crewai_available():
    st.error("⚠️ Sistema em modo limitado")
    st.warning(f"CrewAI indisponível: {get_import_error()}")
    st.info("Algumas funcionalidades podem estar limitadas.")
    
    # Ainda permitir uso limitado
    with st.expander("🔍 Detalhes técnicos"):
        st.code(get_import_error())
        st.markdown("""
        **Possíveis soluções:**
        - Verifique se todas as dependências estão instaladas
        - Aguarde alguns minutos e recarregue a página
        - Entre em contato com o suporte técnico
        """)

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Status do sistema
    if is_crewai_available():
        st.success("✅ Sistema funcionando")
    else:
        st.error("❌ Sistema limitado")
    
    # API Key check (se necessário)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("🔑 API Key configurada")
    else:
        st.warning("🔑 API Key não encontrada")

# Interface principal
st.header("📝 Gerar Leads")

# Formulário de entrada
with st.form("lead_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input(
            "🎯 Tópico/Indústria",
            placeholder="Ex: Empresas de tecnologia em São Paulo",
            help="Descreva o tipo de empresa ou setor que você está procurando"
        )
    
    with col2:
        max_leads = st.number_input(
            "📊 Número de leads",
            min_value=1,
            max_value=10,
            value=3,
            help="Quantos leads você gostaria de gerar?"
        )
    
    additional_info = st.text_area(
        "ℹ️ Informações adicionais",
        placeholder="Ex: Foco em empresas com mais de 100 funcionários...",
        help="Qualquer critério específico ou informação adicional"
    )
    
    submitted = st.form_submit_button("🚀 Gerar Leads", type="primary")

# Processamento
if submitted:
    if not topic:
        st.error("❌ Por favor, insira um tópico para busca")
    else:
        # Preparar inputs
        inputs = {
            "topic": topic,
            "max_leads": max_leads,
            "additional_info": additional_info
        }
        
        # Mostrar status
        if not is_crewai_available():
            st.warning("⚠️ Executando em modo limitado")
        
        # Executar geração de leads
        with st.spinner("🔍 Gerando leads... Isso pode levar alguns minutos"):
            try:
                # Inicializar gerador
                generator = LeadGenerator()
                
                # Executar
                result = generator.run(inputs)
                
                # Mostrar resultados
                st.success("✅ Leads gerados com sucesso!")
                
                # Exibir resultado
                if hasattr(result, 'company_name'):
                    # Resultado estruturado
                    st.subheader("📋 Resultado")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🏢 Empresa", result.company_name or "N/A")
                        if result.website_url:
                            st.link_button("🌐 Website", result.website_url)
                    
                    with col2:
                        st.metric("💰 Receita", result.annual_revenue or "N/A")
                        st.metric("👥 Funcionários", result.num_employees or "N/A")
                    
                    with col3:
                        score = result.score or 0
                        st.metric("⭐ Score", f"{score}/10")
                        
                        # Cor baseada no score
                        if score >= 8:
                            st.success("🎯 Lead excelente!")
                        elif score >= 6:
                            st.info("👍 Lead promissor")
                        else:
                            st.warning("⚠️ Lead para análise")
                    
                    # Descrição
                    if result.review:
                        st.subheader("📝 Descrição")
                        st.write(result.review)
                    
                    # Localização
                    if result.location:
                        st.subheader("📍 Localização")
                        location = result.location
                        st.write(f"**Cidade:** {location.get('city', 'N/A')}")
                        st.write(f"**País:** {location.get('country', 'N/A')}")
                    
                    # Contatos importantes
                    if result.key_decision_makers:
                        st.subheader("👥 Contatos-chave")
                        for contact in result.key_decision_makers:
                            with st.expander(f"👤 {contact.get('name', 'N/A')}"):
                                st.write(f"**Cargo:** {contact.get('position', 'N/A')}")
                                if contact.get('linkedin'):
                                    st.link_button("🔗 LinkedIn", contact['linkedin'])
                
                else:
                    # Resultado como texto
                    st.subheader("📋 Resultado")
                    st.write(result)
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar leads: {str(e)}")
                
                if not is_crewai_available():
                    st.info("💡 Este erro pode estar relacionado às limitações do modo atual")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🎯 Lead Generator AI - Powered by CrewAI & Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Debug info (apenas em desenvolvimento)
if st.checkbox("🐛 Mostrar informações de debug"):
    st.subheader("🔧 Debug Info")
    st.json({
        "crewai_available": is_crewai_available(),
        "import_error": get_import_error(),
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "environment_vars": list(os.environ.keys())
    })
