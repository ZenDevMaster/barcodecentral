"""
Test type conversion for Jinja2 template variables
"""
import pytest
from utils.type_converter import convert_variable_types, _convert_string_value


def test_convert_numeric_strings():
    """Test conversion of numeric strings to int/float"""
    variables = {
        'quantity': '123',
        'price': '45.67',
        'count': '0',
        'negative': '-10'
    }
    
    result = convert_variable_types(variables)
    
    assert result['quantity'] == 123
    assert isinstance(result['quantity'], int)
    
    assert result['price'] == 45.67
    assert isinstance(result['price'], float)
    
    assert result['count'] == 0
    assert isinstance(result['count'], int)
    
    assert result['negative'] == -10
    assert isinstance(result['negative'], int)


def test_convert_boolean_strings():
    """Test conversion of boolean-like strings to bool"""
    variables = {
        'is_fragile': '1',
        'requires_signature': '1',
        'is_active': 'true',
        'is_disabled': 'false',
        'enabled': 'yes',
        'disabled': 'no',
        'flag_on': 'on',
        'flag_off': 'off',
        'zero': '0'
    }
    
    result = convert_variable_types(variables)
    
    assert result['is_fragile'] is True
    assert result['requires_signature'] is True
    assert result['is_active'] is True
    assert result['is_disabled'] is False
    assert result['enabled'] is True
    assert result['disabled'] is False
    assert result['flag_on'] is True
    assert result['flag_off'] is False
    assert result['zero'] is False


def test_keep_strings():
    """Test that regular strings remain as strings"""
    variables = {
        'name': 'John Doe',
        'address': '123 Main St',
        'sku': 'ABC-123',
        'empty': ''
    }
    
    result = convert_variable_types(variables)
    
    assert result['name'] == 'John Doe'
    assert isinstance(result['name'], str)
    
    assert result['address'] == '123 Main St'
    assert isinstance(result['address'], str)
    
    assert result['sku'] == 'ABC-123'
    assert isinstance(result['sku'], str)
    
    assert result['empty'] == ''
    assert isinstance(result['empty'], str)


def test_mixed_types():
    """Test conversion with mixed input types"""
    variables = {
        'quantity': '123',  # string -> int
        'price': 45.67,     # already float
        'is_active': True,  # already bool
        'name': 'Product',  # string stays string
        'flag': '1'         # string -> bool
    }
    
    result = convert_variable_types(variables)
    
    assert result['quantity'] == 123
    assert isinstance(result['quantity'], int)
    
    assert result['price'] == 45.67
    assert isinstance(result['price'], float)
    
    assert result['is_active'] is True
    assert isinstance(result['is_active'], bool)
    
    assert result['name'] == 'Product'
    assert isinstance(result['name'], str)
    
    assert result['flag'] is True
    assert isinstance(result['flag'], bool)


def test_template_scenario():
    """Test the exact scenario from the bug report"""
    variables = {
        'address2': '123123123',
        'is_fragile': '1',
        'quantity': '123',
        'requires_signature': '1'
    }
    
    result = convert_variable_types(variables)
    
    # These should now work in Jinja2 templates
    assert result['quantity'] >= 100  # Numeric comparison
    assert result['is_fragile'] and result['requires_signature']  # Boolean logic
    assert result['address2'] == '123123123'  # String remains string


if __name__ == '__main__':
    pytest.main([__file__, '-v'])