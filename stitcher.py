import os
from PIL import Image
import argparse
import glob
import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description='stitch tiles scraped by scraper.py')
    parser.add_argument('--dir', required=True, type=str, help='directory containing times, saved in {zoom}_{X}_{Y} form')
    parser.add_argument('--out-file', required=True, type=str, help='output filename')
    opts = parser.parse_args()
    return opts

def main():
    opts = parse_args()
    search_path = os.path.join(opts.dir, '*_*_*.png')
    
    filepaths = glob.glob(search_path)

    def xy(filepath):
        base = os.path.basename(filepath)
        z, x, y = filepath.split('_')
        y = os.path.splitext(y)[0]
        return int(x), int(y)

    yx = lambda filepath : xy(filepath)[::-1]

    filepaths = sorted(filepaths, key=xy)
    
    if len(filepaths) == 0:
        print('No files found')
        raise SystemExit

    tile_w, tile_h = Image.open(filepaths[0]).size

    xys = list(map(xy, filepaths))
    x_0, y_0 = min(map(lambda x_y : x_y[0], xys)), min(map(lambda x_y: x_y[1], xys))
    x_1, y_1 = max(map(lambda x_y : x_y[0], xys)), max(map(lambda x_y: x_y[1], xys))

    n_x, n_y = x_1 - x_0, y_1 - y_0

    out_w, out_h = n_x * tile_w, n_y * tile_h

    print('output image size:', out_w, out_h, 'tile size:', tile_w, tile_h)

    out_img = Image.new('RGB', (out_w, out_h), (0, 0, 255))
    for filepath in tqdm.tqdm(filepaths):
        x, y = xy(filepath)
        x, y = x - x_0, y - y_0
        tile = Image.open(filepath)
        out_img.paste(tile, box=(x * tile_w, y * tile_h, (x + 1) * tile_w, (y + 1) * tile_h))

    print('Saving')
    out_img.save(opts.out_file)

if __name__ == '__main__':
    main()