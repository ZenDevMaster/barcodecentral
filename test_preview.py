#!/usr/bin/env python3
"""
Test script for preview generation
Tests preview generation from templates and raw ZPL
Usage: python test_preview.py [--template TEMPLATE] [--zpl ZPL] [--size SIZE]
"""
import argparse
import sys
import os
from preview_generator import PreviewGenerator
from template_manager import TemplateManager


def test_preview_from_template(template_name: str, variables: dict = None, label_size: str = '4x6', dpi: int = 203):
    """
    Test preview generation from a template
    
    Args:
        template_name: Template filename
        variables: Variables to render
        label_size: Label size
        dpi: DPI setting
    """
    print(f"\n{'='*60}")
    print(f"Testing Preview from Template: {template_name}")
    print(f"{'='*60}")
    
    try:
        # Initialize managers
        template_manager = TemplateManager()
        preview_generator = PreviewGenerator()
        
        # Get template info
        print(f"\n1. Loading template...")
        template = template_manager.get_template(template_name)
        print(f"   ✓ Template loaded: {template.get('name', template_name)}")
        print(f"   - Description: {template.get('description', 'N/A')}")
        print(f"   - Size: {template.get('size', 'N/A')}")
        print(f"   - Variables: {', '.join(template.get('variables', []))}")
        
        # Use template's label size if not specified
        if not label_size and 'size' in template:
            label_size = template['size']
        
        # Render template
        print(f"\n2. Rendering template...")
        if variables is None:
            # Use sample variables
            variables = {}
            for var in template.get('variables', []):
                variables[var] = f"Sample_{var}"
        
        rendered_zpl = template_manager.render_template(template_name, variables)
        print(f"   ✓ Template rendered ({len(rendered_zpl)} bytes)")
        print(f"   - Variables used: {variables}")
        
        # Generate preview
        print(f"\n3. Generating preview...")
        print(f"   - Label size: {label_size}")
        print(f"   - DPI: {dpi}")
        
        success, filename, error_msg = preview_generator.save_preview(
            rendered_zpl,
            filename=None,
            label_size=label_size,
            dpi=dpi,
            format='png'
        )
        
        if success:
            filepath = preview_generator.get_preview_path(filename)
            file_size = os.path.getsize(filepath)
            print(f"   ✓ Preview generated successfully!")
            print(f"   - Filename: {filename}")
            print(f"   - Path: {filepath}")
            print(f"   - Size: {file_size:,} bytes")
            return True
        else:
            print(f"   ✗ Preview generation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_preview_from_zpl(zpl_content: str, label_size: str = '4x6', dpi: int = 203):
    """
    Test preview generation from raw ZPL
    
    Args:
        zpl_content: Raw ZPL code
        label_size: Label size
        dpi: DPI setting
    """
    print(f"\n{'='*60}")
    print(f"Testing Preview from Raw ZPL")
    print(f"{'='*60}")
    
    try:
        preview_generator = PreviewGenerator()
        
        print(f"\n1. ZPL Content:")
        print(f"   - Length: {len(zpl_content)} bytes")
        print(f"   - Preview: {zpl_content[:100]}...")
        
        print(f"\n2. Generating preview...")
        print(f"   - Label size: {label_size}")
        print(f"   - DPI: {dpi}")
        
        success, filename, error_msg = preview_generator.save_preview(
            zpl_content,
            filename=None,
            label_size=label_size,
            dpi=dpi,
            format='png'
        )
        
        if success:
            filepath = preview_generator.get_preview_path(filename)
            file_size = os.path.getsize(filepath)
            print(f"   ✓ Preview generated successfully!")
            print(f"   - Filename: {filename}")
            print(f"   - Path: {filepath}")
            print(f"   - Size: {file_size:,} bytes")
            return True
        else:
            print(f"   ✗ Preview generation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_pdf_generation(template_name: str = None, zpl_content: str = None, label_size: str = '4x6', dpi: int = 203):
    """
    Test PDF preview generation
    
    Args:
        template_name: Template filename (optional)
        zpl_content: Raw ZPL code (optional)
        label_size: Label size
        dpi: DPI setting
    """
    print(f"\n{'='*60}")
    print(f"Testing PDF Preview Generation")
    print(f"{'='*60}")
    
    try:
        preview_generator = PreviewGenerator()
        
        # Get ZPL content
        if template_name:
            print(f"\n1. Rendering template: {template_name}")
            template_manager = TemplateManager()
            template = template_manager.get_template(template_name)
            
            # Use sample variables
            variables = {}
            for var in template.get('variables', []):
                variables[var] = f"Sample_{var}"
            
            zpl_content = template_manager.render_template(template_name, variables)
            print(f"   ✓ Template rendered")
        else:
            print(f"\n1. Using provided ZPL content")
        
        print(f"\n2. Generating PDF preview...")
        print(f"   - Label size: {label_size}")
        print(f"   - DPI: {dpi}")
        
        success, filename, error_msg = preview_generator.save_preview(
            zpl_content,
            filename=None,
            label_size=label_size,
            dpi=dpi,
            format='pdf'
        )
        
        if success:
            filepath = preview_generator.get_preview_path(filename)
            file_size = os.path.getsize(filepath)
            print(f"   ✓ PDF preview generated successfully!")
            print(f"   - Filename: {filename}")
            print(f"   - Path: {filepath}")
            print(f"   - Size: {file_size:,} bytes")
            return True
        else:
            print(f"   ✗ PDF generation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_different_sizes():
    """Test preview generation with different label sizes"""
    print(f"\n{'='*60}")
    print(f"Testing Different Label Sizes")
    print(f"{'='*60}")
    
    # Simple test ZPL
    test_zpl = "^XA^FO50,50^A0N,50,50^FDTest Label^FS^XZ"
    
    sizes = ['4x6', '4x2', '4x3', '2x1']
    preview_generator = PreviewGenerator()
    
    results = []
    for size in sizes:
        print(f"\n  Testing size: {size}")
        success, filename, error_msg = preview_generator.save_preview(
            test_zpl,
            filename=None,
            label_size=size,
            dpi=203,
            format='png'
        )
        
        if success:
            filepath = preview_generator.get_preview_path(filename)
            file_size = os.path.getsize(filepath)
            print(f"    ✓ Generated: {filename} ({file_size:,} bytes)")
            results.append(True)
        else:
            print(f"    ✗ Failed: {error_msg}")
            results.append(False)
    
    success_count = sum(results)
    print(f"\n  Results: {success_count}/{len(sizes)} successful")
    return all(results)


def test_cleanup():
    """Test preview cleanup functionality"""
    print(f"\n{'='*60}")
    print(f"Testing Preview Cleanup")
    print(f"{'='*60}")
    
    try:
        preview_generator = PreviewGenerator()
        
        print(f"\n1. Checking preview directory...")
        previews_dir = preview_generator.previews_dir
        
        if os.path.exists(previews_dir):
            file_count = len([f for f in os.listdir(previews_dir) if os.path.isfile(os.path.join(previews_dir, f))])
            print(f"   - Directory: {previews_dir}")
            print(f"   - Files: {file_count}")
        else:
            print(f"   - Directory does not exist yet")
            return True
        
        print(f"\n2. Running cleanup (7 days)...")
        files_deleted, errors = preview_generator.cleanup_old_previews(days=7)
        
        print(f"   ✓ Cleanup completed")
        print(f"   - Files deleted: {files_deleted}")
        print(f"   - Errors: {errors}")
        
        return errors == 0
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("PREVIEW GENERATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Preview from template
    try:
        result = test_preview_from_template('example.zpl.j2')
        results.append(('Template Preview', result))
    except Exception as e:
        print(f"Test failed: {e}")
        results.append(('Template Preview', False))
    
    # Test 2: Preview from raw ZPL
    test_zpl = "^XA^FO50,50^A0N,50,50^FDTest Label^FS^FO50,120^A0N,30,30^FDRaw ZPL Test^FS^XZ"
    try:
        result = test_preview_from_zpl(test_zpl)
        results.append(('Raw ZPL Preview', result))
    except Exception as e:
        print(f"Test failed: {e}")
        results.append(('Raw ZPL Preview', False))
    
    # Test 3: PDF generation
    try:
        result = test_pdf_generation(zpl_content=test_zpl)
        results.append(('PDF Generation', result))
    except Exception as e:
        print(f"Test failed: {e}")
        results.append(('PDF Generation', False))
    
    # Test 4: Different sizes
    try:
        result = test_different_sizes()
        results.append(('Different Sizes', result))
    except Exception as e:
        print(f"Test failed: {e}")
        results.append(('Different Sizes', False))
    
    # Test 5: Cleanup
    try:
        result = test_cleanup()
        results.append(('Cleanup', result))
    except Exception as e:
        print(f"Test failed: {e}")
        results.append(('Cleanup', False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n  Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return passed == total


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test preview generation')
    parser.add_argument('--template', help='Template filename to test')
    parser.add_argument('--zpl', help='Raw ZPL content to test')
    parser.add_argument('--size', default='4x6', help='Label size (default: 4x6)')
    parser.add_argument('--dpi', type=int, default=203, help='DPI setting (default: 203)')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF instead of PNG')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Run all tests if --all flag is set
    if args.all:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    
    # Run specific test based on arguments
    if args.template:
        if args.pdf:
            success = test_pdf_generation(template_name=args.template, label_size=args.size, dpi=args.dpi)
        else:
            success = test_preview_from_template(args.template, label_size=args.size, dpi=args.dpi)
    elif args.zpl:
        if args.pdf:
            success = test_pdf_generation(zpl_content=args.zpl, label_size=args.size, dpi=args.dpi)
        else:
            success = test_preview_from_zpl(args.zpl, label_size=args.size, dpi=args.dpi)
    else:
        # No arguments, run all tests
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()