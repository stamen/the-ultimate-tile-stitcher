# the-ultimate-tile-stitcher

It can scrape things for you and stitch them for you too.

To install: `pip install -r requirements.txt`
It needs `python 3.6`.


Make a geojson containing `Polygon` outlines of areas you want to scrape

Then:

1. `mkdir tiles`
2. `python scraper.py --poly poly.geojson --zoom 19 --url http://.../abcd/{z}/{x}/{y}@2x.png --out-dir tiles`
3. `python stitcher.py --dir tiles --out-file out.png`

If you the scraper repeatedly fails in downloading certain tiles, and the tile urls (put into `failed_urls.txt`) work, then you could set `--max-connections` to something low (default is 8) or increase `--retries` (default is 10)