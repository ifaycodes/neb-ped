from openai import OpenAI
from tavily import TavilyClient
import os
from pydantic import BaseModel
from dotenv import load_dotenv
import re

load_dotenv()

class BrandDirection(BaseModel):
    genre: str
    traits: list[str]

class Suggestions(BaseModel):
    exposure: float
    shadows: float
    highlights: float
    contrast: float
    temp: float
    saturation: float
    confidence: float
    reason: str

START_PROMPT = """
    You are a brand visual strategist.
    Provide only the final answer without any explanation or preamble

    Given the following input about a photo shoot or brand, return a JSON object with two fields:

    - "genre": one to three words describing the photography category 
    (e.g. "skincare product", "fashion portrait", "food", "jewellery", "lifestyle").
    If the input is vague, infer the most likely genre from context clues.
    
    - "traits": an array of 3 to 5 words or short phrases describing how 
    the photos should look and feel visually
    Each trait should be one to three words
    (e.g. ["warm", "minimal", "soft light", "clean background"]).
    If the input is vague, suggest traits that suit the inferred genre.

    Return ONLY valid JSON, nothing else.

    Example output:
    {{
    "genre": "skincare product",
    "traits": ["warm", "minimal", "clean", "soft contrast"]
    }}

    Shoot description: {input}
    """

MERGE_PROMPT = """
    You are a photography style consultant.

    A brand shooting {genre} photos has these visual traits they want: {traits}

    General industry conventions for editing {genre} photos are:
    {conventions}

    Your job: write 3 to 4 short bullet points describing how this specific brand should edit their {genre} photos.
    Where the brand traits conflict with general conventions, the brand traits win.
    Where they align, reinforce both.
    Be specific about tone, contrast, colour temperature, and mood.
    One sentence per bullet. No intro or conclusion.
    """

ANALYSIS_PROMPT = """
    You are an expert photo editor reviewing a product photo.
    Provide only the final answer without any explanation or preamble

    Brand visual direction: {traits}
    (e.g. ["warm", "minimal", "clean", "premium"])

    Image measurements:
    - Average brightness: {brightness} (0=black, 1=white)
    - Clipped highlights: {highlight_pct}% of pixels above 0.95
    - Clipped shadows: {shadow_pct}% of pixels below 0.05
    - Color cast: red channel avg {r_avg}, green {g_avg}, blue {b_avg}

    Based on the image and the brand direction, suggest edits using 
    these six sliders only. All values must be between -1.0 and +1.0.

    Return ONLY valid JSON in this exact format, nothing else:
    {
    "exposure":    0.0,
    "shadows":     0.0,
    "highlights":  0.0,
    "contrast":    0.0,
    "temp":        0.0,
    "saturation":  0.0,
    "confidence":  0.0,
    "reason":      "One sentence explaining the main adjustment and why it serves the brand direction."
    }
    """

# client declaration
client_light = OpenAI(
    base_url="https://api.tokenfactory.eu-north1.nebius.com/v1/",
    api_key=os.environ.get('EDITOR_KEY')
)

client_vision = OpenAI(
    base_url="https://api.tokenfactory.us-north1.nebius.com/v1/",
    api_key=os.environ.get('VISION_KEY')
)

client_tavily = TavilyClient(os.environ.get('TAVILY_KEY'))

# the model call functions
def get_brand_direction(user_input: str, brand_url: str = '') -> BrandDirection:
    
    if brand_url:
        tavily_url_extract = client_tavily.extract(urls=[brand_url])
        result = tavily_url_extract['results'][0]['raw_content']
        combined_input = f"{user_input}\n\n{result}"
    else:
        combined_input = user_input

    raw = client_light.chat.completions.create(
        model = 'nvidia/Nemotron-3_5-Lightning',
        messages=[
            {
                "role": "system",
                "content": "Provide only the JSON final answer without any explanation or preamble"
            },
            {
                "role": "user",
                "content": START_PROMPT.format(input=combined_input)
            }
        ],
    )
    brand_direction = raw.choices[0].message.content
    return BrandDirection.model_validate_json(extract_json(brand_direction))

def get_tavily_convention(genre: str) -> str:
    results = client_tavily.search(
        f"style guide on how to edit {genre} brand photos")
    
    snippets = [r.get('content', '') for r in results.get('results', []) if r['score'] > 0.65]
    return ('\n\n'.join(snippets[:3]))

def get_personalized_conventions(genre: str, traits: list[str]) -> str:
    raw_conventions = get_tavily_convention(genre)
    
    response = client_light.chat.completions.create(
        model="nvidia/Nemotron-3_5-Lightning",
        messages=[
            {
                "role": "system",
                "content": "Return only the bullet points. No intro, no conclusion."
            },
            {
                "role": "user",
                "content": MERGE_PROMPT.format(
                    genre=genre,
                    traits=traits,
                    conventions=raw_conventions,
                ),
            }
        ],
    )
    conventions = response.choices[0].message.content
    print(conventions)
    return conventions

def get_suggestions(
        image_base64: str, traits: list[str], genre: str, conventions: str, measurements: dict,
) -> Suggestions:
    res = client_vision.chat.completions.create(
        model = 'nvidia/Nemotron-3.5-Super-VL',
        messages=[
            {
                "role": "system",
                "content": ANALYSIS_PROMPT,
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f"""
                                Genre: {genre}
                                Conventions: {conventions}  
                                Visual traits: {traits}
                                Measurements: brightness={measurements['brightness']},  highlight_pct={measurements['highlight_pct']}%, shadow_pct={measurements['shadow_pct']}%, r={measurements['r_avg']}, g={measurements['g_avg']}, b={measurements['b_avg']}
                                """
                    },
                    {
                        'type': 'image_url',
                        'image_url': {'url': image_base64}
                    }
                ]
            }],
    )
    suggestions = res.choices[0].message.content
    return Suggestions.model_validate_json(extract_json(suggestions))

def extract_json(text: str) -> str:
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text.strip()
