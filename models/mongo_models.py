import datetime

from mongoengine import fields, Document, EmbeddedDocument, signals


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


class Sentence(EmbeddedDocument):
    text = fields.StringField(required=True)
    price = fields.FloatField(min_value=0.0, max_value=100000)


class Author(Document):

    nickname = fields.StringField(required=True, unique=True, max_length=255)
    profile_link = fields.URLField(required=True)
    activity_index = fields.FloatField(default=0.0)


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
    sentences = fields.ListField(fields.EmbeddedDocumentField(Sentence))

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        author_articles=sender.objects(author=document.author).count()
        total_articles=sender.objects.count()
        document.author.activity_index = total_articles/author_articles
        document.author.save()


signals.post_save.connect(Article.post_save, sender=Article)
