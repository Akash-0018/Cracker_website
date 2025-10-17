import os
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Category, Product
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import requests

class Command(BaseCommand):
    help = 'Populate database with mock data'

    def create_mock_image(self, category_name, index):
        # Use placeholder images from Lorem Picsum
        width = 800
        height = 600
        img_url = f'https://picsum.photos/{width}/{height}?random={index}'
        
        try:
            # Download the image
            response = requests.get(img_url)
            if response.status_code == 200:
                # Create the media directory if it doesn't exist
                media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                os.makedirs(media_dir, exist_ok=True)
                
                # Create filename
                filename = f"{category_name.lower().replace(' ', '_')}_{index}.jpg"
                file_path = os.path.join(media_dir, filename)
                
                # Save the image directly to the media directory
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Return the relative path for the model
                return f'products/{filename}'
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to create image: {str(e)}'))
            return None

    def handle(self, *args, **kwargs):
        # Create categories
        categories = [
            {"name": "Aerial Crackers", "description": "Spectacular aerial fireworks that light up the sky"},
            {"name": "Ground Chakras", "description": "Spinning fireworks that create beautiful patterns on the ground"},
            {"name": "Sparklers", "description": "Hand-held fireworks that emit colorful sparks"},
            {"name": "Fountains", "description": "Stationary fireworks that shoot colorful sparks upward"},
            {"name": "Rockets", "description": "Sky-shooting fireworks with various effects"},
            {"name": "Roman Candles", "description": "Tube-based fireworks shooting multiple colored balls"},
            {"name": "Garland Crackers", "description": "String of small crackers for continuous excitement"},
            {"name": "Flower Pots", "description": "Beautiful fountain-like fireworks with expanding effects"},
            {"name": "Sound Crackers", "description": "Loud crackers with various sound effects"},
            {"name": "Gift Boxes", "description": "Assorted fireworks collections in attractive packages"}
        ]

        # Product name templates for each category
        product_templates = {
            "Aerial Crackers": ["Sky Blaster", "Star Rain", "Color Burst", "Thunder Cloud", "Night Pearl"],
            "Ground Chakras": ["Spin Master", "Color Wheel", "Ground Star", "Rainbow Spin", "Light Circle"],
            "Sparklers": ["Golden Sparkle", "Color Rain", "Magic Wand", "Silver Shine", "Star Stick"],
            "Fountains": ["Color Shower", "Rainbow Fall", "Crystal Spray", "Diamond Dust", "Pearl Stream"],
            "Rockets": ["Sky Hunter", "Star Chaser", "Moon Rider", "Cloud Pierce", "Night Flyer"],
            "Roman Candles": ["Color Shot", "Star Stream", "Night Ball", "Rainbow Balls", "Pearl Shot"],
            "Garland Crackers": ["Joy String", "Festival Chain", "Celebration Line", "Party Link", "Happy Thread"],
            "Flower Pots": ["Garden Bloom", "Color Bloom", "Night Flower", "Star Blossom", "Rainbow Pot"],
            "Sound Crackers": ["Thunder King", "Sound Storm", "Blast Master", "Echo Plus", "Boom Box"],
            "Gift Boxes": ["Festival Pack", "Party Box", "Celebration Kit", "Family Pack", "Premium Collection"]
        }

        self.stdout.write('Creating categories and products...')

        for cat_data in categories:
            category = Category.objects.create(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            
            # Create 5 products for each category
            templates = product_templates[cat_data["name"]]
            for i in range(5):
                base_name = templates[i]
                # Create variants of each base name
                for size in ["Small", "Medium", "Large", "Premium", "Deluxe"]:
                    price = random.uniform(
                        50.0 if size == "Small" else 100.0 if size == "Medium" else 200.0 if size == "Large" else 500.0 if size == "Premium" else 1000.0,
                        100.0 if size == "Small" else 200.0 if size == "Medium" else 400.0 if size == "Large" else 800.0 if size == "Premium" else 2000.0
                    )
                    
                    product = Product.objects.create(
                        name=f"{size} {base_name}",
                        category=category,
                        price=round(price, 2),
                        stock_quantity=random.randint(5, 50),
                        description=f"{size} size {base_name} - {cat_data['description']}. Perfect for celebrations and festivals.",
                        is_active=True
                    )

                    # Add image to product
                    image_path = self.create_mock_image(cat_data["name"], i)
                    if image_path:
                        product.image = image_path
                        product.save()

        self.stdout.write(self.style.SUCCESS('Successfully created mock data!'))