import argparse
import os
import requests
from urllib.parse import urljoin, unquote, urlsplit

from pathvalidate import sanitize_filename
from pathlib import Path
from bs4 import BeautifulSoup


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError
    

def download_txt(response, filename, folder='books/'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(folder,f'{sanitize_filename(filename)}.txt')
    with open(filepath, 'wb') as file:
        file.write(response.content)
  


def parse_book_page(response, template_url):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find(id='content').find('h1')
    title_text = title_tag.text
    book_title, book_author = title_text.split(" :: ")
    image_url = soup.find('div', class_='bookimage').find('img')['src']
    full_image_url = urljoin(template_url, image_url)
    book_comments = soup.find_all('div', class_='texts')
    book_comments_text = [comment_book.find('span', class_='black').text for comment_book in book_comments]
    book_genres = soup.find('span', class_='d_book').find_all('a')
    book_geners = [genres.text for genres in book_genres]
    book_parameters = {
        'name': book_title.strip(),                   
        'author': book_author.strip(), 
        'image': full_image_url,
        'comments': book_comments_text,
        'genre': book_geners
    }
    return book_parameters


def download_image(image_url, folder='images/'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(image_url)
    response.raise_for_status() 
    filename = urlsplit(image_url).path.split('/')[-1]
    filepath = os.path.join(folder, filename)
    with open(unquote(filepath), 'wb') as file:
        file.write(response.content)
    return filepath


def download_books():
    os.makedirs("books", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    parser = argparse.ArgumentParser(
        description='скачивает книги и картинки к скаченным книгам'
    )
    parser.add_argument('--start_id', type=int, help='Начальный индекс книги', default=1)
    parser.add_argument('--end_id', type=int, help='Конечнный индекс книги', default=11)
    args = parser.parse_args()
    for number in range(args.start_id, args.end_id):
        params = {'id': number}
        url = f"https://tululu.org/txt.php"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status() 
            check_for_redirect(response)
            book_url = 'https://tululu.org/b{}/'
            book_response = requests.get(book_url.format(number))
            book_response.raise_for_status() 
            check_for_redirect(book_response)
            book_parameters = parse_book_page(book_response, book_url)
            download_txt(response, book_parameters['name'])
            download_image(book_parameters['image'])
        except requests.exceptions.HTTPError:
            print("Такой книги нет")


if __name__ == '__main__':            
    download_books()

