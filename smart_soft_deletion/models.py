from django.db import models


def _related_on_delete(obj, *args, **kwargs):
    for relation in obj._meta._relation_tree:
        on_delete = relation.remote_field.on_delete
        
        if on_delete in [None, models.DO_NOTHING]:
            continue
        
        filter = {relation.name: obj}
                
        related_queryset = relation.model.objects_with_deleted.filter(**filter)
        #print('related_queryset: ', related_queryset)
        
        if on_delete is models.CASCADE:
            #print('CASCADE')
            related_queryset.delete(*args, **kwargs)
        
        elif on_delete is models.SET_NULL:
            #print('SET_NULL')
            kwargs[str(relation.name)] = None
            related_queryset.update(*args, **kwargs)
        
        elif on_delete is models.PROTECT:
            #print('PROTECT')
            if related_queryset.count() > 0:
                raise models.ProtectedError()
    
        else:
            print('on_delete: ', on_delete)
            raise NotImplementedError('Soft Deletion does not support fields with on_delete SET and SET_DEFAULT')


class SoftDeletionQuerySet(models.query.QuerySet):
    """
    Ensure that bulk deleted is called.
    Django Docs: https://docs.djangoproject.com/en/dev/topics/db/queries/#deleting-objects
        If you’ve provided a custom delete() method on a model class and want to ensure
        that it is called, you will need to “manually” delete instances of that model
        (e.g., by iterating over a QuerySet and calling delete() on each object individually)
        rather than using the bulk delete() method of a QuerySet.
    """
    # Ref: https://stackoverflow.com/a/28730380/1323471
    
    def original_delete(self, *args, **kwargs):
        super().delete()
    
    def delete(self, *args, **kwargs):
        hard_deletion = kwargs.pop('hard_deletion', False)
        if hard_deletion:
            self.original_delete(*args, **kwargs)
        else:
            for obj in self:
                _related_on_delete(obj, *args, **kwargs)
            super(SoftDeletionQuerySet, self).update(is_deleted=True)
    
    def retore(self):
        self.update(is_deleted=True)


class SoftDeletionMixinMananger(models.Manager):
    def __init__(self, *args, **kwargs):
        self.with_deleted = kwargs.pop('deleted', False)
        super(SoftDeletionMixinMananger, self).__init__(*args, **kwargs)

    def original_queryset(self):
        return super().get_queryset()
    
    def get_queryset(self):
        # qs = self.original_queryset()
        qs = SoftDeletionQuerySet(self.model, using=self._db)
        if self.with_deleted:
            return qs
        else:
            return qs.filter(is_deleted=False)


class SoftDeletionMixin(models.Model):
    is_deleted = models.BooleanField(null=False, default=False)
    objects = SoftDeletionMixinMananger()
    objects_with_deleted = SoftDeletionMixinMananger(deleted=True)
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        hard_deletion = kwargs.get('hard_deletion', False)
        if hard_deletion:
            kwargs.pop('hard_deletion')
            super(SoftDeletionMixin, self).delete(*args, **kwargs)
        else:
            self.is_deleted = True
            _related_on_delete(self, *args, **kwargs)
            self.save()
    
    def restore(self):
        self.is_deleted = False
        self.save()
