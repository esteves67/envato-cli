# see http://www.ibm.com/developerworks/aix/library/au-pythocli/index.html
import csv
import optparse
import urllib
import requests
import sys
from bs4 import BeautifulSoup, NavigableString
from tabulate import tabulate


def main():
    p = optparse.OptionParser()

    p.add_option('--pages', '-p', default=1, help="Number of pages to fetch")
    p.add_option('--search', '-s', default='', help="Term to search for")
    p.add_option('--output', '-o', default='table', help="The output format (csv or table)")

    options, arguments = p.parse_args()

    # how many pages to fetch
    page_count = int(options.pages)

    # fetch pages
    pages = []
    for page_number in range(1, page_count + 1):
        url = get_url(page_number, term=options.search)
        r = requests.get(url)

        if r.status_code == 302:
            # 302 means last page was exceeded
            # just break to save results
            break
        elif r.status_code != 200:
            exit('HTTP code is ' + str(r.status))

        # only save text to save space
        pages.append(r.text)

    # extract items
    items = []
    for page in pages:
        soup = BeautifulSoup(page, 'html.parser')

        product_list = soup.findAll(attrs={'class': 'product-list'})[0]
        for li in product_list.contents:
            if not isinstance(li, NavigableString):
                items.append(extract_item(li))

        # break if there are no more results (last page)
        if len(items) % 30 != 0:
            break

    if options.output == 'table':
        output_table(items)
    elif options.output == 'csv':
        output_csv(items)


def output_csv(items):
    listWriter = csv.DictWriter(
            sys.stdout,
            fieldnames=items[0].keys(),
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
    )
    listWriter.writeheader()
    for a in items:
        listWriter.writerow(a)


def output_table(items):
    table = tabulate(items, headers='keys')
    print(table)


def get_url(page=1, term=''):
    # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlencode
    query = {
        'page': page,
        'utf8': '✓',
        'term': term,
        'referrer': 'search',
        # grid
        'view': 'list',
        # empty (is newest), sales, rating, price-asc, price-desc
        'sort': 'trending',
        # this-year, this-month, this-week, this-day
        'date': '',
        # site-templates, wordpress, psd-templates, marketing, ecommerce, cms-themes, muse-templates, blogging,
        #  courses, sketch-templates, forums, static-site-generators, typeengine-themes
        'category': 'site-templates/admin-templates',
        # int
        'price_min': '',
        # int
        'price_max': '',
        # rank-0 (no sales) to rank-4 (top sellers)
        'sales': '',
        # empty, 1 to 4
        'rating_min': '',
    }
    return 'https://themeforest.net/search?' + urllib.parse.urlencode(query, True)


def extract_item(li):
    template = {}

    heading = li.findAll("h3")[0]
    template['name'] = heading.text.strip()
    template['link'] = heading.a['href']

    template['price'] = li.findAll(attrs={'class': 'product-list__price'})[0].text.strip()
    if len(li.findAll(attrs={'class': 'item-thumbnail__preview'})) == 1:
        template['demo'] = li.findAll(attrs={'class': 'item-thumbnail__preview'})[0].a['href']

    return template


if __name__ == '__main__':
    main()
