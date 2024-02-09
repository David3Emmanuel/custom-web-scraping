from . import parse

with open("custom-web-scraping/sample.html") as file:
    html = file.read()

parsed = parse(html)
with open("custom-web-scraping/out.html", 'w') as file:
    print(parsed, file=file)
