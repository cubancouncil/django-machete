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
        return self.filter(status=STATUS_PUBLISHED)

class PublishedManager(models.Manager):
    def get_query_set(self):
        return PublishedQuerySet(self.model, using=self._db)
    
    def get_published(self):
        return self.get_query_set().get_published()

# Global field model

class GlobalModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(max_length=max([len(str(STATUS_DRAFT)), len(str(STATUS_PUBLISHED))]), db_index=True, choices=STATUS_OPTIONS, default=STATUS_PUBLISHED)
    objects = PublishedManager()
    
    class Meta:
        abstract = True
    
    def get_is_published(self):
        return self.status == STATUS_PUBLISHED
    
    is_published = property(get_is_published)
