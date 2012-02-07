from django.db import models

"""
Global model and queryset definitions. Add 'status', 'created' and 'modified' fields
"""

# Status choices

STATUS_DRAFT = 0
STATUS_PUBLISHED = 1
STATUS_OPTIONS = (
    (STATUS_DRAFT, u'Draft'),
    (STATUS_PUBLISHED, u'Published'),
)

"""
Global published QuerySet/Manager classes

Any custom methods need to be set in the QuerySet class and a proxy
method needs to be created in the Manager class so that chaining works
properly
"""

class PublishedQuerySet(models.query.QuerySet):
    def get_published(self):
        return self.filter(status=1)

class PublishedManager(models.Manager):
    def get_query_set(self):
        return PublishedQuerySet(self.model, using=self._db)
    
    def get_published(self):
        return self.get_query_set().filter(status=1)

# Global field model

class GlobalModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(max_length=1, choices=STATUS_OPTIONS, default=STATUS_PUBLISHED)
    objects = PublishedManager()
    
    class Meta:
        abstract = True
    
    def get_is_published(self):
        return self.status is 1
    
    is_published = property(get_is_published)
