class ChatRequest(BaseModel):
    pergunta: str

@app.post("/api/chat")
def chat_literario(req: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada no Render.")

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system", 
                    "content": "És um assistente virtual inteligente e amigável especializado nas obras de Machado de Assis, com foco particular nos contos 'Ideias de Canário' e 'Pai Contra Mãe'. Responde às dúvidas dos estudantes de forma educativa, clara e literária em português."
                },
                {"role": "user", "content": req.pergunta}
            ],
            temperature=0.7
        )
        resposta_IA = completion.choices[0].message.content
        return {"resposta": resposta_IA}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))