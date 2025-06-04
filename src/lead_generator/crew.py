import os
import sys
from typing import List, Dict, Optional

# Configuração específica para Streamlit Cloud
os.environ["ALLOW_RESET"] = "TRUE"
os.environ["CHROMA_SERVER_HOST"] = "localhost"
os.environ["CHROMA_SERVER_PORT"] = "8000"
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

# Verificar se está no Streamlit
IS_STREAMLIT = 'streamlit' in sys.modules or 'streamlit' in str(sys.argv)

# Tentar importar CrewAI
CREWAI_AVAILABLE = False
IMPORT_ERROR = None

try:
    from crewai import Agent, Crew, Process, Task
    from crewai.project import CrewBase, agent, crew, task
    from crewai_tools import SerperDevTool, ScrapeWebsiteTool
    CREWAI_AVAILABLE = True
    print("✅ CrewAI importado com sucesso!")
except Exception as e:
    IMPORT_ERROR = str(e)
    print(f"❌ Erro ao importar CrewAI: {e}")
    
    # Se estiver no Streamlit, importar para mostrar erro na interface
    if IS_STREAMLIT:
        try:
            import streamlit as st
        except ImportError:
            pass

# Imports sempre disponíveis
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Carregar variáveis de ambiente
load_dotenv()

# Schema sempre disponível
class LeadOutput(BaseModel):
    company_name: Optional[str] = Field(description="The name of the company")
    annual_revenue: Optional[str] = Field(description="Annual revenue of the company")
    location: Optional[Dict[str, str]] = Field(description="Location with city and country fields")
    website_url: Optional[str] = Field(description="Company website URL")
    review: Optional[str] = Field(description="Description of what the company does")
    num_employees: Optional[int] = Field(description="Number of employees")
    key_decision_makers: Optional[List[Dict[str, str]]] = Field(description="List of key people with their LinkedIn profiles")
    score: Optional[int] = Field(description="Fit score on a scale of 1-10")

# Tools (apenas se CrewAI estiver disponível)
if CREWAI_AVAILABLE:
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool()

# Classe principal com fallback
if CREWAI_AVAILABLE:
    @CrewBase
    class LeadGenerator():
        """LeadGenerator crew"""
        agents_config = 'config/agents.yaml'
        tasks_config = 'config/tasks.yaml'
        
        def __init__(self):
            self.fallback_mode = False
            super().__init__()
        
        @agent
        def lead_generator(self) -> Agent:
            return Agent(
                config=self.agents_config['lead_generator'],
                tools=[search_tool, scrape_tool],
                verbose=True
            )
        
        @agent
        def contact_agent(self) -> Agent:
            return Agent(
                config=self.agents_config['contact_agent'],
                tools=[search_tool, scrape_tool],
                verbose=True
            )
        
        @agent 
        def lead_qualifier(self) -> Agent:
            return Agent(
                config=self.agents_config['lead_qualifier'],
                verbose=True
            )	
        
        @agent
        def sales_manager(self) -> Agent:
            return Agent(
                config=self.agents_config['sales_manager'],
                tools=[],
                verbose=True
            )	
        
        @task
        def lead_generation_task(self) -> Task:
            return Task(
                config=self.tasks_config['lead_generation_task'],
                output_pydantic=LeadOutput
            )
        
        @task
        def contact_research_task(self) -> Task:
            return Task(
                config=self.tasks_config['contact_research_task'],
                context=[self.lead_generation_task()],
            )
        
        @task
        def lead_qualification_task(self) -> Task:
            return Task(
                config=self.tasks_config['lead_qualification_task'],
                context=[self.lead_generation_task(), self.contact_research_task()],
                output_pydantic=LeadOutput,
            )
        
        @task
        def sales_management_task(self) -> Task:
            return Task(
                config=self.tasks_config['sales_management_task'],
                context=[self.lead_generation_task(), self.lead_qualification_task(), self.contact_research_task()],
                output_pydantic=LeadOutput
            )
        
        @crew
        def crew(self) -> Crew:
            """Creates the LeadGenerator crew"""
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                usage_metrics={}
            )
        
        def run(self, inputs: dict):
            """Executa o crew com os inputs fornecidos"""
            try:
                return self.crew().kickoff(inputs=inputs)
            except Exception as e:
                print(f"Erro ao executar crew: {e}")
                return self._fallback_response(inputs)
        
        def _fallback_response(self, inputs: dict) -> LeadOutput:
            """Resposta de fallback quando há erro"""
            return LeadOutput(
                company_name="Erro na geração",
                review=f"Houve um erro ao processar a solicitação: {inputs.get('topic', 'N/A')}",
                score=0
            )

else:
    # Classe de fallback quando CrewAI não está disponível
    class LeadGenerator:
        """LeadGenerator fallback class"""
        
        def __init__(self):
            self.fallback_mode = True
            self._show_error_if_streamlit()
        
        def _show_error_if_streamlit(self):
            """Mostra erro no Streamlit se aplicável"""
            if IS_STREAMLIT:
                try:
                    import streamlit as st
                    st.error("⚠️ CrewAI não está disponível neste ambiente")
                    st.info("A aplicação está rodando em modo limitado")
                    st.code(f"Erro técnico: {IMPORT_ERROR}")
                    st.warning("Por favor, verifique as dependências do projeto")
                except ImportError:
                    pass
        
        def run(self, inputs: dict) -> LeadOutput:
            """Execução em modo fallback"""
            return LeadOutput(
                company_name="Modo Limitado",
                review=f"CrewAI indisponível. Tópico solicitado: {inputs.get('topic', 'N/A')}",
                score=0,
                location={"city": "N/A", "country": "N/A"}
            )
        
        def crew(self):
            """Crew mockado"""
            return None

# Função utilitária para verificar disponibilidade
def is_crewai_available() -> bool:
    """Retorna True se CrewAI está disponível"""
    return CREWAI_AVAILABLE

def get_import_error() -> Optional[str]:
    """Retorna o erro de importação, se houver"""
    return IMPORT_ERROR

# Exemplo de uso
if __name__ == "__main__":
    print(f"CrewAI disponível: {CREWAI_AVAILABLE}")
    if not CREWAI_AVAILABLE:
        print(f"Erro: {IMPORT_ERROR}")
    
    # Teste básico
    generator = LeadGenerator()
    print(f"Modo fallback: {generator.fallback_mode}")

	
