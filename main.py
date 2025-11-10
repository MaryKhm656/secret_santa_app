from app.web.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.1.1.1", port=8005, reload=True)
