import os
import argparse
import shapely.geometry
import asyncio
import aiohttp
import json
from random import random

from utils import tile2latlon, latlon2tile

BASE_WAIT = 0.5

def parse_args():
    parser = argparse.ArgumentParser(description='scrape tiles from a tiled map service')
    parser.add_argument('--poly', required=True, type=str, help='path to geojson containnig bounding polygon(s) to scrape within in lat lon')
    parser.add_argument('--zoom', required=True, type=int, help='zoom level to scrape at')
    parser.add_argument('--url', required=True, type=str, help='Map service url in http://...{z}/{x}/{y}... format')
    parser.add_argument('--out-dir', required=True, type=str, help='Folder to output to')
    parser.add_argument('--max-connections', required=False, type=int, default=8, help='Max concurrent connections')
    parser.add_argument('--retries', required=False, type=int, default=10, help='Retries per tile')
    opts = parser.parse_args()

    with open(opts.poly, 'r') as geojf:
        opts.poly = json.load(geojf)

    return opts


# this is inefficient and slow, but also good enough
def tile_idxs_in_poly(poly : shapely.geometry.Polygon, zoom : int):
    min_lon, min_lat, max_lon, max_lat = poly.bounds
    (min_x, max_y), (max_x, min_y) = latlon2tile(min_lat, min_lon, zoom), latlon2tile(max_lat, max_lon, zoom)
    for x in range(int(min_x), int(max_x) + 1):
        for y in range(int(min_y) , int(max_y) + 1):
            nw_pt = tile2latlon(x, y, zoom)[::-1] # poly is defined in geojson form
            ne_pt = tile2latlon(x + 1, y, zoom)[::-1] # poly is defined in geojson form
            sw_pt = tile2latlon(x, y + 1, zoom)[::-1] # poly is defined in geojson form
            se_pt = tile2latlon(x + 1, y + 1, zoom)[::-1] # poly is defined in geojson form
            if any(map(lambda pt : shapely.geometry.Point(pt).within(poly), 
                (nw_pt, ne_pt, sw_pt, se_pt))):
                yield x, y
            else:
                continue


async def fetch_and_save(session : aiohttp.ClientSession, url : str, retries : int, filepath : str, **kwargs):
    wait_for = BASE_WAIT
    for retry in range(retries):
        response = await session.get(url, params=kwargs)
        try:
            response.raise_for_status()
            img = await response.read()
            with open(filepath, 'wb') as fp:
                fp.write(img)
            return True
        except aiohttp.client_exceptions.ClientResponseError:
            print('err')
            await asyncio.sleep(wait_for)
            wait_for = wait_for * (1.0 * random() + 1.0)
    return False

async def main():
    failed_urls = []

    opts = parse_args()
    
    os.makedirs(opts.out_dir, exist_ok=True)

    semaphore = asyncio.Semaphore(opts.max_connections)

    for feat in opts.poly['features']:
        poly = shapely.geometry.shape(feat['geometry'])

        async with aiohttp.ClientSession() as session:
            tasks = []
            urls = []
            for x, y in tile_idxs_in_poly(poly, opts.zoom):
                url = opts.url.format(z=opts.zoom, x=x, y=y)
                with (await semaphore):
                    filepath = os.path.join(opts.out_dir, '{}_{}_{}.png'.format(opts.zoom, x, y))
                    if os.path.isfile(filepath):
                        continue
                    ret = fetch_and_save(session, url, opts.retries, filepath)
                    urls.append(url)
                    tasks.append(asyncio.ensure_future(ret))
            
            res : list = await asyncio.gather(*tasks)
            n_failed = res.count(False)

            for i, url in enumerate(urls):
                if res[i] == False:
                    failed_urls.append(url)

    print('Downloaded {}/{}'.format(len(tasks) - n_failed, len(tasks)))
    return failed_urls

    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    failed_urls = loop.run_until_complete(main())
    if len(failed_urls) > 0:
        with open('failed_urls.txt', 'w') as fp:
            fp.writelines(failed_urls)
