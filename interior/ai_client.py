import os
import base64
import io
from openai import OpenAI
from PIL import Image
from .config import Config

class AIClient:
    """Класс для работы с AI API"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY, 
            base_url=Config.BASE_URL
        )
    
    def analyze_thematic_subcategory(self, image_path, logger):
        """Анализирует тематику и подкатегорию товара"""
        base64_image = self.encode_image_to_base64(image_path)
        
        system_prompt = """Ты эксперт по категоризации товаров маркетплейса.
        Твоя задача — определить категорию и подкатегорию товара по фото.
        Ответ строго в формате: КАТЕГОРИЯ|ПОДКАТЕГОРИЯ
        
        Особое правило:
        - Если изображены праздничные украшения (ёлочные игрушки, новогодние, пасхальные, хэллоуинские предметы и т.п.), 
          отнеси их к категории HOLIDAY с соответствующей подкатегорией:
          CHRISTMAS, EASTER, HALLOWEEN, NEW_YEAR, VALENTINE или GENERAL.
        
        Остальные доступные категории и подкатегории:
        KITCHEN - COOKWARE, UTENSILS, APPLIANCES, STORAGE, DINNERWARE, DECOR
        BATHROOM - TOWELS, HYGIENE, FURNITURE, STORAGE, ACCESSORIES, CLEANING  
        LIVING_ROOM - FURNITURE, LIGHTING, DECOR, TEXTILES, STORAGE, ELECTRONICS
        BEDROOM - BEDDING, FURNITURE, LIGHTING, DECOR, STORAGE, TEXTILES
        GARDEN - FURNITURE, TOOLS, DECOR, PLANTS, LIGHTING, STORAGE
        OFFICE - FURNITURE, ORGANIZATION, STATIONERY, TECH, DECOR
        HOLIDAY - CHRISTMAS, EASTER, HALLOWEEN, NEW_YEAR, VALENTINE, GENERAL"""
        
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Определи категорию и подкатегорию этого товара:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            if "|" in result:
                category, subcategory = result.split("|")
                return category, subcategory
            else:
                return "LIVING_ROOM", "DECOR"
                
        except Exception as e:
            logger.error(f"Ошибка анализа категории: {e}")
            return "LIVING_ROOM", "DECOR"

    def generate_context_prompt(self, main_category, subcategory):
        """Генерирует промпт для создания изображения в контексте"""
        
        context_descriptions = {
            "KITCHEN": {
                "COOKWARE": "kitchen counter with other cooking utensils, stove in background",
                "UTENSILS": "kitchen drawer or utensil holder, cooking preparation scene",
                "APPLIANCES": "kitchen counter with other appliances, modern kitchen setting",
                "STORAGE": "pantry or kitchen shelves with other storage items",
                "DINNERWARE": "dining table setting or kitchen cabinet with other dishes",
                "DECOR": "kitchen wall or counter with decorative elements"
            },
            "BATHROOM": {
                "TOWELS": "bathroom towel rack or shelf with other bathroom textiles",
                "HYGIENE": "bathroom sink or shower with other hygiene products",
                "FURNITURE": "bathroom with vanity or storage furniture",
                "STORAGE": "bathroom shelves or organizer with other bathroom items",
                "ACCESSORIES": "bathroom wall or counter with accessories",
                "CLEANING": "bathroom cleaning station or storage area"
            },
            "LIVING_ROOM": {
                "FURNITURE": "living room with complementary furniture pieces",
                "LIGHTING": "living room corner with ambient lighting",
                "DECOR": "living room shelf or wall with decorative items",
                "TEXTILES": "sofa or armchair with complementary textiles",
                "STORAGE": "living room shelves or media console",
                "ELECTRONICS": "entertainment center or tech area"
            },
            "BEDROOM": {
                "BEDDING": "made bed with complementary bedding items",
                "FURNITURE": "bedroom with complementary furniture arrangement",
                "LIGHTING": "bedside table with lighting elements",
                "DECOR": "bedroom dresser or wall with decorative pieces",
                "STORAGE": "bedroom closet or storage area",
                "TEXTILES": "bed or seating area with textile elements"
            },
            "GARDEN": {
                "FURNITURE": "garden patio or deck with outdoor furniture",
                "TOOLS": "garden shed or tool storage area",
                "DECOR": "garden path or flower bed with decorative elements",
                "PLANTS": "garden bed or plant display area",
                "LIGHTING": "garden evening scene with lighting",
                "STORAGE": "garden storage box or shelf"
            },
            "OFFICE": {
                "FURNITURE": "office space with desk and chair setup",
                "ORGANIZATION": "office desk with organizational systems",
                "STATIONERY": "office desk with stationery items",
                "TECH": "office workstation with technology accessories",
                "DECOR": "office shelf or wall with decorative elements"
            },
            "HOLIDAY": {
                "CHRISTMAS": "festive indoor setting with Christmas tree, lights and ornaments",
                "EASTER": "bright spring setting with flowers, eggs and decorations",
                "HALLOWEEN": "autumn interior with pumpkins, candles, spider webs",
                "NEW_YEAR": "festive interior with garlands, tinsel and lights",
                "VALENTINE": "romantic indoor decor with hearts, candles and flowers",
                "GENERAL": "festive cozy room with party decorations"
            }
        }
        
        context = context_descriptions.get(main_category, {}).get(subcategory, "neutral interior setting")
        
        prompt = f"""
CREATE NATURAL PRODUCT PHOTO IN CONTEXT:

PRODUCT PRESERVATION:
- Use the EXACT same product from the input image
- Maintain the SAME angle, orientation, and position as in the original photo
- Do NOT change the product's perspective or viewing angle
- Preserve all product details, colors, textures exactly as shown
- Keep all text, labels, logos completely unchanged

CONTEXT AND SETTING:
- Place the product in a {main_category.lower()} environment: {context}
- The product should appear naturally placed in this setting
- Maintain the same scale and proportions as in the original

BACKGROUND AND COMPOSITION:
- Create a soft, slightly blurred background that matches {main_category} aesthetic
- Background should be authentic but not distracting from the product
- Use natural lighting that complements the product's original appearance
- Add subtle contextual elements that make sense for {subcategory.lower()}

STYLING GUIDELINES:
- The scene should look realistic and professionally styled
- Product must remain the main focus of the image
- Keep the composition clean and uncluttered
- Lighting should highlight the product naturally

TECHNICAL REQUIREMENTS:
- High-quality professional photography
- Product appearance must be identical to input (only environment changes)
- Maintain original product angle and orientation
- Soft background blur to keep focus on product

FINAL OUTPUT: Natural product photo in appropriate {main_category} context, with identical product presentation. 1:1 aspect ratio image.
"""
        
        return prompt

    def edit_image_with_gemini(self, input_path, prompt, logger):
        """Генерирует изображение с помощью AI"""
        base64_image = self.encode_image_to_base64(input_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
        try:
            response = self.client.chat.completions.create(
                model=Config.IMAGE_MODEL,
                messages=messages,
                max_tokens=1000
            )
            msg = response.choices[0].message
            if hasattr(msg, "image") and msg.image and "url" in msg.image:
                img_url = msg.image["url"]
                if "base64," in img_url:
                    base64_data = img_url.split("base64,")[1]
                    image = Image.open(io.BytesIO(base64.b64decode(base64_data)))
                    return image
                else:
                    logger.error("В поле image нет base64.")
                    return None
            else:
                logger.error("В ответе не найдено msg.image с url.")
                return None
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения: {e}")
            return None

    @staticmethod
    def encode_image_to_base64(image_path):
        """Кодирует изображение в base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')