from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from uuid import uuid4
import ipaddress
from core.models.audit_log_model import AuditLog

User = get_user_model()

class AuditLogModelTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create an audit log entry
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action='create',
            resource_type='TikTokAccount',
            resource_id=uuid4(),
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            changes={
                'before': {'name': None},
                'after': {'name': 'Test Account'}
            },
            metadata={
                'device': 'desktop',
                'browser': 'Chrome'
            }
        )

    def test_audit_log_creation(self):
        """Test audit log entry creation"""
        self.assertEqual(self.audit_log.user, self.user)
        self.assertEqual(self.audit_log.action, 'create')
        self.assertEqual(self.audit_log.resource_type, 'TikTokAccount')
        self.assertIsNotNone(self.audit_log.resource_id)
        self.assertEqual(self.audit_log.ip_address, '127.0.0.1')

    def test_action_choices(self):
        """Test valid action choices"""
        valid_actions = [
            'create', 'update', 'delete', 'login',
            'logout', 'publish', 'schedule'
        ]
        for action in valid_actions:
            self.audit_log.action = action
            self.audit_log.save()
            self.assertEqual(self.audit_log.action, action)

    def test_changes_jsonfield(self):
        """Test changes JSONField with complex data"""
        complex_changes = {
            'before': {
                'username': None,
                'email': None
            },
            'after': {
                'username': 'newuser',
                'email': 'new@example.com'
            },
            'nested_data': {
                'roles': ['admin'],
                'permissions': {
                    'read': True,
                    'write': False
                }
            }
        }
        self.audit_log.changes = complex_changes
        self.audit_log.save()

        # Retrieve and verify
        retrieved_log = AuditLog.objects.get(id=self.audit_log.id)
        self.assertEqual(retrieved_log.changes, complex_changes)

    def test_optional_fields(self):
        """Test optional fields"""
        # Create an audit log without a user (anonymous)
        anonymous_log = AuditLog.objects.create(
            action='login',
            resource_type='User',
            resource_id=uuid4(),
            ip_address='192.168.1.1'
        )

        self.assertIsNone(anonymous_log.user)
        self.assertIsNone(anonymous_log.user_agent)

    def test_metadata_jsonfield(self):
        """Test metadata JSONField"""
        detailed_metadata = {
            'session_id': 'abc123',
            'location': {
                'country': 'US',
                'city': 'San Francisco',
                'coordinates': {
                    'lat': 37.7749,
                    'lon': -122.4194
                }
            }
        }
        self.audit_log.metadata = detailed_metadata
        self.audit_log.save()

        # Retrieve and verify
        retrieved_log = AuditLog.objects.get(id=self.audit_log.id)
        self.assertEqual(retrieved_log.metadata, detailed_metadata)

    def test_string_representation(self):
        """Test string representation of the model"""
        # With a known user
        expected_str = f"{self.user.email} - create - TikTokAccount"
        self.assertEqual(str(self.audit_log), expected_str)

        # With an anonymous user
        anonymous_log = AuditLog.objects.create(
            action='login',
            resource_type='User',
            resource_id=uuid4(),
            ip_address='192.168.1.1'
        )
        expected_anon_str = "Anonymous - login - User"
        self.assertEqual(str(anonymous_log), expected_anon_str)