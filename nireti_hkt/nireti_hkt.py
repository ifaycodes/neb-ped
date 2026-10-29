import reflex as rx
from src.pages.settings import settings_page
from src.pages.editor import editor_page
from src.pages.home import home_page

app = rx.App()
app.add_page(home_page, route='/')
app.add_page(settings_page, route='/settings')
app.add_page(editor_page, route='/editor')
