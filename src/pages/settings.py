import reflex as rx
from src.state import PhotoState

def settings_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading('Project Setup', size='6'),
            rx.text('Describe what this shoot is for.', color_scheme='gray'),

            rx.vstack(
                rx.text('Project name (Required)', weight='bold'),
                rx.input(
                    placeholder='e.g. Adaeze Evening hangout',
                    value=PhotoState.project_name,
                    on_change=PhotoState.set_project_name,
                    width='100%',
                ),
                align='start', width='100%',
            ),

            rx.vstack(
                rx.text('Brand brief (Required)', weight='bold'),
                rx.text('What is the brand about? Who is it for? What feeling should the photos give?', 
                        size='2', color_scheme='gray'),
                rx.text_area(
                    placeholder='e.g. A natural skincare brand for young Nigerian women. Clean, warm, minimal. Be very descriptive and clear to improve the output',
                    value=PhotoState.brand_brief,
                    on_change=PhotoState.set_brand_brief,
                    width='100%',
                    min_height='120px',
                ),
                align='start', width='100%',
            ),

            rx.vstack(
                rx.text('Brand website (Optional)', weight='bold'),
                rx.input(
                    placeholder='https://...',
                    value=PhotoState.brand_url,
                    on_change=PhotoState.set_brand_url,
                    width='100%',
                ),
                align='start', width='100%',
            ),

            rx.cond(
                PhotoState.settings_error != "",
                rx.text(PhotoState.settings_error, color_scheme="red", size="2"),
            ),
            rx.button(
                rx.cond(
                    PhotoState.is_loading,
                    rx.spinner(size='3'),
                    rx.text('Continue to Editor →'),
                ),
                on_click=PhotoState.submit_settings(),
                disabled=PhotoState.is_loading,
                size='3',
                color_scheme='indigo'
            ),

            spacing='5',
            max_width='560px',
            width='100%',
            padding='40px 24px',
        ),

        display='flex',
        justify_content='center',
        min_height='100vh',
        background='var(--gray-1)',
    )