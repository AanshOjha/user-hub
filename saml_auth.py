from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from fastapi import Request, HTTPException
from typing import Dict, Any, Optional
from config import settings

class SAMLConfig:
    """SAML Configuration class"""
    
    @staticmethod
    def get_saml_settings() -> Dict[str, Any]:
        """Get SAML settings configuration"""
        return {
            "strict": True,
            "debug": settings.debug,
            "sp": {
                "entityId": f"{settings.base_url}/auth/saml/metadata",
                "assertionConsumerService": {
                    "url": f"{settings.base_url}/acs",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "singleLogoutService": {
                    "url": f"{settings.base_url}/sls",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "x509cert": "",
                "privateKey": ""
            },
            "idp": {
                "entityId": f"https://sts.windows.net/{settings.azure_tenant_id}/",
                "singleSignOnService": {
                    "url": f"https://login.microsoftonline.com/{settings.azure_tenant_id}/saml2",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "singleLogoutService": {
                    "url": f"https://login.microsoftonline.com/{settings.azure_tenant_id}/saml2",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": settings.azure_saml_certificate
            }
        }

class SAMLAuth:
    """SAML Authentication handler"""
    
    def __init__(self):
        self.settings = SAMLConfig.get_saml_settings()
    
    def prepare_fastapi_request(self, request: Request) -> Dict[str, Any]:
        """Prepare FastAPI request for SAML processing"""
        form_data = {}
        query_data = {}
        
        # Handle form data if present
        if hasattr(request, '_form') and request._form:
            form_data = dict(request._form)
        
        # Handle query parameters
        if request.query_params:
            query_data = dict(request.query_params)
        
        # Get port from URL or use default
        port = str(request.url.port) if request.url.port else ('443' if request.url.scheme == 'https' else '80')
        
        return {
            'https': 'on' if request.url.scheme == 'https' else 'off',
            'http_host': request.url.hostname or 'localhost',
            'server_port': port,
            'script_name': request.url.path,
            'get_data': query_data,
            'post_data': form_data
        }
    
    def get_auth_object(self, request: Request) -> OneLogin_Saml2_Auth:
        """Create SAML Auth object from FastAPI request"""
        req = self.prepare_fastapi_request(request)
        return OneLogin_Saml2_Auth(req, self.settings)
    
    def initiate_login(self, request: Request) -> str:
        """Initiate SAML SSO login"""
        auth = self.get_auth_object(request)
        return auth.login()
    
    def process_response(self, request: Request) -> Dict[str, Any]:
        """Process SAML response and extract user data"""
        auth = self.get_auth_object(request)
        auth.process_response()
        
        errors = auth.get_errors()
        if errors:
            raise HTTPException(status_code=400, detail=f"SAML errors: {', '.join(errors)}")
        
        if not auth.is_authenticated():
            raise HTTPException(status_code=401, detail="SAML authentication failed")
        
        attributes = auth.get_attributes()
        
        # Extract user information from SAML attributes
        # Try multiple possible claim names for object identifier
        objectidentifier = (
            self._get_attribute_value(attributes, 'http://schemas.microsoft.com/identity/claims/objectidentifier') or
            self._get_attribute_value(attributes, 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier') or
            self._get_attribute_value(attributes, 'objectidentifier') or
            self._get_attribute_value(attributes, 'oid') or
            self._get_attribute_value(attributes, 'http://schemas.microsoft.com/identity/claims/tenantid')
        )
        
        user_data = {
            'email': self._get_attribute_value(attributes, 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name'),
            'name': self._get_attribute_value(attributes, 'http://schemas.microsoft.com/identity/claims/displayname'),
            'first_name': self._get_attribute_value(attributes, 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'),
            'last_name': self._get_attribute_value(attributes, 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'),
            'role': self._get_attribute_value(attributes, 'http://schemas.microsoft.com/ws/2008/06/identity/claims/role'),
            'groups': attributes.get('http://schemas.microsoft.com/ws/2008/06/identity/claims/groups', []),
            'upn': self._get_attribute_value(attributes, 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn'),
            'objectidentifier': objectidentifier,
            'nameid': auth.get_nameid(),
            'session_index': auth.get_session_index(),
            'all_attributes': attributes
        }
        
        return user_data
    
    def initiate_logout(self, request: Request, name_id: Optional[str] = None, 
                       session_index: Optional[str] = None) -> str:
        """Initiate SAML SLO (Single Logout)"""
        auth = self.get_auth_object(request)
        return auth.logout(name_id=name_id, session_index=session_index)
    
    def process_logout_response(self, request: Request) -> bool:
        """Process SAML logout response"""
        auth = self.get_auth_object(request)
        url = auth.process_slo(delete_session_cb=lambda: None)
        errors = auth.get_errors()
        
        if errors:
            raise HTTPException(status_code=400, detail=f"SAML logout errors: {', '.join(errors)}")
        
        return True
    
    def get_metadata(self, request: Request) -> str:
        """Generate SAML metadata"""
        saml_settings = OneLogin_Saml2_Settings(self.settings)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        
        if errors:
            raise HTTPException(status_code=500, detail=f"Metadata validation errors: {', '.join(errors)}")
        
        return metadata
    
    def _get_attribute_value(self, attributes: Dict[str, list], attribute_name: str) -> Optional[str]:
        """Get first value from SAML attribute list"""
        values = attributes.get(attribute_name, [])
        return values[0] if values else None

# Global SAML auth instance
saml_auth = SAMLAuth()
