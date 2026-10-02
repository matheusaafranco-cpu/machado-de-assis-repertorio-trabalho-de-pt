import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Inicializa o app FastAPI
app = FastAPI(title="API Quiz Machado de Assis")

# Configuração de CORS para permitir requisições do frontend (HTML/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# Modelo Pydantic para validação do corpo da requisição
class QuizRequest(BaseModel):
    tema: str

@app.get("/")
def health_check():
    """Rota de verificação para saber se a API está online."""
    return {"status": "ok", "message": "API do Quiz do Machado de Assis está operacional!"}

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    # Obtém a chave da API das variáveis de ambiente no Render/Servidor
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Chave de API (GROQ_API_KEY) não encontrada nas variáveis de ambiente."
        )

    try:
        # Cria a instância do cliente Groq
        client = Groq(api_key=api_key)

        prompt_text = (
            f"Gere exatamente 3 perguntas de múltipla escolha inéditas e educativas sobre o tema/conto '{req.tema}' de Machado de Assis. "
            "Retorne APENAS um JSON puro no formato de array, sem blocos de código markdown (```json ... ```) e sem qualquer texto adicional antes ou depois. "
            "Cada elemento deve ter exatamente esta estrutura:\n"
            "[\n"
            "  {\n"
            '    "question": "Texto da pergunta?",\n'
            '    "options": ["Opção 0", "Opção 1", "Opção 2", "Opção 3"],\n'
            '    "answer": 0,\n'
            '    "explanation": "Explicação pedagógica e clara da resposta correta."\n'
            "  }\n"
            "]"
        )

        # Chamada utilizando o modelo gratuito recomendado da Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Você é um professor e especialista em literatura brasileira que responde estritamente em formato JSON válido."
                },
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7
        )
        
        raw_text = completion.choices[0].message.content.strip()
        
        # Limpeza de formatação markdown caso a IA inclua blocos de código
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        if clean_json.startswith("`"):
            clean_json = clean_json.strip("`").replace("json\n", "").strip()
            
        # Converte a string JSON para objeto Python e retorna ao cliente
        return json.loads(clean_json)

    except json.JSONDecodeError as json_err:
        print(f"Erro ao parsear JSON retornado pela Groq: {str(json_err)}")
        raise HTTPException(status_code=500, detail="A resposta da IA não veio em um formato JSON válido.")
    except Exception as e:
        print(f"Exceção ao comunicar com a Groq: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")