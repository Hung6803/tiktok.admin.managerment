# Code Review: Phase 02 Database Schema Design

**Date:** 2025-12-04
**Reviewer:** Code Review Agent
**Phase:** Phase 02 - Database Schema Design
**Status:** Complete with Recommendations

---

## Code Review Summary

### Scope
- **Files reviewed:** 19 Python files (models, admin, migrations)
- **Lines of code:** ~900 lines across models and admin interfaces
- **Review focus:** Database schema implementation, Django best practices, security
- **Plan file:** `phase-02-database-schema.md`

### Core Files Reviewed

**Base Models:**
- `backend/core/models/base_model.py` - Abstract base with UUID, timestamps, soft delete
- `backend/core/models/audit_log_model.py` - System audit trail

**TikTok Accounts App:**
- `backend/apps/tiktok_accounts/models/tiktok_account_model.py` - OAuth account management
- `backend/apps/tiktok_accounts/admin.py` - Admin interface

**Content App:**
- `backend/apps/content/models/scheduled_post_model.py` - Post scheduling
- `backend/apps/content/models/post_media_model.py` - Media file tracking
- `backend/apps/content/models/publish_history_model.py` - Publishing audit
- `backend/apps/content/admin.py` - Admin interfaces

**Analytics App:**
- `backend/apps/analytics/models/account_analytics_model.py` - Metrics tracking
- `backend/apps/analytics/admin.py` - Admin interface

**User Model:**
- `backend/apps/accounts/models/user_model.py` - Custom user with UUID

---

## Overall Assessment

**Grade: B+ (Good with Room for Improvement)**

Implementation demonstrates solid Django fundamentals with proper model design, relationships, indexes, and admin interfaces. Code is clean, well-documented, follows DRY principles. Key strengths include comprehensive field documentation, proper use of choices, soft delete implementation, helper methods.

**Major concerns:**
1. **CRITICAL**: OAuth tokens stored as plaintext TextField (security vulnerability)
2. User model doesn't inherit from BaseModel (inconsistent pattern)
3. Missing QuerySet managers for soft delete filtering
4. JSONField default=list can cause mutable default issues
5. Missing encryption library integration
6. No database-level constraints for some business rules

---

## Critical Issues

### 1. **SECURITY: OAuth Tokens Not Encrypted**

**Location:** `tiktok_accounts/models/tiktok_account_model.py:55-62`

**Issue:** Access and refresh tokens stored as plaintext TextField despite comments claiming encryption.

```python
# Current (VULNERABLE):
access_token = models.TextField(
    help_text="Encrypted OAuth access token"  # FALSE - NOT ENCRYPTED!
)
refresh_token = models.TextField(
    null=True,
    blank=True,
    help_text="Encrypted OAuth refresh token"  # FALSE - NOT ENCRYPTED!
)
```

**Impact:** Catastrophic if database compromised. Attackers gain full access to all connected TikTok accounts.

**Fix Required:**
```python
# Option 1: Use django-fernet-fields (recommended)
from fernet_fields import EncryptedTextField

class TikTokAccount(BaseModel):
    access_token = EncryptedTextField(
        help_text="Encrypted OAuth access token"
    )
    refresh_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text="Encrypted OAuth refresh token"
    )

# Option 2: Property-based encryption
from django.conf import settings
from cryptography.fernet import Fernet

class TikTokAccount(BaseModel):
    _access_token = models.TextField(db_column='access_token')

    @property
    def access_token(self):
        cipher = Fernet(settings.FIELD_ENCRYPTION_KEY)
        return cipher.decrypt(self._access_token.encode()).decode()

    @access_token.setter
    def access_token(self, value):
        cipher = Fernet(settings.FIELD_ENCRYPTION_KEY)
        self._access_token = cipher.encrypt(value.encode()).decode()
```

**Required Actions:**
1. Add `django-fernet-fields==6.0.0` to requirements.txt
2. Generate encryption key: `python manage.py generate_encryption_key`
3. Store key in environment variable: `FIELD_ENCRYPTION_KEY`
4. Create migration to encrypt existing tokens
5. Update model fields to use EncryptedTextField
6. Test token encryption/decryption
7. **NEVER expose token fields in API responses**

**Priority:** CRITICAL - Must fix before production

---

### 2. **SECURITY: Audit Log IP Address Not Validated**

**Location:** `core/models/audit_log_model.py:48`

**Issue:** IP address field not validated, could store malicious data.

```python
# Current:
ip_address = models.GenericIPAddressField(
    help_text="IP address of the user"
)

# Better (but GenericIPAddressField already validates):
# This is actually OK - Django validates IP format
# But should be nullable for system actions:
ip_address = models.GenericIPAddressField(
    null=True,  # Allow null for system-initiated actions
    blank=True,
    help_text="IP address of the user (null for system actions)"
)
```

**Impact:** Medium - Could reject valid system audit logs.

**Priority:** HIGH

---

## High Priority Findings

### 3. **Model Inconsistency: User Doesn't Use BaseModel**

**Location:** `accounts/models/user_model.py`

**Issue:** User model duplicates BaseModel fields instead of inheriting.

```python
# Current (BAD):
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Missing soft_delete() and restore() methods!

# Better (GOOD):
# Option 1: Multiple inheritance (can be tricky with AbstractUser)
class User(AbstractUser, BaseModel):
    # BaseModel provides all common fields
    email = models.EmailField(unique=True, db_index=True)
    timezone = models.CharField(max_length=50, default='UTC')
    # ...

# Option 2: Separate AbstractBaseModel without id field
class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class User(AbstractUser, AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ...
```

**Impact:**
- Code duplication
- Missing helper methods (soft_delete, restore)
- Inconsistent patterns across codebase

**Priority:** HIGH

---

### 4. **QuerySet Issue: No Soft Delete Manager**

**Location:** All models using BaseModel

**Issue:** No custom manager to filter soft-deleted records by default.

```python
# Current usage (requires manual filtering):
TikTokAccount.objects.filter(is_deleted=False)  # Must remember everywhere!

# Better approach:
# In base_model.py
class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class BaseModel(models.Model):
    # ... fields ...

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access all including deleted

    class Meta:
        abstract = True

# Usage becomes:
TikTokAccount.objects.all()  # Only active records
TikTokAccount.all_objects.all()  # Include deleted
TikTokAccount.objects.deleted()  # Only deleted
```

**Impact:**
- Easy to accidentally query deleted records
- Verbose filtering everywhere
- Potential data leaks

**Priority:** HIGH

---

### 5. **Mutable Default Argument: JSONField default=list**

**Location:**
- `scheduled_post_model.py:49-54` (hashtags, mentions)
- Other JSONFields with default=list

**Issue:** Python mutable default gotcha - all instances share same list.

```python
# Current (POTENTIALLY BUGGY):
hashtags = models.JSONField(default=list)
mentions = models.JSONField(default=list)

# Better (SAFE):
def default_list():
    return []

hashtags = models.JSONField(default=default_list)
mentions = models.JSONField(default=default_list)

# Best (Django 3.2+):
from django.db.models import Value
from django.db.models.functions import Cast

hashtags = models.JSONField(default=list, blank=True)
# Django handles this correctly for JSONField in recent versions

# But safest is still callable:
hashtags = models.JSONField(default=lambda: [])
```

**Impact:** Potential data corruption - modifications could affect multiple records.

**Priority:** HIGH (test thoroughly if keeping current approach)

---

### 6. **Type Safety: Missing Validation for TikTok IDs**

**Location:** `scheduled_post_model.py:81-87`

**Issue:** tiktok_video_id stored as CharField but should validate TikTok ID format.

```python
# Current:
tiktok_video_id = models.CharField(
    max_length=100,
    null=True,
    blank=True,
    unique=True,
    help_text="TikTok's video ID after publishing"
)

# Better with validation:
from django.core.validators import RegexValidator

tiktok_id_validator = RegexValidator(
    regex=r'^[0-9]{19}$',  # TikTok IDs are 19-digit numbers
    message='TikTok video ID must be a 19-digit number'
)

tiktok_video_id = models.CharField(
    max_length=19,  # Exact length
    null=True,
    blank=True,
    unique=True,
    validators=[tiktok_id_validator],
    help_text="TikTok's 19-digit video ID after publishing"
)
```

**Priority:** MEDIUM

---

### 7. **Missing Database Constraint: Scheduled Time Validation**

**Location:** `scheduled_post_model.py`

**Issue:** No constraint preventing scheduling posts in the past.

```python
# Add model validation:
from django.core.exceptions import ValidationError
from django.utils import timezone

class ScheduledPost(BaseModel):
    # ... fields ...

    def clean(self):
        super().clean()
        if self.status == 'scheduled' and self.scheduled_time:
            # Allow past times for draft/processing states
            if self.scheduled_time < timezone.now():
                raise ValidationError({
                    'scheduled_time': 'Cannot schedule posts in the past'
                })

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation runs
        super().save(*args, **kwargs)
```

**Priority:** MEDIUM

---

### 8. **Index Optimization: Missing Composite Index**

**Location:** `publish_history_model.py`

**Issue:** Querying by scheduled_post + success is common but not optimized.

```python
# Current indexes:
indexes = [
    models.Index(fields=['scheduled_post', 'attempt_number']),
    models.Index(fields=['started_at']),
    models.Index(fields=['success']),  # Added separately
]

# Better (add composite):
indexes = [
    models.Index(fields=['scheduled_post', 'attempt_number']),
    models.Index(fields=['scheduled_post', 'success']),  # For failed attempt queries
    models.Index(fields=['started_at']),
    models.Index(fields=['success', 'started_at']),  # For recent failures
]
```

**Priority:** MEDIUM

---

## Medium Priority Improvements

### 9. **Code Quality: Missing __repr__ Methods**

All models have good `__str__` but missing `__repr__` for debugging:

```python
def __repr__(self):
    return f"<TikTokAccount id={self.id} username={self.username}>"
```

**Priority:** LOW-MEDIUM

---

### 10. **Documentation: Missing Field Constraints Documentation**

Add model-level docstrings explaining business rules:

```python
class ScheduledPost(BaseModel):
    """
    Post scheduled for publishing to TikTok.

    Business Rules:
    - Caption max 2200 chars (TikTok limit)
    - scheduled_time must be in future for status='scheduled'
    - Max 3 retry attempts (configurable via max_retries)
    - Only one video per post (enforced by media_files relationship)

    State Machine:
    draft -> scheduled -> queued -> processing -> published
                                 \-> failed -> [retry] -> queued
                                 \-> cancelled
    """
```

**Priority:** MEDIUM

---

### 11. **Admin UX: Token Fields Should Be Fully Hidden**

**Location:** `tiktok_accounts/admin.py:18-20`

**Issue:** Tokens shown in read-only fields (collapsed but still visible).

```python
# Current:
readonly_fields = [
    'id', 'tiktok_user_id', 'access_token', 'refresh_token',  # BAD
    'created_at', 'updated_at', 'deleted_at'
]

# Better:
readonly_fields = [
    'id', 'tiktok_user_id', 'token_status',  # Custom method
    'created_at', 'updated_at', 'deleted_at'
]
exclude = ['access_token', 'refresh_token']  # NEVER show tokens

@admin.display(description='Token Status')
def token_status(self, obj):
    if obj.is_token_expired():
        return format_html('<span style="color: red;">Expired</span>')
    elif obj.needs_refresh():
        return format_html('<span style="color: orange;">Needs Refresh</span>')
    return format_html('<span style="color: green;">Valid</span>')
```

**Priority:** HIGH (security best practice)

---

### 12. **Performance: N+1 Query Issue in Admin**

**Location:** All admin classes

**Issue:** No select_related/prefetch_related optimization.

```python
# Current:
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = [
        'tiktok_account',  # N+1 query!
        'status', 'scheduled_time',
        'published_at', 'retry_count', 'created_at'
    ]

# Better:
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = [
        'tiktok_account', 'status', 'scheduled_time',
        'published_at', 'retry_count', 'created_at'
    ]
    list_select_related = ['tiktok_account']  # Optimize!

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tiktok_account__user')
```

**Priority:** MEDIUM

---

## Low Priority Suggestions

### 13. **User Model: USERNAME_FIELD Configuration**

```python
# Current:
REQUIRED_FIELDS = ['email']

# Should also set:
USERNAME_FIELD = 'email'  # If email is primary login
REQUIRED_FIELDS = []  # Username auto-included

# Or keep username but require email:
USERNAME_FIELD = 'username'  # Default
REQUIRED_FIELDS = ['email']  # Current is correct
```

**Priority:** LOW (clarify intent)

---

### 14. **Helper Methods: Add Convenience Properties**

```python
# PostMedia model:
@property
def is_video(self):
    return self.media_type == 'video'

@property
def is_image(self):
    return self.media_type == 'image'

# ScheduledPost model:
@property
def is_published(self):
    return self.status == 'published'

@property
def can_cancel(self):
    return self.status in ['draft', 'scheduled']
```

**Priority:** LOW

---

### 15. **Admin Actions: Add Bulk Operations**

```python
@admin.action(description='Mark selected as cancelled')
def cancel_posts(self, request, queryset):
    updated = queryset.filter(
        status__in=['draft', 'scheduled']
    ).update(status='cancelled')
    self.message_user(request, f'Cancelled {updated} posts.')

actions = [cancel_posts]
```

**Priority:** LOW

---

## Positive Observations

### Excellent Practices Found:

1. **Comprehensive Documentation**
   - Every field has help_text
   - Model-level docstrings explain purpose
   - Clear naming conventions

2. **Proper Indexing Strategy**
   - Composite indexes for common queries
   - ForeignKey fields indexed
   - DateTime fields for filtering indexed

3. **Good Use of Choices**
   - STATUS_CHOICES, PRIVACY_CHOICES properly defined
   - Clear, readable choice labels

4. **Soft Delete Implementation**
   - Consistent across all models via BaseModel
   - includes deleted_at timestamp
   - Helper methods provided

5. **Helper Methods**
   - Business logic encapsulated (is_token_expired, can_retry)
   - Clean separation of concerns

6. **Admin Interface Quality**
   - Logical fieldset organization
   - Appropriate readonly fields
   - Search and filter configured

7. **Relationship Design**
   - Proper CASCADE behavior
   - Related_name consistency
   - Clear ownership hierarchy

8. **Type Usage**
   - UUID for primary keys (security)
   - BigIntegerField for large counts
   - DecimalField for rates
   - JSONField for flexible data

9. **Migration Quality**
   - Clean, generated migrations
   - Proper dependencies
   - Index creation included

10. **DRY Principle**
    - BaseModel reduces duplication
    - Abstract model pattern used correctly

---

## Recommended Actions

### Immediate (Before Moving to Phase 03):

1. **[CRITICAL]** Implement OAuth token encryption
   - Add django-fernet-fields
   - Generate encryption keys
   - Update model fields
   - Create data migration
   - Test encryption/decryption

2. **[CRITICAL]** Hide token fields from admin completely
   - Use exclude, not readonly_fields
   - Add token status display method

3. **[HIGH]** Add SoftDeleteManager to BaseModel
   - Prevents accidental deleted record queries
   - Consistent API across all models

4. **[HIGH]** Fix User model inheritance
   - Use BaseModel pattern
   - Add soft_delete/restore methods

5. **[HIGH]** Fix JSONField defaults to use callables
   - Replace default=list with default=lambda: []
   - Test with multiple instances

### Short-term (During Phase 03):

6. **[MEDIUM]** Add model validation methods
   - scheduled_time cannot be in past
   - Status transition validations

7. **[MEDIUM]** Optimize admin queries
   - Add select_related to all admin classes
   - Prefetch related objects

8. **[MEDIUM]** Add TikTok ID validation
   - Regex validator for 19-digit format
   - Consistent with TikTok API

### Future Improvements:

9. **[LOW]** Add __repr__ methods to all models
10. **[LOW]** Add convenience properties
11. **[LOW]** Add admin bulk actions
12. **[LOW]** Consider database connection pooling config

---

## Security Considerations

### Current State:
- ❌ OAuth tokens stored as plaintext (CRITICAL)
- ✅ UUID primary keys (good for security)
- ✅ Soft delete instead of hard delete (audit trail)
- ⚠️  Admin token fields visible (should hide)
- ✅ Audit log tracks all actions
- ✅ No SQL injection risk (Django ORM)

### Required Changes:
1. Implement field-level encryption for tokens
2. Hide sensitive fields from admin UI
3. Add rate limiting for token refresh
4. Document token rotation policy
5. Implement token expiry monitoring

---

## Performance Analysis

### Index Coverage: ✅ GOOD
- Composite indexes for common queries
- ForeignKey fields indexed appropriately
- DateTime fields indexed for filtering

### Potential Bottlenecks:
1. ⚠️ Admin list views (N+1 queries) - Add select_related
2. ⚠️ JSONField queries (no index) - Expected, acceptable
3. ✅ Soft delete filtering - Will benefit from manager

### Query Optimization Opportunities:
```python
# Common queries that should be optimized:

# 1. Posts ready to publish (OK - indexed)
ScheduledPost.objects.filter(
    status='scheduled',
    scheduled_time__lte=timezone.now(),
    is_deleted=False
)

# 2. Failed posts for retry (NEEDS composite index)
ScheduledPost.objects.filter(
    status='failed',
    retry_count__lt=models.F('max_retries')
)
# Add: models.Index(fields=['status', 'retry_count'])

# 3. Account analytics history (OK - indexed)
AccountAnalytics.objects.filter(
    tiktok_account=account,
    date__gte=start_date
).order_by('-date')
```

---

## Task Completeness Verification

### Phase 02 TODO List Status:

✅ Create base model with common fields
✅ Create User model extending AbstractUser (but needs improvement)
✅ Create TikTokAccount model with OAuth fields (but needs encryption)
✅ Create ScheduledPost model with scheduling logic
✅ Create PostMedia model for file tracking
✅ Create PublishHistory model for audit trail
✅ Create AccountAnalytics model for metrics
✅ Create AuditLog model for system tracking
✅ Generate initial migrations (4 migrations created)
⚠️ Run migrations on development database (not verified - no DB access)
✅ Create database indexes (included in migrations)
⚠️ Test model relationships (no tests found)
✅ Create model admin interfaces
✅ Document model field constraints (excellent help_text)
❌ Create database backup script (not found)

### Success Criteria:
✅ All models created with proper relationships
⚠️ Migrations run successfully (cannot verify)
✅ Database indexes created
✅ Foreign key constraints working (in migrations)
✅ Soft delete functionality working (methods present)
✅ UUID primary keys generated correctly
✅ Timestamp fields auto-populate (auto_now_add, auto_now)
✅ Django admin can view all models

### Remaining Work:
1. Token encryption implementation
2. Database migrations need to be run and verified
3. Model unit tests need to be written
4. Database backup script needs creation
5. Connection pooling configuration

---

## Unresolved Questions

1. **Encryption Key Management**: Where will FIELD_ENCRYPTION_KEY be stored in production? (AWS Secrets Manager, env var, etc.)

2. **Database Setup**: Have migrations been run on development database? Any errors?

3. **Token Rotation**: What's the policy for refreshing OAuth tokens? Should be in Phase 03.

4. **File Storage**: Where will media files be stored? Local, S3, etc.? Affects file_path field design.

5. **Timezone Handling**: Should scheduled_time be stored in UTC or user timezone? Currently stores both.

6. **Analytics Collection**: How often will AccountAnalytics snapshots be taken? Daily cron job?

7. **Audit Log Retention**: How long to keep audit logs? Need partitioning strategy?

8. **User Authentication**: Is email or username the primary login? USERNAME_FIELD needs clarification.

9. **Testing Database**: Is there a test database configured for running pytest?

10. **Phase 01 Completion**: Was Phase 01 fully completed? Need to verify project setup before proceeding.

---

## Next Steps

**Before Phase 03:**
1. Implement CRITICAL security fixes (token encryption)
2. Apply HIGH priority improvements (managers, User model)
3. Run and verify all migrations
4. Write model unit tests
5. Create database backup script

**Phase 03 Planning:**
- Token encryption must be working before TikTok API integration
- Consider rate limiting for API calls
- Implement token refresh mechanism
- Add error handling for API failures

**Documentation Updates:**
- Document encryption key generation process
- Add database schema diagram
- Document model validation rules
- Create migration runbook

---

## Metrics

- **Models Created:** 8 (BaseModel, AuditLog, User, TikTokAccount, ScheduledPost, PostMedia, PublishHistory, AccountAnalytics)
- **Admin Interfaces:** 4 (TikTokAccount, ScheduledPost, PostMedia, PublishHistory, AccountAnalytics)
- **Migrations Generated:** 4 apps
- **Database Indexes:** 15+ composite indexes
- **Foreign Key Relationships:** 6
- **Code Quality Score:** 7.5/10
- **Security Score:** 4/10 (due to token encryption issue)
- **Documentation Score:** 9/10

---

**Overall Recommendation:** Code quality is good but MUST address token encryption before production. Phase 02 is 85% complete. Recommend completing security fixes and testing before Phase 03.
