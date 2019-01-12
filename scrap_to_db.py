import datetime

from mongoengine import connect

from scraper.over_scraper import Scraper
from models.mongo_models import Author, Article


def create_entries(article_item: dict):
    author_obj = Author.objects(nickname=article_item.get('author')).modify(
        upsert=True,
        new=True,
        nickname=article_item.get('author'),
        profile_link=article_item.get('author_profile_link')
    )
    try:
        last_post_date = datetime.datetime.utcfromtimestamp(article_item.get('last_post_ts'))
        if not Article.objects(
            article_id=article_item.get('id'),
            last_post_dt=last_post_date
        ):
            _ = Article.objects(article_id=article_item.get('id')).modify(
                upsert=True,
                new=True,
                article_id=article_item.get('id'),
                author=author_obj,
                url=article_item.get('url'),
                title=article_item.get('title'),
                post_content=article_item.get('post'),
                location=article_item.get('location'),
                post_count=article_item.get('posts_count'),
                views_count=article_item.get('views_count'),
                last_post_dt=last_post_date,
            ).save()
    except Exception as err:
        print(article_item)
        print(err)


if __name__ == '__main__':
    connect('Overbot')

    s = Scraper(raise_exceptions=False, r_timeout=10, pause=10)
    result = s.get_content(1, 10)
    for item in result:
        create_entries(item)
