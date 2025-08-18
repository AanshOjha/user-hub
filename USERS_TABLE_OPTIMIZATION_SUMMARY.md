# Users Table Optimization for SAML and Normal Users

## Overview
The users table has been optimized to efficiently support both SAML-authenticated users and traditional password-based users, following the SAML claims structure provided.

## Key Changes Made

### Database Schema Changes

#### Fields Retained/Added:
- `id` - Primary key (unchanged)
- `email` - Primary human-readable identifier (unchanged) 
- `full_name` - For personalizing the user interface (unchanged)
- `is_active` - Control access within the app; IdP login sets this to True
- `created_at` - Audit timestamp (unchanged)
- `hashed_password` - Only for password-based users (nullable)
- `is_saml_user` - Flag to distinguish authentication method (boolean)
- `saml_subject_id` - Critical permanent unique ID from objectidentifier claim (unique constraint)
- `azure_role` - Store raw Azure role from role/rbac claim
- `role_id` - Internal role mapping (foreign key)

#### Fields Removed:
- `updated_at` - Unnecessary overhead for this use case
- `saml_session_index` - Session data not needed for permanent user records

### SAML Claims Mapping

| SAML Claim | Example Value | Database Column | Purpose |
|------------|---------------|-----------------|---------|
| `.../claims/objectidentifier` | `727bde2a-...` | `saml_subject_id` | Critical permanent unique ID for user lookup |
| `.../claims/emailaddress` | `1aanshojha@...` | `email` | Primary human-readable ID and communication |
| `.../claims/displayname` | `Puyi` | `full_name` | User interface personalization |
| `.../claims/role` or `rbac` | `itfc-business-admin` | `azure_role` & `role_id` | Raw Azure role storage and internal role mapping |
| N/A (System field) | `True` | `is_saml_user` | Authentication method flag |
| N/A (System field) | `True` | `is_active` | Access control within the app |

## User Types Supported

### SAML Users
- **Authentication**: Via Azure AD/SAML IdP
- **Identification**: Uses `saml_subject_id` as permanent unique identifier
- **Role Assignment**: Automatic mapping from Azure AD roles to internal roles
- **Password**: No password stored (`hashed_password` is NULL)
- **Status**: `is_saml_user = True`, `is_active = True` (set by IdP login)

### Normal Users
- **Authentication**: Username/password
- **Identification**: Uses `email` as primary identifier
- **Role Assignment**: Manual assignment through admin interface
- **Password**: Stored as `hashed_password`
- **Status**: `is_saml_user = False`, `is_active` managed manually

## Updated API Schemas

### New Schemas Added:
- `UserCreateSAML` - For creating SAML users with required SAML fields
- Updated `UserInDB` - Includes SAML-specific fields
- Updated `UserCreate` - Password is now optional to support both user types

### CRUD Operations Updated:
- `create_user()` - For password-based users only
- `create_saml_user()` - For SAML users only  
- `get_user_by_saml_subject_id()` - Lookup by permanent SAML identifier
- `create_or_update_saml_user()` - Updated to use `saml_subject_id` as primary lookup

## Azure Role Mapping

The system automatically maps Azure AD roles to internal roles:

```python
role_mapping = {
    'itfc-business-admin': 'Super Admin',
    'hr-manager': 'HR Manager', 
    'hiring-manager': 'Hiring Manager',
    'hr-intern': 'HR Intern',
    'recruiter': 'Recruiter',
    'sourcer': 'Sourcer'
}
```

Default fallback role: `HR Intern`

## Migration Notes

- **Backward Compatibility**: Existing users are preserved
- **Data Cleanup**: Duplicate `saml_subject_id` values are cleared during migration
- **Constraints**: Unique constraint added to `saml_subject_id`
- **Defaults**: Existing users get appropriate `is_saml_user` values based on presence of SAML data

## Security Considerations

1. **Primary Identification**: SAML users are identified by `saml_subject_id` (permanent) rather than email (can change)
2. **No Password Storage**: SAML users have no password stored in the system
3. **Active Directory Integration**: Role assignments automatically sync with Azure AD
4. **Access Control**: `is_active` flag provides application-level access control independent of IdP status

## Benefits

1. **Optimized Storage**: Removed unnecessary fields reduces database overhead
2. **Clear Separation**: Distinct handling for SAML vs password users
3. **Permanent Identity**: `saml_subject_id` provides stable user identification even if email changes
4. **Automatic Role Sync**: Azure AD roles automatically map to internal permissions
5. **Flexible Access Control**: Application can control access independently of authentication method

This optimized structure provides a clean, efficient foundation for supporting both authentication methods while maintaining security and performance.
