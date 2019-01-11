import datetime

from mongoengine import fields, Document, connect


class TimestampedDocument(Document):
    """
    Subclass this to add auto-creation/modification dates generation.

    """

    meta = {'abstract': True}

    creation_date = fields.DateTimeField()
    modified_date = fields.DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        if not self.creation_date:
            self.creation_date = datetime.datetime.now()
        self.modified_date = datetime.datetime.now()
        return super().save(*args, **kwargs)


class Author(Document):

    nickname = fields.StringField(required=True, unique=True, max_length=255)
    profile_link = fields.URLField(required=True)


class Article(TimestampedDocument):

    meta = {
        'indexes': [
            'article_id',
            '$author'
        ]
    }

    article_id = fields.IntField(required=True, unique=True)
    author = fields.ReferenceField(Author, reverse_delete_rule=fields.DO_NOTHING)
    url = fields.URLField(required=True)
    title = fields.StringField(required=True)
    post_content = fields.StringField(required=True)
    location = fields.StringField()
    post_count = fields.IntField(default=0)
    views_count = fields.IntField(default=0)
    last_post_dt = fields.DateTimeField(default=datetime.datetime.now)
    tags = fields.ListField(fields.StringField(max_length=30))
