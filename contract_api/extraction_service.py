import re
import json
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from django.conf import settings
from .models import Document, DocumentPage


class ContractExtractionService:
    """
    Pure LLM-based contract field extraction service using Gemini Flash
    """
    
    def __init__(self):
        # Initialize Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.llm_available = True
        else:
            self.llm_available = False
            print("Warning: GEMINI_API_KEY not set. LLM extraction disabled.")
    
    def extract_fields(self, document_id: str) -> Dict[str, Any]:
        """
        Extract contract fields using pure LLM approach
        """
        try:
            document = Document.objects.get(id=document_id)
            
            # Get all text from document pages
            full_text = self._get_document_text(document)
            
            if not self.llm_available:
                return {
                    'success': False,
                    'error': 'LLM extraction not available. Please set GEMINI_API_KEY.'
                }
            
            # Extract all fields using LLM
            extracted_fields = self._llm_extraction(full_text)
            
            return {
                'success': True,
                'document_id': str(document_id),
                'extracted_fields': extracted_fields,
                'extraction_method': 'pure_llm_gemini_flash'
            }
            
        except Document.DoesNotExist:
            return {'success': False, 'error': 'Document not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_document_text(self, document: Document) -> str:
        """Get full text from all document pages"""
        pages = document.pages.all().order_by('page_number')
        return '\n\n'.join([page.text for page in pages])
    
    def _llm_extraction(self, text: str) -> Dict[str, Any]:
        """Extract all contract fields using Gemini Flash LLM"""
        try:
            # Create comprehensive extraction prompt
            prompt = self._create_extraction_prompt(text)
            
            # Get LLM response
            response = self.model.generate_content(prompt)
            
            # Parse LLM response
            if response.text:
                extracted_fields = self._parse_llm_response(response.text)
                return self._validate_and_clean_fields(extracted_fields)
            else:
                return self._get_empty_fields()
                
        except Exception as e:
            print(f"LLM extraction failed: {str(e)}")
            return self._get_empty_fields()
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create comprehensive prompt for LLM extraction"""
        return f"""
        You are a contract analysis expert. Analyze the following contract text and extract ALL specified fields in JSON format.

        Contract Text:
        {text[:6000]}  # Increased limit for better context

        Please extract the following fields from the contract. If a field cannot be found or is not applicable, use null.

        REQUIRED FIELDS TO EXTRACT:
        1. parties: Array of company/organization names that are parties to the contract
        2. effective_date: The effective/start date of the contract (YYYY-MM-DD format)
        3. term: The duration/term of the contract (e.g., "2 years", "6 months")
        4. governing_law: The governing law or jurisdiction
        5. payment_terms: Payment terms and conditions
        6. termination: Termination date or conditions (YYYY-MM-DD if date, or text description)
        7. auto_renewal: Boolean indicating if contract has auto-renewal (true/false/null)
        8. confidentiality: Confidentiality clauses and obligations
        9. indemnity: Indemnification clauses and scope
        10. liability_cap: Liability cap amount (numeric value)
        11. liability_cap_currency: Currency of liability cap (3-letter code like USD, EUR)
        12. signatories: Array of signatories with name, title, and date
        13. contract_type: Type of contract (NDA, Service Agreement, Employment, etc.)
        14. total_value: Total contract value (numeric value)
        15. value_currency: Currency of contract value (3-letter code)

        IMPORTANT INSTRUCTIONS:
        - Return ONLY valid JSON
        - Use proper data types (strings, numbers, booleans, arrays)
        - For dates, use YYYY-MM-DD format when possible
        - For amounts, extract numeric values only
        - For currencies, use 3-letter codes (USD, EUR, GBP, etc.)
        - For signatories, include name, title, and date if available
        - If a field is not found, use null
        - Be thorough and extract as much information as possible

        Example response format:
        {{
            "parties": ["Company A Inc.", "Company B LLC"],
            "effective_date": "2024-01-01",
            "term": "2 years",
            "governing_law": "California",
            "payment_terms": "Net 30 days",
            "termination": "2026-01-01",
            "auto_renewal": true,
            "confidentiality": "Both parties agree to maintain confidentiality...",
            "indemnity": "Company A shall indemnify Company B against...",
            "liability_cap": 100000,
            "liability_cap_currency": "USD",
            "signatories": [
                {{"name": "John Doe", "title": "CEO", "date": "2024-01-01"}},
                {{"name": "Jane Smith", "title": "General Counsel", "date": "2024-01-01"}}
            ],
            "contract_type": "Service Agreement",
            "total_value": 50000,
            "value_currency": "USD"
        }}

        Now extract the fields from the contract text above:
        """
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON fields"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse LLM response: {str(e)}")
            print(f"Raw response: {response_text[:500]}...")
        
        return {}
    
    def _validate_and_clean_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted fields"""
        # Ensure all required fields exist
        required_fields = [
            'parties', 'effective_date', 'term', 'governing_law', 'payment_terms',
            'termination', 'auto_renewal', 'confidentiality', 'indemnity',
            'liability_cap', 'liability_cap_currency', 'signatories', 'contract_type',
            'total_value', 'value_currency'
        ]
        
        cleaned_fields = {}
        
        for field in required_fields:
            if field in fields and fields[field] is not None:
                cleaned_fields[field] = fields[field]
            else:
                cleaned_fields[field] = None
        
        # Special handling for specific fields
        if cleaned_fields.get('parties') and not isinstance(cleaned_fields['parties'], list):
            cleaned_fields['parties'] = [cleaned_fields['parties']]
        
        if cleaned_fields.get('signatories') and not isinstance(cleaned_fields['signatories'], list):
            cleaned_fields['signatories'] = [cleaned_fields['signatories']]
        
        # Ensure auto_renewal is boolean
        if cleaned_fields.get('auto_renewal') is not None:
            if isinstance(cleaned_fields['auto_renewal'], str):
                cleaned_fields['auto_renewal'] = cleaned_fields['auto_renewal'].lower() in ['true', 'yes', '1']
        
        # Ensure numeric fields are numbers
        for field in ['liability_cap', 'total_value']:
            if cleaned_fields.get(field) is not None:
                try:
                    cleaned_fields[field] = float(cleaned_fields[field])
                except (ValueError, TypeError):
                    cleaned_fields[field] = None
        
        return cleaned_fields
    
    def _get_empty_fields(self) -> Dict[str, Any]:
        """Return empty field structure when extraction fails"""
        return {
            'parties': None,
            'effective_date': None,
            'term': None,
            'governing_law': None,
            'payment_terms': None,
            'termination': None,
            'auto_renewal': None,
            'confidentiality': None,
            'indemnity': None,
            'liability_cap': None,
            'liability_cap_currency': None,
            'signatories': None,
            'contract_type': None,
            'total_value': None,
            'value_currency': None
        }
