import reflex as rx
from src.state import PhotoState

def home_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.heading('NIRETI', size='9', letter_spacing='1em', line_height='2'),

                rx.heading('Your brand has a look. Now your photos can match it.', size='6', line_height='3'),

                rx.text("Nireti analyzes your product photos and suggests edits guided by your brand’s visual direction. " \
                    "You stay in control. Nothing changes until you say so.", size='2', font_style='italic', line_height='4'
                ),

                rx.button('Get started →', on_click=rx.redirect('/settings'), size='3', color_scheme='indigo', width='50%'
                ),

                position="relative", width="100%", height="500px", overflow="hidden",
                border_radius="12px", box_shadow="lg", align='center', justify='center', 
                padding='24px 24px',
            ),

            rx.divider(color_scheme='indigo'),

            rx.vstack(
                rx.text('How It Works', weight='bold', text_decoration="underline"),
                rx.text("""1. Describe your brand → tell Nireti about your shoot and drop in your website URL. It figures out your visual style.
                2. Import your photos → upload your product shots. Each one is analyzed in the background automatically.
                3. Review the suggestions → see exactly what to adjust and why, in plain language. Apply with one click.
                4. Export → download your edited photos, ready to post.""", 
                size='2', color_scheme='gray', line_height='3', white_space="pre-line"),
                align='center', width='100%', justify='center', padding='24px 24px',
            ),
            rx.button(
                'See it work →',
                on_click=rx.redirect('/settings'),
                size='3', width='30%',
                color_scheme='indigo', align='center', justify='center',
                variant='outline'
            ),

            rx.text("No Lightroom. No editing experience needed. Just your brand and your photos.", size='1', font_style='italic', line_height='4'),

            spacing='3',
            width='100%',
            align='center'
        ),

        display='flex',
        justify_content='center',
        min_height='100vh',
        background='var(--gray-1)',
    )