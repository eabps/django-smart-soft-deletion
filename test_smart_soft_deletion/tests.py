from django.test import TestCase
from django.db import models

from . models import Country, Category, Industry, Product


class DeleteTestCase(TestCase):
    def setUp(self):
        self.japan = Country.objects.create(name="Japan")
        self.usa = Country.objects.create(name="USA")
        self.toys = Category.objects.create(name="Toys")
        self.sony = Industry.objects.create(name="Sony", country=self.japan)
        self.microsoft = Industry.objects.create(name="Microsoft", country=self.usa)
        self.play_station = Product.objects.create(name="Play Station", category=self.toys, industry=self.sony)
        self.xbox = Product.objects.create(name="Xbox", category=self.toys, industry=self.microsoft)
    
    def test_create(self):
        self.assertEqual("Japan", Country.objects.get(name='Japan').name)
        self.assertEqual(2, Industry.objects.count())
        self.assertEqual("Toys", Category.objects.get(name='Toys').name)
        self.assertEqual("Xbox", Product.objects.get(name='Xbox').name)
        self.assertEqual(2, Product.objects.count())
    
    def test_soft_deletion_and_restore(self):
        self.assertEqual(False, self.xbox.is_deleted)
        
        # DELETE
        self.xbox.delete()
        self.xbox.refresh_from_db()
        self.assertEqual(True, self.xbox.is_deleted)
                
        # RESTORE
        self.xbox.restore()
        self.assertEqual(False, self.xbox.is_deleted)

        """
        # ON_DELETE = SET (No implemented yet)
        """
        
    def test_filter_get_queryset(self):
        self.assertEqual(2, Industry.objects.all().count())
        self.assertEqual(2, Industry.objects_with_deleted.all().count())
        self.microsoft.delete()
        self.assertEqual(1, Industry.objects.all().count())
        self.assertEqual(2, Industry.objects_with_deleted.all().count())
    
    def test_hard_deletion(self):
        self.assertEqual(False, self.xbox.is_deleted)

        # HARD DELETION
        self.xbox.delete(hard_deletion=True)
        with self.assertRaises(Product.DoesNotExist):
            self.xbox.refresh_from_db()
    
    def test_soft_deletion_with_fk(self):
        # CASCADE
        self.assertEqual(self.xbox.industry, self.microsoft)
        self.assertEqual(False, self.xbox.is_deleted)
        self.assertEqual(False, self.microsoft.is_deleted)

        self.microsoft.delete()
        self.xbox.refresh_from_db()
        self.assertEqual(True, self.xbox.is_deleted)
        
        # SET_NULL
        self.assertEqual(self.japan, self.sony.country)
        self.assertEqual(False, self.japan.is_deleted)
        self.assertEqual(False, self.sony.is_deleted)
        
        self.japan.delete()
        self.sony.refresh_from_db()
        self.assertEqual(None, self.sony.country)
        self.assertEqual(False, self.sony.is_deleted)
        
        """
        # ON_DELETE = SET (No implemented yet)
        """

    
    def test_hard_deletion_with_fk(self):
        self.assertEqual(False, self.sony.is_deleted)
        self.assertEqual(False, self.play_station.is_deleted)

        self.sony.delete(hard_deletion=True)
        with self.assertRaises(Industry.DoesNotExist):
            self.sony.refresh_from_db()

        with self.assertRaises(Product.DoesNotExist):
            self.play_station.refresh_from_db()
            
    
    def test_queryset_soft_deletion(self):
        Product.objects.all().delete()
        self.assertEqual(0, Product.objects.all().count())
        self.assertEqual(2, Product.objects_with_deleted.all().count())
    
    def test_queryset_hard_deletion(self):
        Product.objects.all().delete(hard_deletion=True)
        self.assertEqual(0, Product.objects.all().count())
        self.assertEqual(0, Product.objects_with_deleted.all().count())
    
    def test_queryset_soft_deletion_with_fk(self):
        Industry.objects.all().delete()
        self.assertEqual(0, Product.objects.all().count())
        self.assertEqual(2, Product.objects_with_deleted.all().count())
        
        # CASCADE
        play_station = Product.objects_with_deleted.get(name="Play Station")
        sony = Industry.objects_with_deleted.get(name="Sony")
        self.assertEqual(play_station.industry, sony)
        
        # SETNULL
        Country.objects.all().delete()
        sony.refresh_from_db()
        self.assertEqual(None, sony.country)
    
    def test_queryset_hard_deletion_with_fk(self):
        # CASCADE
        Industry.objects.all().delete(hard_deletion=True)
        self.assertEqual(0, Industry.objects.all().count())
        self.assertEqual(0, Industry.objects_with_deleted.all().count())
        self.assertEqual(0, Product.objects.all().count())
        self.assertEqual(0, Product.objects_with_deleted.all().count())
        
        # SETNULL
        brazil = Country.objects.create(name='Brazil')
        bluboard = Industry.objects.create(name='Bluboard', country=brazil)
        Country.objects.all().delete(hard_deletion=True)
        bluboard.refresh_from_db()
        self.assertEqual(None, bluboard.country)


class RestoreTestCase(TestCase):
    def setUp(self):
        self.japan = Country.objects.create(name="Japan")
        self.usa = Country.objects.create(name="USA")
        self.toys = Category.objects.create(name="Toys")
        self.sony = Industry.objects.create(name="Sony", country=self.japan)
        self.microsoft = Industry.objects.create(name="Microsoft", country=self.usa)
        self.play_station = Product.objects.create(name="Play Station", category=self.toys, industry=self.sony)
        self.xbox = Product.objects.create(name="Xbox", category=self.toys, industry=self.microsoft)
    
    def test_restore(self):
        self.xbox.delete()
        self.assertEqual(True, self.xbox.is_deleted)
        self.xbox.restore()
        self.assertEqual(False, self.xbox.is_deleted)
    

    def test_restore_with_fk_deleted(self):
        self.sony.delete()
        self.play_station.refresh_from_db()
        self.assertEqual(True, self.play_station.is_deleted)
        
        # CASCADE
        with self.assertRaises(ValueError):
            self.play_station.restore()
        
        # SETNULL
        self.japan.delete()
        self.sony.refresh_from_db()
        self.sony.restore()
        self.assertEqual(None, self.sony.country)


class CreateTestCase(TestCase):
    def setUp(self):
        self.japan = Country.objects.create(name="Japan")
        self.usa = Country.objects.create(name="USA")
        self.toys = Category.objects.create(name="Toys")
        self.sony = Industry.objects.create(name="Sony", country=self.japan)
        self.microsoft = Industry.objects.create(name="Microsoft", country=self.usa)
        self.play_station = Product.objects.create(name="Play Station", category=self.toys, industry=self.sony)
        self.xbox = Product.objects.create(name="Xbox", category=self.toys, industry=self.microsoft)
    
    def test_create_with_fk_deleted(self):
        self.japan.delete()
        self.japan.refresh_from_db()
        
        with self.assertRaises(ValueError):
            honda = Industry.objects.create(name='Honda', country=self.japan)
    