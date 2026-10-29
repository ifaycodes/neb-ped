import reflex as rx
from rxconfig import config
from pathlib import Path
from PIL import Image
import io, base64
from render import render, make_thumbnail, img_to_base64, measure_image, crop_to_ratio
from reModels.models import get_brand_direction, get_suggestions, get_personalized_conventions

ZERO_SLIDERS = {
    "exposure": 0.0,
    "shadows": 0.0,
    "highlights": 0.0,
    "contrast": 0.0,
    "temp": 0.0,
    "saturation": 0.0,
}

RATIOS = {
    "none": None,
    "4:3": (4, 3),
    "4:5": (4, 5),
    "1:1": (1, 1)
}

class PhotoState(rx.State):
    # Settings Page
    project_name: str = ''
    brand_brief: str = ''
    brand_url: str = ''
    direction_traits: list[str] = []
    genre: str = ''
    direction_conventions: str = ''
    settings_error: str = ''
    is_loading: bool = False

    # Editor page - Photos
    photos: list[str] = []
    photo_names: list[str] = []
    current_index: int = -1
    _originals: list[str] = []

    # Editor - Edit State per photo: List of dicts for each photo
    edit_states: list[dict] = []
    history: list[list[dict]] = []
    redo_stack: list[list[dict]] = []

    # Editor - Photo analysis
    analysis_status: list[str] = []
    suggestions: list[dict] = []

    # UI
    show_original: bool = False
    current_preview: str = ''

    # Crop
    crop_ratio: str = "none"
    crop_x: float = 0.5
    crop_y: float = 0.5

    async def load_photos(self, files: list[rx.UploadFile]):
        """ When user uploads photos """
        was_empty = len(self.photos) == 0

        for f in files:
            data = await f.read() if not isinstance(f, bytes) else f
            img = Image.open(io.BytesIO(data)).convert("RGB")
            thumb = make_thumbnail(img)
            self.photos.append(img_to_base64(thumb))
            self.photo_names.append(getattr(f, 'name', 'photo'))
            self.edit_states.append(dict(ZERO_SLIDERS))
            self.history.append([dict(ZERO_SLIDERS)])
            self.redo_stack.append([])

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            self._originals.append(base64.b64encode(buf.getvalue()).decode())

        self.analysis_status.extend(['pending'] * len(files))
        self.suggestions.extend([{} for _ in files])
        
        if was_empty and self.photos:
            self.select_photo(0)

        yield PhotoState.per_photo_analysis

    def select_photo(self, index: int):
        self.current_index = index
        self.show_original = False
        self._update_preview()

    def remove_photo(self, index: int):
        if index < 0 or index >= len(self.photos):
            return
        
        self.photos.pop(index)
        self.photo_names.pop(index)
        self.edit_states.pop(index)
        self.history.pop(index)
        self.redo_stack.pop(index)
        self._originals.pop(index)
        self.suggestions.pop(index)
        self.analysis_status.pop(index)

        # Adjust current_index if needed
        if not self.photos:
            self.current_index = -1
            self.current_preview = ""
        elif self.current_index >= len(self.photos):
            self.select_photo(len(self.photos) - 1)
        else:
            self.select_photo(self.current_index)

    def remove_from_preview(self):
        self.current_index = -1
        self.current_preview = ''

    def _update_preview(self):
        if self.current_index < 0:
            return
        if self.show_original:
            self.current_preview = "data:image/jpeg;base64," + self._originals[self.current_index]
            return

        raw = base64.b64decode(self._originals[self.current_index])
        img = make_thumbnail(Image.open(io.BytesIO(raw)))
        v = self.edit_states[self.current_index]
        edited = render(img, v)
        ratio = RATIOS.get(self.crop_ratio)
        if ratio:
            edited = crop_to_ratio(edited, ratio, self.crop_x, self.crop_y)
        self.current_preview = img_to_base64(edited)

    def set_slider(self, key: str, value: float):
        if self.current_index < 0:
            return
        self.edit_states[self.current_index][key] = round(value, 2)
        self._update_preview()

    def set_slider_from_input(self, key: str, value_str: str):
        if self.current_index < 0:
            return
        try:
            val = float(value_str)
            clamped = max(-1.0, min(1.0, round(val, 2)))
            self.edit_states[self.current_index][key] = clamped
            self._update_preview()
        except (ValueError, TypeError):
            pass

    def apply_suggestions(self):
        """When user clicks apply to accept AI suggestions"""
        if self.current_index < 0:
            return
        index = self.current_index
        suggestions = self.suggestions[index]
        if not suggestions:
            return
        
        # push to history before appying changes
        self.history[index].append(dict(self.edit_states[index]))
        self.redo_stack[index] = []
        self.edit_states[index] = {key: suggestions.get(key, 0.0) for key in ZERO_SLIDERS}
        self._update_preview()

    def undo(self):
        index = self.current_index
        if index < 0 or len(self.history[index]) <= 1:
            return
        self.redo_stack[index].append(dict(self.edit_states[index]))
        self.edit_states[index] = self.history[index].pop()
        self._update_preview()

    def redo(self):
        index = self.current_index
        if index < 0 or  not self.redo_stack[index]:
            return
        self.history[index].append(dict(self.edit_states[index]))
        self.edit_states[index] = self.redo_stack[index].pop()
        self._update_preview()

    def reset_edit(self):
        if self.current_index < 0:
            return
        index = self.current_index
        self.history[index].append(dict(self.edit_states[index]))
        self.redo_stack[index] = []
        self.edit_states[index] = dict(ZERO_SLIDERS)
        self._update_preview()

    def toggle_original(self, value: bool):
        self.show_original = value
        self._update_preview()

    @rx.var
    def current_sliders(self) -> dict:
        if self.current_index < 0 or not self.edit_states:
            return {"exposure": 0.0, "shadows": 0.0, "highlights": 0.0,
                "contrast": 0.0, "temp": 0.0, "saturation": 0.0}
        return self.edit_states[self.current_index]

    async def submit_settings(self):
        if not self.brand_brief and not self.brand_url:
            self.settings_error = 'Add a brief or URL to continue.'
            return

        self.is_loading = True
        user_input = self.brand_brief or ''

        direction = get_brand_direction(user_input, self.brand_url)
        self.genre = direction.genre
        self.direction_traits = direction.traits

        conventions = get_personalized_conventions(direction.genre, direction.traits)
        self.direction_conventions = conventions

        self.is_loading = False
        yield rx.redirect('/editor')

    @rx.event(background=True)
    async def per_photo_analysis(self):
        for i in range(len(self._originals)):
            async with self:
                if self.analysis_status[i] != 'pending':
                    continue
                self.analysis_status[i] = 'analysing'

            raw = base64.b64decode(self._originals[i])
            photo = Image.open(io.BytesIO(raw)).convert('RGB')

            measurement = measure_image(photo)
            image_b64 = img_to_base64(make_thumbnail(photo))

            try:
                edit_suggestions = get_suggestions(
                    image_base64=image_b64,
                    traits=list(self.direction_traits), 
                    genre=self.genre, 
                    conventions=self.direction_conventions,
                    measurements=measurement
                )
                async with self:
                    self.suggestions[i] = edit_suggestions.model_dump()
                    self.analysis_status[i] = 'ready'
            except Exception as e:
                print(f'Photo analysis failed for photo {i}: {e}')
                async with self:
                    self.analysis_status[i] = 'failed'

    def export_photo(self):
        if self.current_index < 0:
            return
        
        raw = base64.b64decode(self._originals[self.current_index])
        img = Image.open(io.BytesIO(raw)).convert("RGB")

        v = self.edit_states[self.current_index]
        edited = render(img, v)

        ratio = RATIOS.get(self.crop_ratio)
        if ratio:
            edited = crop_to_ratio(edited, ratio, self.crop_x, self.crop_y)
        
        buf = io.BytesIO()
        edited.save(buf, format="JPEG", quality=95, optimize=True)
        buf.seek(0)
        
        stem = self.photo_names[self.current_index].rsplit(".", 1)[0]
        return rx.download(
            data=buf.getvalue(),
            filename=f"{stem}_edited.jpg",
        )

    async def export_all(self):
        if not self._originals:
            return

        for i, original in enumerate(self._originals):
            raw = base64.b64decode(original)
            img = Image.open(io.BytesIO(raw)).convert('RGB')

            v = self.edit_states[i]
            edited = render(img, v)

            ratio = RATIOS.get(self.crop_ratio)
            if ratio:
                edited = crop_to_ratio(edited, ratio, self.crop_x, self.crop_y)

            img_buf = io.BytesIO()
            edited.save(img_buf, format='JPEG', quality=95, optimize=True)
            img_buf.seek(0)

            stem = self.photo_names[i].rsplit('.', 1)[0]
            yield rx.download(
                data=img_buf.getvalue(),
                filename=f'{stem}_edited.jpg'
            )
    
    def set_project_name(self, val: str):
        self.project_name = val

    def set_brand_brief(self, val: str):
        self.brand_brief = val

    def set_brand_url(self, val: str):
        self.brand_url = val

    def set_crop_ratio(self, val: str):
        self.crop_ratio = val
        self._update_preview()

    def set_crop_x(self, val: float):
            self.crop_x = val
            self._update_preview()

    def set_crop_y(self, val: float):
            self.crop_y = val
            self._update_preview()