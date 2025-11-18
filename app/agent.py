from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.google import Gemini
from dotenv import load_dotenv

load_dotenv()

class TranscriptSummarizer:
    """Classe que encapsula a funcionalidade de resumo usando Agno."""
    
    def __init__(self):
        """Inicializa o summarizer com configurações padrão do Agno."""
        self.client = Agent(
            # model=Groq(id="llama-3.3-70b-versatile"),
            model=Gemini(id="gemini-2.5-flash"),
            name="TranscriptSummarizerAgent",
            instructions="Você é um assistente especializado em criar resumos detalhados e informativos de transcrições de vídeos.",
        )
    
    def summarize(self, text: str) -> str:
        """Gera um resumo do texto fornecido.
        
        Args:
            text: Texto da transcrição para resumir
            
        Returns:
            String com o resumo gerado
        """
        if not text or not text.strip():
            return ""
        
        prompt = f"""
        Por favor, faça um resumo conciso do seguinte texto de transcrição.
        
        Texto para resumir:
        {text}
        
        Resumo:
        """

        try:
            run = self.client.run(prompt)

            if hasattr(run, "content") and isinstance(run.content, str) and run.content.strip():
                return run.content.strip()

            raise ValueError("Resposta vazia do modelo.")
            
        except Exception as e:
            print(f"Erro ao gerar resumo: {e}")
            # Fallback: retorna as primeiras frases do texto original
            sentences = text.split('.')[:3]
            return '. '.join(sentences).strip() + '.'

def create_agent() -> TranscriptSummarizer:
    """Cria uma nova instância do agente de resumo.
    
    Returns:
        Instância do TranscriptSummarizer
    """
    return TranscriptSummarizer()