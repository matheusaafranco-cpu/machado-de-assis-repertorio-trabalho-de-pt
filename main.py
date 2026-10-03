@app.post("/api/quiz/like/{pergunta_id}")
def dar_like_pergunta(pergunta_id: int):
    try:
        # Busca a pergunta atual para somar +1 no like
        resp = supabase.table("perguntas_usuario").select("likes").eq("id", pergunta_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Pergunta não encontrada.")
        
        likes_atuais = resp.data[0].get("likes", 0)
        novo_total = likes_atuais + 1
        
        # Atualiza no Supabase
        supabase.table("perguntas_usuario").update({"likes": novo_total}).eq("id", pergunta_id).execute()
        return {"mensagem": "Like registado com sucesso!", "likes": novo_total}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))