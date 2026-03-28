from flask import Flask, render_template, request, jsonify
import json
import os
import sys
from datetime import datetime

# Determine base path for bundled exe vs script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        return sys._MEIPASS
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# For data files that need to persist (read/write), use exe directory
def get_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DATA_PATH = get_data_path()

# Add Scrapling to path
if getattr(sys, 'frozen', False):
    # When frozen, scrapling is bundled directly in _MEIPASS
    sys.path.insert(0, BASE_PATH)
else:
    # When running as script, add Scrapling repo folder
    sys.path.insert(0, os.path.join(BASE_PATH, 'Scrapling'))
from scrapling import DynamicFetcher

app = Flask(__name__,
            template_folder=os.path.join(BASE_PATH, 'templates'))
WISHLIST_FILE = os.path.join(DATA_PATH, 'wishlist.json')
BRAND_FILE = os.path.join(BASE_PATH, 'brand.json')
BRAND_YAHOO_FILE = os.path.join(BASE_PATH, 'brand_yahoo.json')

def load_wishlist():
    if os.path.exists(WISHLIST_FILE):
        with open(WISHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_wishlist(wishlist):
    with open(WISHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(wishlist, f, ensure_ascii=False, indent=2)

def fetch_product_info(url):
    try:
        # Use Scrapling's DynamicFetcher for fast JS rendering
        response = DynamicFetcher.fetch(
            url,
            headless=True,
            disable_resources=True,  # Block fonts, media, etc. for speed
            timeout=30000,
            wait_selector='[data-testid="name"]',
            wait=500  # Reduced wait time
        )

        # Extract product name from <div data-testid="name"> containing <h1>
        name = 'Unknown'
        name_elements = response.css('div[data-testid="name"] h1')
        if name_elements:
            name = str(name_elements[0].text) or name_elements[0].get_all_text(strip=True)

        # Extract brand - first <p> in <div data-testid="item-size-and-brand-container">
        brand = 'Unknown'
        brand_elements = response.css('div[data-testid="item-size-and-brand-container"] p')
        if brand_elements:
            brand = str(brand_elements[0].text) or brand_elements[0].get_all_text(strip=True)

        # Extract price from <div data-testid="price">
        price = 'Unknown'
        price_elements = response.css('div[data-testid="price"] span')
        if len(price_elements) >= 2:
            currency = str(price_elements[0].text)
            amount = str(price_elements[1].text)
            price = currency + amount

        # Extract image from figure with itemThumbnail class -> img src
        image = ''
        img_elements = response.css('figure[class*="itemThumbnail"] img')
        if img_elements:
            image = img_elements[0].attrib.get('src', '')

        return {
            'name': name if name else 'Unknown',
            'brand': brand if brand else 'Unknown',
            'price': price if price else 'Unknown',
            'image': image,
            'error': None
        }
    except Exception as e:
        return {
            'name': 'Error',
            'brand': 'Error',
            'price': 'Error',
            'image': '',
            'error': str(e)
        }

@app.route('/')
def index():
    with open(BRAND_FILE, 'r', encoding='utf-8') as f:
        brands_data = json.load(f)
    # Sort brands alphabetically A-Z
    brands = dict(sorted(brands_data.items(), key=lambda x: x[0].lower()))

    # Load Yahoo brands
    brands_yahoo = {}
    if os.path.exists(BRAND_YAHOO_FILE):
        with open(BRAND_YAHOO_FILE, 'r', encoding='utf-8') as f:
            brands_yahoo_data = json.load(f)
        brands_yahoo = dict(sorted(brands_yahoo_data.items(), key=lambda x: x[0].lower()))

    wishlist = load_wishlist()
    return render_template('index.html', brands=brands, brands_yahoo=brands_yahoo, wishlist=wishlist)

@app.route('/api/wishlist', methods=['POST'])
def add_to_wishlist():
    data = request.json
    url = data.get('url', '').strip()

    if not url or 'mercari.com' not in url:
        return jsonify({'success': False, 'error': 'Invalid Mercari URL'}), 400

    wishlist = load_wishlist()

    # Check if already exists
    for item in wishlist:
        if item['url'] == url:
            return jsonify({'success': False, 'error': 'Product already in wishlist'}), 400

    info = fetch_product_info(url)

    item = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'url': url,
        'name': info['name'],
        'brand': info['brand'],
        'price': info['price'],
        'desire_price': '',
        'image': info['image'],
        'error': info['error'],
        'bought': False,
        'bought_at': None,
        'added_at': datetime.now().isoformat()
    }

    wishlist.append(item)
    save_wishlist(wishlist)

    return jsonify({'success': True, 'item': item})

@app.route('/api/wishlist/<item_id>/refetch', methods=['POST'])
def refetch_item(item_id):
    wishlist = load_wishlist()

    for item in wishlist:
        if item['id'] == item_id:
            info = fetch_product_info(item['url'])
            item['name'] = info['name']
            item['brand'] = info['brand']
            item['price'] = info['price']
            item['image'] = info['image']
            item['error'] = info['error']
            item['updated_at'] = datetime.now().isoformat()
            save_wishlist(wishlist)
            return jsonify({'success': True, 'item': item})

    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/api/wishlist/<item_id>/desire-price', methods=['POST'])
def update_desire_price(item_id):
    data = request.json
    desire_price = data.get('desire_price', '')
    wishlist = load_wishlist()

    for item in wishlist:
        if item['id'] == item_id:
            item['desire_price'] = desire_price
            save_wishlist(wishlist)
            return jsonify({'success': True, 'item': item})

    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/api/wishlist/<item_id>', methods=['DELETE'])
def delete_from_wishlist(item_id):
    wishlist = load_wishlist()
    wishlist = [item for item in wishlist if item['id'] != item_id]
    save_wishlist(wishlist)
    return jsonify({'success': True})

@app.route('/api/wishlist/<item_id>/bought', methods=['POST'])
def toggle_bought_status(item_id):
    data = request.json
    bought = data.get('bought', True)
    wishlist = load_wishlist()

    for item in wishlist:
        if item['id'] == item_id:
            item['bought'] = bought
            item['bought_at'] = datetime.now().isoformat() if bought else None
            save_wishlist(wishlist)
            return jsonify({'success': True, 'item': item})

    return jsonify({'success': False, 'error': 'Item not found'}), 404

if __name__ == '__main__':
    import webbrowser
    from threading import Timer

    port = 5001
    is_frozen = getattr(sys, 'frozen', False)

    # Open browser after short delay when running as exe
    if is_frozen:
        Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()

    app.run(debug=not is_frozen, port=port, use_reloader=not is_frozen)
