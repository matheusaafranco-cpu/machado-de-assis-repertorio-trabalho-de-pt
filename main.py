import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Permite requisições vindas do GitHub Pages ou localhost (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizRequest(BaseModel):
    tema: str = "Um Canário (Machado de Assis)"

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    # Lê a chave configurada nas variáveis de ambiente do Render (GEMINI_API_KEY)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave GEMINI_API_KEY não configurada no servidor.")

    prompt_text = (
        f"Gere 3 perguntas inéditas e criativas de múltipla escolha sobre o conto '{req.tema}' de Machado de Assis. "
        "Responda EXCLUSIVAMENTE com um JSON no formato de Array de objetos (sem markdown, sem ```json ou texto adicional). "
        "Estrutura obrigatória:\n"
        "[\n"
        "  {\n"
        '    "question": "Texto da pergunta?",\n'
        '    "options": ["Opção 0", "Opção 1", "Opção 2", "Opção 3"],\n'
        '    "answer": 0,\n'
        '    "explanation": "Explicação sobre a resposta correta."\n'
        "  }\n"
        "]\n"
        "O campo 'answer' deve ser um inteiro (0 a 3) indicando o índice da opção correta."
    )

    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=){api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Limpa marcas de markdown caso a API as inclua
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        
        # Converte o texto para objeto JSON real e retorna
        quiz_json = json.loads(clean_json)
        return quiz_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível carregar o quiz: {str(e)}")