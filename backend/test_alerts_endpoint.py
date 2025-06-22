# Teste simples do endpoint de alertas
@app.get("/api/v1/test/alerts")
async def test_alerts():

@app.get("/api/v1/accounts/{account_id}/alerts")
async def get_account_alerts_simple(account_id: int):
    return {
        "account_id": account_id,
        "message": "This is the alerts endpoint",
        "test": True
    }
