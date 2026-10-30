import reflex as rx
from src.state import PhotoState

SLIDERS = [
    ("exposure",   "Exposure"),
    ("shadows",    "Shadows"),
    ("highlights", "Highlights"),
    ("contrast",   "Contrast"),
    ("temp",       "Temperature"),
    ("saturation", "Saturation"),
]

def slider_row(key: str, label: str):
    value = PhotoState.current_sliders[key].to(float)
    return rx.hstack(
        rx.text(label, width='90px', size='1', weight='light'),
        rx.slider(
            min=-1, max=1, step=0.01,
            size='1',
            value=[PhotoState.current_sliders[key]],
            on_change=lambda v: PhotoState.set_slider(key, v[0]).throttle(100),
            flex='1',
        ),

        rx.input(
            type='number',
            min=-1,
            max=1,
            step=0.01,
            value=PhotoState.current_sliders[key],
            on_change=lambda v: PhotoState.set_slider_from_input(key, v),
            width="36px", size="1", text_align="center", variant="surface", color_scheme='gray',
        ),
        width='100%', align='center', spacing='3',
    )

def filmstrip() -> rx.Component:
    return rx.hstack(
        rx.foreach(
            rx.Var.range(PhotoState.photos.length()),
            lambda i: rx.box(
                # The image
                rx.image(
                    src=PhotoState.photos[i], width="80px", height="60px", object_fit="cover", cursor="pointer",
                    border=rx.cond(
                        PhotoState.current_index == i,
                        '2px solid var(--indigo-9)',
                        '2px solid transparent',
                    ),
                    on_click=lambda: PhotoState.select_photo(i),
                ),
                # The hovering 'X' button
                rx.icon_button(
                    rx.icon("x", size=10), size="1", variant="solid", color_scheme="gray", radius="full", 
                    position="absolute", top="-4px", right="-4px", cursor="pointer", on_click=lambda: PhotoState.remove_photo(i),
                ),
                position="relative",
                display="inline-block",
                ),
        ),

        rx.spacer(),
    
        rx.button(
            'Export All', variant='outline', size='2', on_click=PhotoState.export_all
        ),

        overflow_x='auto',
        padding='8px 16px',
        background='var(--gray-3)',
        width='100%',
        spacing='2',
    )

def editor_page() -> rx.Component:
    return rx.vstack(
        # top bar
        rx.hstack(
            rx.heading('Nireti', size='4', display=["block", "block", "none"]),
            rx.heading('Nireti - Photo Copilot', size='6', display=["none", "none", "block"]),
            rx.spacer(),
            rx.upload(
                rx.button('Import photos', variant='outline', size='2'),
                accept={'image/*': [".jpg", '.jpeg', '.png', '.webp']},
                multiple=True,
                padding='0',
                border='none',
                on_drop=PhotoState.load_photos,
            ),
            rx.spacer(),
            rx.button('← Settings', variant='ghost', size='2', on_click=rx.redirect('/settings')),

            padding='12px 12px', width='100%', height='60px', border_bottom='1px solid var(--gray-5)', background='var(--gray-2)',
        ),
        # main preview area
        rx.hstack(
            rx.vstack(
                rx.cond(
                    PhotoState.current_preview != '',
                    rx.box(
                        rx.image(
                            src=PhotoState.current_preview,
                            max_width="100%",
                            max_height="calc(100vh - 220px)",
                            height="1000px",
                            object_fit="contain",
                        ),
                        rx.icon_button(
                            rx.icon("x", size=12), size="1", variant="solid", color_scheme="gray", radius="full", opacity='0', _hover={'opacity': '1'},
                            position="absolute", top="-4px", right="-4px", cursor="pointer", on_click=lambda: PhotoState.remove_from_preview,
                        ),
                        
                        position="relative",
                        display="inline-block",
                    ),
                    rx.vstack(
                        rx.text('Import photos to begin', color_scheme='gray'),
                        rx.upload(
                            rx.button(f'Import photos or Drag and Drop', variant='ghost', size='2'),
                            accept={'image/*': [".jpg", '.jpeg', '.png', '.webp']},
                            multiple=True,
                            on_drop=PhotoState.load_photos,
                        ),
                        width='100%', height='400px', align='center', justify='center', spacing='3'
                    ),
                ),

                align='center', flex='1', padding='16px', overflow='hidden',
            ),

            # right panel, sliders and controls
            rx.vstack(
                rx.text('ADJUSTMENTS', size='1', weight='medium', color_scheme='gray', letter_spacing='0.1em'),
                rx.vstack(
                    *[slider_row(k, label) for k, label in SLIDERS],
                    spacing='3',
                    width='100%',
                ),

                rx.divider(),

                rx.text('CROP', size='1', weight='medium', letter_spacing='0.1em'),
                rx.select(
                    ['none', '4:3', '4:5', '1:1'],
                    value=PhotoState.crop_ratio,
                    on_change=PhotoState.set_crop_ratio,
                    placeholder='Crop ratio',
                    size='1',
                    width='50%',
                ),

                rx.cond(
                    PhotoState.crop_ratio != 'none',
                    rx.vstack(
                        rx.hstack(
                            rx.text("Pan H", width="60px", size="1"),
                            rx.slider(min=0, max=1, step=0.01, value=[PhotoState.crop_x],
                                on_change=lambda v: PhotoState.set_crop_x(v[0]).throttle(200), flex="1"),
                            width='100%', align="center", spacing="3"
                        ),
                        rx.hstack(
                            rx.text("Pan V", width="60px", size="1"),
                            rx.slider(min=0, max=1, step=0.01, value=[PhotoState.crop_y],
                                on_change=lambda v: PhotoState.set_crop_y(v[0]).throttle(200), flex="1"),
                            width='100%', align="center", spacing="3"
                        ),
                        width='100%', spacing='3',
                    )
                ),

                rx.divider(),

                # Apply suggestion
                rx.vstack(
                    rx.text("SUGGESTIONS", size='1', weight='medium', letter_spacing='0.1em'),
                    rx.cond(
                        PhotoState.current_index >= 0,
                        rx.cond(
                            PhotoState.analysis_status[PhotoState.current_index] == "ready",
                            rx.vstack(
                                rx.box(
                                    rx.vstack(
                                        rx.text(f'exposure: {PhotoState.suggestions[PhotoState.current_index]['exposure']}', line_height='2',size='1'),
                                        rx.text(f'shadows: {PhotoState.suggestions[PhotoState.current_index]['shadows']}', line_height='2', size='1'),
                                        rx.text(f'highlights: {PhotoState.suggestions[PhotoState.current_index]['highlights']}', line_height='2', size='1'),
                                        rx.text(f'contrast: {PhotoState.suggestions[PhotoState.current_index]['contrast']}', line_height='2',  size='1'),
                                        rx.text(f'temp: {PhotoState.suggestions[PhotoState.current_index]['temp']}', line_height='2', size='1'),
                                        rx.text(f'saturation: {PhotoState.suggestions[PhotoState.current_index]['saturation']}', line_height='2', size='1'),
                                        rx.text(f'confidence: {PhotoState.suggestions[PhotoState.current_index]['confidence']}', line_height='2', size='1'),
                                        rx.text(f'reason: {PhotoState.suggestions[PhotoState.current_index]['reason']}', line_height='2', size='1'),

                                        align_items='start',
                                        gap='2px',
                                        margin_bottom='1em',
                                        padding='0.5em',
                                        background='var(--gray-3)',
                                        color_scheme='gray',
                                        width='100%',
                                    ),
                                ),

                                rx.button(
                                    'Apply AI Suggestions',
                                    on_click=PhotoState.apply_suggestions,
                                    width='50%',
                                    color_scheme='indigo',
                                    size='1',
                                ),
                                width='100%',
                                spacing='2',
                            ),
                            rx.cond(
                                PhotoState.analysis_status[PhotoState.current_index] == "analyzing",
                                rx.text("Analyzing...", size='1', color_scheme='gray'),
                                rx.text("Pending analysis", size='1', color_scheme='gray'),
                            ),
                        ),
                        rx.text("No photo selected", size='1', color_scheme='gray'),
                    ),
                    width='100%',
                    spacing='2',
                ),

                rx.divider(),

                rx.hstack(
                    rx.button("Undo", on_click=PhotoState.undo, variant="outline", size="1", flex="1"),
                    rx.button("Redo", on_click=PhotoState.redo, variant="outline", size="1", flex="1"),
                    rx.button("Reset", on_click=PhotoState.reset_edit, color_scheme="red", variant="outline", size="1", flex="1"),
                    width="100%", 
                    spacing="2",
                ),

                rx.button('Download Image', on_click=PhotoState.export_photo, color_scheme='indigo', size='1', width='50%', justify='center'),

                rx.divider(),

                # Before/After Toggle
                rx.hstack(
                    rx.text('After', size='1'),
                    rx.switch(
                        checked=PhotoState.show_original,
                        on_change=PhotoState.toggle_original,
                    ),
                    rx.text('Before', size='1'),
                    spacing='2', align='center',
                ),

                width="400px",
                min_width="400px",
                padding="16px",
                border_left="1px solid var(--gray-5)",
                height="100%",
                overflow_y="auto",
                spacing="4",
                background="var(--gray-2)",
            ),

            width="100%",
            flex="1",
            overflow="hidden",
            align="start",
            justify='center'
        ),

        # Call filmstrip
        filmstrip(),

        spacing='0',
        width="100%",
        height='100vh',
        overflow="hidden",
    )