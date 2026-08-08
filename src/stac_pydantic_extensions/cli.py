import typer

app = typer.Typer()


@app.callback()
def callback():
    """
    STAC Pydantic Extensions
    """


@app.command()
def migrate():
    """
    Takes an item and migrates it to the latest versions
    """
    pass
