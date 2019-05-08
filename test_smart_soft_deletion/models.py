from django.db import models

from smart_soft_deletion.models import SoftDeletionMixin


class Country(SoftDeletionMixin):
    name = models.CharField(max_length=64, unique=True, verbose_name="Name")

    def __str__(self):
        return "{}".format(self.name)


class Category(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")

    def __str__(self):
        return "{}".format(self.name)


class Founder(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")
    def __str__(self):
        return "{}".format(self.name)    


class Industry(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, verbose_name="Country")
    founders = models.ManyToManyField(Founder, verbose_name="Founders")

    def __str__(self):
        return "{}".format(self.name)


def create_category_default():
    return Category.objects.get_or_create(name='Default Category')


class Product(SoftDeletionMixin):
    name = models.CharField(max_length=128, unique=True, verbose_name="Name")
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, verbose_name="Industry")
    category = models.ForeignKey(Category, null=True, on_delete=models.SET(create_category_default), verbose_name="Category")

    def __str__(self):
        return "{}".format(self.name)
