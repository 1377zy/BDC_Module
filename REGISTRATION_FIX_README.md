# User Registration Fix

This patch fixes the "Forbidden" error encountered during user registration by making the following changes:

1. **Removed login requirement for registration**:
   - Removed the `@admin_required` decorator from the `/register` route in `auth/routes.py`
   - This allows any user to access the registration page

2. **Fixed circular imports**:
   - Modified `app/models/__init__.py` to prevent circular imports
   - Created `app/models_main.py` with the User model and related models

## How to Apply the Fix

Apply the patch file using:

```
git apply registration_fix.patch
```

Or manually make the changes shown in the patch file.

## Testing

After applying the patch, the registration page should be accessible to all users without requiring login or admin privileges.
