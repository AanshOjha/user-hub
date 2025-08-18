#!/usr/bin/env python3
"""
Test script to analyze SAML claims and help debug objectidentifier issues.

This script helps you understand what claims are being sent by Azure AD
and helps identify the correct claim name for the object identifier.
"""

def analyze_saml_attributes(attributes_dict):
    """Analyze SAML attributes to find object identifier"""
    print("=== SAML Attributes Analysis ===")
    print(f"Total attributes received: {len(attributes_dict)}")
    print()
    
    # Look for object identifier related claims
    oid_candidates = {}
    
    for claim_name, claim_values in attributes_dict.items():
        print(f"Claim: {claim_name}")
        print(f"  Values: {claim_values}")
        
        # Check if this might be an object identifier
        if any(keyword in claim_name.lower() for keyword in ['object', 'oid', 'identifier', 'guid', 'id']):
            oid_candidates[claim_name] = claim_values
        print()
    
    print("=== Potential Object Identifier Claims ===")
    if oid_candidates:
        for claim_name, claim_values in oid_candidates.items():
            print(f"Candidate: {claim_name} = {claim_values}")
            # Check if value looks like a GUID (727bde... format)
            for value in claim_values:
                if isinstance(value, str) and len(value) >= 6:
                    if value.startswith('727bde') or '-' in value or len(value) == 36:
                        print(f"  *** LIKELY MATCH *** This looks like the object ID you want!")
    else:
        print("No obvious object identifier claims found.")
    
    print()
    print("=== Common Azure AD Object Identifier Claim Names ===")
    common_oid_claims = [
        'http://schemas.microsoft.com/identity/claims/objectidentifier',
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier', 
        'objectidentifier',
        'oid',
        'http://schemas.microsoft.com/identity/claims/tenantid',
        'unique_name',
        'sub'
    ]
    
    for claim_name in common_oid_claims:
        if claim_name in attributes_dict:
            print(f"FOUND: {claim_name} = {attributes_dict[claim_name]}")
        else:
            print(f"NOT FOUND: {claim_name}")

def check_azure_ad_config():
    """Provide guidance on Azure AD configuration"""
    print("\n=== Azure AD Configuration Check ===")
    print("To ensure objectidentifier is included in SAML responses:")
    print()
    print("1. Go to Azure Portal → Azure Active Directory → Enterprise applications")
    print("2. Find your application → Single sign-on → Attributes & Claims")
    print("3. Ensure these claims are configured:")
    print("   - Name: objectidentifier")
    print("   - Namespace: http://schemas.microsoft.com/identity/claims/objectidentifier")
    print("   - Source: user.objectid")
    print()
    print("4. Alternative claim configurations to try:")
    print("   - Name: oid")
    print("   - Source: user.objectid")
    print("   - Namespace: (leave empty)")
    print()
    print("5. Save and test the configuration")

if __name__ == "__main__":
    # Example usage - you can call this from your SAML processing
    print("SAML Claims Analysis Tool")
    print("Call analyze_saml_attributes(attributes) from your SAML processing code")
    print("to debug what claims are being received.")
    
    # Example attributes dict (replace with real data)
    example_attributes = {
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': ['user@domain.com'],
        'http://schemas.microsoft.com/identity/claims/displayname': ['User Name'],
        'http://schemas.microsoft.com/identity/claims/objectidentifier': ['727bde12-3456-7890-abcd-ef1234567890']
    }
    
    print("\nExample analysis:")
    analyze_saml_attributes(example_attributes)
    check_azure_ad_config()
