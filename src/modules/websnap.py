import asyncio
import os
import argparse
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import shutil
import matplotlib.pyplot as plt
from PIL import Image


class ImageViewer:
    """Image viewer that allows navigation through a dictionary of images."""

    def __init__(self, img_dict):
        self.images = list(img_dict.keys())
        self.img_paths = img_dict
        self.current_index = 0
        self.viewer_open = True

        self.fig, self.ax = plt.subplots()
        self.btn_prev = plt.Button(plt.axes([0.1, 0.01, 0.3, 0.075]), 'Previous')
        self.btn_next = plt.Button(plt.axes([0.6, 0.01, 0.3, 0.075]), 'Next')

        self.btn_prev.on_clicked(self.previous_image)
        self.btn_next.on_clicked(self.next_image)

        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('close_event', self.on_close)

        self.view_image()
        plt.show()

    def view_image(self):
        title = self.images[self.current_index]
        img_path = self.img_paths[title]
        try:
            img = Image.open(img_path)
            self.ax.clear()
            self.ax.imshow(img)
            self.ax.set_title(title)
            self.ax.axis('off')
            plt.draw()
        except Exception as e:
            print(f"Error loading image: {e}")

    def next_image(self, event=None):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.view_image()
        else:
            print("You are at the last image.")

    def previous_image(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.view_image()
        else:
            print("You are at the first image.")

    def on_key_press(self, event):
        if event.key == 'right':
            self.next_image()
        elif event.key == 'left':
            self.previous_image()
        elif event.key == 'q':
            self.on_close(event)

    def on_close(self, event):
        self.viewer_open = False
        plt.close(self.fig)


class Snap:
    @staticmethod
    async def take_screenshot(url, filename='screenshot.png', save_dir='./tmp/'):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)

            os.makedirs(save_dir, exist_ok=True)
            full_path = os.path.join(save_dir, filename)
            await page.screenshot(path=full_path)
            print(f"Screenshot saved to: {full_path}")

            await browser.close()


async def main():
    parser = argparse.ArgumentParser(description='Take a screenshot of a webpage.')
    parser.add_argument('--url', type=str, help='The URL of the webpage to screenshot.')
    parser.add_argument('-o', '--output', type=str, help='Optional output filename for the screenshot (default: <webpage>.png)')
    parser.add_argument('-f', '--fromfile', type=str, help='Optional file containing a list of URLs to screenshot (one per line).')
    parser.add_argument('-vi', '--view', action='store_true', help='Optional auto view the images after taken')
    parser.add_argument('-cf', '--clearafter', action='store_true', help='Clear images after viewing')

    args = parser.parse_args()

    if not args.url and not args.fromfile:
        parser.error('Please include either --url or --fromfile. Neither provided.')

    if args.fromfile:
        with open(args.fromfile, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
    else:
        urls = [args.url]

    img_dict = {}
    for url in urls:
        purl = urlparse(url)
        safe_hostname = (purl.hostname or "snapshot").replace('.', '_')
        webpage = purl.path.strip('/').replace('/', '_') or 'index'
        root_path = "tmp"
        save_directory = f'./{root_path}/{safe_hostname}/screenshots/'
        filename = args.output if args.output else f'{webpage}.png'

        await Snap.take_screenshot(url, filename, save_directory)

        full_image_path = os.path.join(save_directory, filename)
        img_dict[filename] = full_image_path

    if args.view and img_dict:
        ImageViewer(img_dict)
        if args.clearafter:
            try:
                shutil.rmtree(f'./{root_path}')
                print("cleared done!")
            except Exception as e:
                print(f"Error clearing: {e}")



def core(cliargs):
        asyncio.run(main(cliargs))  # Use asyncio.run to run the core async function

if __name__ == "__main__":
    asyncio.run(main())
