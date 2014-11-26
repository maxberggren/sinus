import mechanize

url = "https://www.youtube.com/watch?v=oswUssXzFlY"

br = mechanize.Browser()


response = br.open(url) 

for link in br.links():
    print link.text, link.url