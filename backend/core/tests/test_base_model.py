from django.test import TestCase
from django.utils import timezone
from django.db import models
from core.models.base_model import BaseModel

# Create a concrete implementation of BaseModel for testing
class TestModel(BaseModel):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core'

class BaseModelTestCase(TestCase):
    def setUp(self):
        self.test_model = TestModel.objects.create(name="Test Instance")

    def test_uuid_primary_key(self):
        """Test that UUID primary key is generated automatically"""
        self.assertIsNotNone(self.test_model.id)
        self.assertTrue(isinstance(self.test_model.id, str))

    def test_timestamps(self):
        """Test automatic timestamp fields"""
        self.assertIsNotNone(self.test_model.created_at)
        self.assertIsNotNone(self.test_model.updated_at)
        self.assertTrue(self.test_model.created_at <= timezone.now())

    def test_soft_delete(self):
        """Test soft delete functionality"""
        self.assertFalse(self.test_model.is_deleted)
        self.assertIsNone(self.test_model.deleted_at)

        self.test_model.soft_delete()
        self.assertTrue(self.test_model.is_deleted)
        self.assertIsNotNone(self.test_model.deleted_at)

    def test_restore(self):
        """Test restore functionality"""
        self.test_model.soft_delete()
        self.test_model.restore()

        self.assertFalse(self.test_model.is_deleted)
        self.assertIsNone(self.test_model.deleted_at)

    def test_ordering(self):
        """Test default ordering by created_at descending"""
        TestModel.objects.create(name="Another Test")
        models = TestModel.objects.all()
        self.assertTrue(models[0].created_at >= models[1].created_at)