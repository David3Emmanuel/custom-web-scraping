from . import parse

with open("custom-web-scraping/sample.html") as file:
    html = file.read()

parsed = parse(html)
print(parsed)
