import scrapy
import csv
import re
from functools import partial

class ScorptecSpider(scrapy.Spider):
    name = 'scorptec'
    download_delay = 3

    current_offset = 0

    def start_requests(self):
        endpoints = [
            { 'url3': 'notebooks', 'subid': '613' },
            { 'url3': 'gaming-notebooks', 'subid': '1032' },
            { 'url3': 'ultrabook', 'subid': '999' }
        ]

        for endpoint in endpoints:
            url3 = endpoint['url3']
            subid = endpoint['subid']

            yield self.infinite_scroll_request(
                offset = self.current_offset,
                callback = partial(self.parse, url3=url3, subid=subid),
                url3 = url3,
                subid = subid
            )

    def parse(self, response, url3, subid):
        # Parse the details of all returned products
        rows = response.css('.col-md-12')

        if not rows:
            self.logger.info("No rows found, exiting")
            return

        for product in rows:
            intro = product.css('.item_intro::text').get()

            if intro:
                price = product.css('.item_price_discounted::text').get() or product.css('.item_price::text').get()

                if price and len(re.findall('\d+', price)) > 0:
                    data = {
                        'price': price,
                        'intro': self.clean_intro(intro),
                        'url': product.css('.desc a::attr(href)').get()
                    }

                    clean_data = self.add_missing_data(self.clean_data(data))

                    self.logger.info(clean_data)

                    yield clean_data
                else:
                    self.logger.info("Skipping row, no price found")
            else:
                self.logger.info("Skipping row, no intro found")

        # Handle the infinite scroll
        self.current_offset += 1
        yield self.infinite_scroll_request(offset = self.current_offset, callback = partial(self.parse, url3 = url3, subid = subid), url3 = url3, subid = subid)

    def infinite_scroll_request(self, offset, callback, url3, subid):
        infinite_scroll_url = 'https://www.scorptec.com.au/ajax/product_list'

        formdata = {
            'action': 'get_list',
            'order_by': 'popularity|desc',
            'display': 'list',
            'offset': str(offset),
            'fetch_type': 'scroll',
            'url1': 'product',
            'url2': 'notebooks',
            'url3': url3,
            'catid': '21',
            'subid': subid
        }

        return scrapy.FormRequest(url=infinite_scroll_url, callback=callback, formdata=formdata)

    # Some intros are  malformed (full stop instead of comma for specs).
    # We fix them so the rest of the parsing doesn't break
    def clean_intro(self, intro):
        intro = intro.replace('Dell Latitude 7490 Ultrabook.', 'Dell Latitude 7490 Ultrabook,')
        return intro

    # Some laptops are missing some specs, we can hardcode them as we can look up
    # their data manually
    def add_missing_data(self, product):
        # Notebooks
        if product['name'] == 'Lenovo IdeaPad V130 Iron Grey Notebook':
            product['graphics_card'] = {
                'brand': 'Intel',
                'discrete': False,
                'raw_name': 'Intel HD Graphics 620',
                'model': 'HD',
                'model_power': 0,
                'model_number': '620',
                'name': 'Intel HD 620'
            }

        if product['name'] == 'Acer Spin 5 2-in-1 Notebook':
            product['weight_kgs'] = '1.6'

        if product['name'] == 'Dell Latitude 3590 Notebook':
            product['weight_kgs'] = '2.02'

        if product['name'] == 'HP ProBook 645 G4 Notebook':
            product['storage'] = [{
                "hdd_gbs": "256",
                "is_ssd": True
            }]

        # Gaming Laptops
        if product['name'] == 'Acer Nitro Gaming Notebook':
            product['weight_kgs'] = '2.3'

        if product['name'] == 'Acer Predator Helios G3 Gaming Notebook':
            product['weight_kgs'] = '2.56'

        if product['name'] == 'Aorus 15-W9 Gaming Notebook':
            product['weight_kgs'] = '2.4'

        if product['name'] == 'Aorus 15-X9 Gaming Notebook':
            product['weight_kgs'] = '2.4'

        if product['name'] == 'ASUS TUF FX505GE Gaming Notebook':
            product['weight_kgs'] = '2.2'

        if product['name'] == 'ASUS ROG Zephyrus GX531GM Gaming Notebook':
            product['weight_kgs'] = '2.1'

        if product['name'] == 'MSI GS65 Stealth Black Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI GS75 8SE Stealth Gaming Notebook':
            product['weight_kgs'] = '2.25'

        if product['name'] == 'MSI GS75 8SF Stealth Gaming Notebook':
            product['weight_kgs'] = '2.25'

        if product['name'] == 'MSI GS65 Stealth 9SE Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI GE75 Raider Black Gaming Notebook':
            product['weight_kgs'] = '2.64'

        if product['name'] == 'MSI GE75 Raider Gaming Notebook':
            product['weight_kgs'] = '2.61'

        if product['name'] == 'MSI GE75 Raider 9SE Gaming Notebook':
            product['weight_kgs'] = '2.64'

        if product['name'] == 'MSI GE63 Raider Black Gaming Notebook':
            product['weight_kgs'] = '2.6'

        if product['name'] == 'MSI GT75 8SG Titan Black Gaming Notebook':
            product['weight_kgs'] = '4.56'

        if product['name'] == 'MSI GT75 8SF Black Gaming Notebook':
            product['weight_kgs'] = '4.56'

        if product['name'] == 'MSI P65 9SE Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI P65 9SF Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI P65 Creator 9SE Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI P75-9SF Gaming Notebook':
            product['weight_kgs'] = '2.25'

        # Ultrabooks
        if product['name'] == 'Toshiba Portege X20W Ultrabook':
            product['graphics_card'] = {
                'brand': 'Intel',
                'discrete': False,
                'raw_name': 'Intel UHD Graphics 620',
                'model': 'UHD',
                'model_power': 0,
                'model_number': '620',
                'name': 'Intel UHD 620'
            }

        if product['name'] == 'Acer Swift 5 Ultrabook':
            product['weight_kgs'] = '0.97'

        if product['name'] == 'Lenovo ThinkPad X1 Yoga Gen 3 Ultrabook':
            product['weight_kgs'] = '1.4'

        if product['name'] == 'Dell Latitude 7490 Ultrabook':
            product['weight_kgs'] = '1.4'

        if product['name'] == 'MSI GE75 Raider 9SF Gaming Notebook':
            product['weight_kgs'] = '2.64'

        if product['name'] == 'MSI GL63 8SD Gaming Notebook':
            product['weight_kgs'] = '2.3'

        if product['name'] == 'MSI GL63 8SC Gaming Notebook':
            product['weight_kgs'] = '2.3'

        if product['name'] == 'MSI GS65 Stealth 9SF Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI GS65 Stealth 9SG Gaming Notebook':
            product['weight_kgs'] = '1.9'

        if product['name'] == 'MSI GS75 9SG Gaming Notebook':
            product['weight_kgs'] = '2.28'

        if product['name'] == 'MSI GS75 Stealth 9SE Gaming Notebook':
            product['weight_kgs'] = '2.28'

        if product['name'] == 'MSI GT75 Titan 9SF Gaming Notebook':
            product['weight_kgs'] = '4.56'

        if product['name'] == 'MSI GT75 Titan 9SG Gaming Notebook':
            product['weight_kgs'] = '4.56'

        return product

    # Clean various fields and interpret the intro into more structured data
    def clean_data(self, product):
        self.logger.info(product)

        # Price has newlines and other garbage in it, we just want the digits and
        # the decimal place
        price = re.findall('[\d.]+', product['price'])[0]

        # The intro is a comma separated bunch of fields. We're going
        # to try and infer the specs from it
        #
        # A lot of the data seems to have space issues so we also strip the prefixed/postfixed
        # whitespace from everything
        intro_csv = [field.strip() for field in list(csv.reader([product['intro']]))[0]]
        self.logger.info(intro_csv)

        # The first field seems to _always_ be laptop name
        name = intro_csv[0]
        self.logger.info(name)

        # The first word of the name also seems to be the brand
        brand = name.split(' ', 1)[0]

        # CPU seems to be consistently in the second column. Unfortunately no GHz
        cpu = intro_csv[1]

        # Ram seems to follow CPU. Typically it is either in the format "16GB" or "8GB (1x 8GB) RAM". For our purposes
        # we can just take the total
        #
        # We're also assuming all ram is in GBs
        ram_gbs = re.findall('[\d.]+', intro_csv[2])[0]

        # The hard drive string typically contains "256GB" "SSD" "1TB" and "HDD" in addition to other text
        # that is difficult to normalize. Additionally a laptop may have multiple hard drives.
        #
        # In our case we look for the pairing of a size and "SSD" or "HDD" and use that to generate
        # a hard drive array
        storage = []

        # Parentehsis breaks everything, lets get rid of all parenthesised text
        #
        # This won't work for nested parenthesis but they don't seem to occur
        hdd_raw_no_parenthesis = re.sub(r'\(.*\)', '', intro_csv[3])
        hdd_raw_strings = hdd_raw_no_parenthesis.split() # ['512GB', '(2x', '256GB', 'SSD)', 'M.2', 'PCIE', 'SSD', '+', '1TB', 'HDD']
        self.logger.info(hdd_raw_strings)

        hdd_gbs = None
        for hdd_raw_string in hdd_raw_strings:
            # If we haven't found a size string (i.e. 512GB or 1TB) look for it.
            if hdd_gbs == None:
                if hdd_raw_string.endswith("GB") or hdd_raw_string.endswith("TB"):
                    hdd_gbs = re.findall('[\d.]+', hdd_raw_string)[0]
                    if hdd_raw_string.endswith("TB"):
                        hdd_gbs = str(int(hdd_gbs) * 1024)
            else:
                # We have a previous size string, now we want 'SSD' or 'HDD'
                if hdd_raw_string == 'SSD' or hdd_raw_string == 'HDD' or hdd_raw_string == 'SSHD':
                    is_ssd = hdd_raw_string == 'SSD'
                    storage.append({
                        'hdd_gbs': hdd_gbs,
                        'is_ssd': is_ssd
                    })
                    hdd_gbs = None

        # Screen size seems to have a simple format: <x>inch (HD|FHD) (IPS). For our used
        # case we'll just take size, though extending to quality markers in the future
        # would be nice
        #
        # It's _usually_ in index 4 but once we found one in index 5, so we search for a
        # number ending in inch.
        screen_size_inches = None
        for field in intro_csv:
            if 'inch' in field.lower():
                screen_size_inches = re.findall('[\d.]+', field)[0]
                break

        # All laptops seem to have a "graphics" section. We assume that "Intel" means
        # onboard and anything else means discrete
        #
        # We also cut this up into discrete parts to try and make it easier to parse
        #
        # This isn't always in the same position so we search for a list of known brands.
        graphics_card = {}
        for field in intro_csv:
            lfield = field.lower()
            is_graphics_field = False
            if lfield.startswith('geforce'):
                is_graphics_field = True
                graphics_card['brand'] = 'GeForce'
                graphics_card['discrete'] = True
            elif lfield.startswith('radeon'):
                is_graphics_field = True
                graphics_card['brand'] = 'Radeon'
                graphics_card['discrete'] = True
            elif lfield.startswith('intel'):
                is_graphics_field = True
                graphics_card['brand'] = 'Intel'
                graphics_card['discrete'] = False

            if is_graphics_field:
                graphics_card['raw_name'] = field

                # Set the graphics card model and power according to my
                # completely unbiased opinions
                if 'geforce' in lfield and 'rtx' in lfield:
                    graphics_card['model'] = 'RTX'
                    graphics_card['model_power'] = 4
                elif 'geforce' in lfield and 'gtx' in lfield:
                    graphics_card['model'] = 'GTX'
                    graphics_card['model_power'] = 3
                elif 'geforce' in lfield and 'mx' in lfield:
                    graphics_card['model'] = 'MX'
                    graphics_card['model_power'] = 2
                elif 'radeon' in lfield and 'rx' in lfield:
                    graphics_card['model'] = 'RX'
                    graphics_card['model_power'] = 2
                elif 'radeon' in lfield and 'vega' in lfield:
                    graphics_card['model'] = 'Vega'
                    graphics_card['model_power'] = 0
                elif 'intel' in lfield and 'uhd' in lfield:
                    graphics_card['model'] = 'UHD'
                    graphics_card['model_power'] = 1
                elif 'intel' in lfield and 'hd' in lfield:
                    graphics_card['model'] = 'HD'
                    graphics_card['model_power'] = 0
                elif 'intel' in lfield:
                    graphics_card['model'] = 'HD'
                    graphics_card['model_power'] = 0
                else:
                    self.logger.info('UNKNOWN GRAPHICS CARD MODEL: ' + lfield)

                # Grab all the numbers out of the string. We're going to assume things
                graphics_numbers = re.findall('[\d]+', lfield)

                # Assume the first number in the string is the model number
                if len(graphics_numbers) > 0:
                    graphics_card['model_number'] = re.findall('[\d]+', lfield)[0]
                elif 'intel' in lfield:
                    # If we don't know the model number 99% of the time it's a 620
                    graphics_card['model_number'] = '620'

                # Assume the second number is the amount of memory
                if len(graphics_numbers) > 1:
                    graphics_card['memory_gbs'] = int(graphics_numbers[1])

                    # If our memory exceeds 32GB then we are definitely not a graphics
                    # card and this is a false positive
                    if graphics_card['memory_gbs'] > 32:
                        graphics_card = {}
                        continue

                    # Also, if the string contains the word "SSD". It's not a
                    # graphics card
                    if 'ssd' in lfield:
                        graphics_card = {}
                        continue

                # Compute a "nice" name from the data we have. Intel has
                # slightly different naming conventions so we also account
                # for them here
                if 'model' in graphics_card:
                    graphics_card['name'] = graphics_card['brand']
                    graphics_card['name'] += ' ' + graphics_card['model']
                    if graphics_card['brand'] == 'Intel':
                        graphics_card['name'] += ' '
                    if 'model_number' in graphics_card:
                        graphics_card['name'] += graphics_card['model_number']
                    if 'memory_gbs' in graphics_card and graphics_card['memory_gbs'] > 0:
                        graphics_card['name'] += ' (' + str(graphics_card['memory_gbs']) + 'GB)'
                else:
                    graphics_card['name'] = graphics_card['raw_name']

                break


        # Weight doesn't always appear at the same index so we need
        # to stang for a string ending with "kg"
        weight_kgs = None
        for field in intro_csv:
            if field.endswith('kg'):
                weight_kgs = re.findall('[\d.]+', field)[0]
                break

        return {
            'name': name,
            'brand': brand,
            'cpu': cpu,
            'ram_gbs': ram_gbs,
            'storage': storage,
            'screen_size_inches': screen_size_inches,
            'graphics_card': graphics_card,
            'weight_kgs': weight_kgs,
            'price_aud': price,
            'intro': product['intro'],
            'url': product['url']
        }
