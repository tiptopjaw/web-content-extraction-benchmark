"""
Validate annotation files against v2 JSON schema
"""
import json
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
SCHEMA_DIR = BASE_DIR / "schemas"
DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"


def load_schema(version: str = "2.0") -> dict:
    """Load JSON schema for specified version"""
    schema_file = SCHEMA_DIR / f"annotation_v{version.replace('.', '')}.json"
    if not schema_file.exists():
        # Try alternative naming
        schema_file = SCHEMA_DIR / f"annotation_v{version.split('.')[0]}.json"

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file) as f:
        return json.load(f)


def detect_schema_version(annotation: dict) -> str:
    """Detect schema version from annotation"""
    if 'schema_version' in annotation:
        return annotation['schema_version']

    # v1 detection: has ground_truth but no images
    if 'ground_truth' in annotation:
        gt = annotation.get('ground_truth', {})
        if 'images' not in gt:
            return '1.0'
        return '2.0'

    return 'unknown'


def validate_annotation(annotation: dict, schema: dict) -> Tuple[bool, List[str]]:
    """
    Validate a single annotation against schema

    Returns: (is_valid, list of error messages)
    """
    errors = []

    try:
        validate(instance=annotation, schema=schema)
    except ValidationError as e:
        errors.append(f"{e.json_path}: {e.message}")
        # Collect all errors, not just the first
        for error in sorted(e.context, key=lambda x: str(x.path)):
            errors.append(f"  - {error.json_path}: {error.message}")

    return len(errors) == 0, errors


def validate_annotation_content(annotation: dict) -> List[str]:
    """
    Additional content validation beyond schema

    Returns: list of warnings (not errors)
    """
    warnings = []
    gt = annotation.get('ground_truth', {})

    # Check main_content length
    main_content = gt.get('main_content', '')
    if len(main_content) < 200:
        warnings.append(f"main_content is short ({len(main_content)} chars)")

    # Check snippets
    with_snippets = gt.get('with', [])
    without_snippets = gt.get('without', [])

    if len(with_snippets) != 5:
        warnings.append(f"Expected 5 'with' snippets, got {len(with_snippets)}")
    if len(without_snippets) != 5:
        warnings.append(f"Expected 5 'without' snippets, got {len(without_snippets)}")

    # Check images
    images = gt.get('images', {})
    if images:
        items = images.get('items', [])
        annotated_count = images.get('annotated_count', 0)

        if len(items) != annotated_count:
            warnings.append(f"Image count mismatch: annotated_count={annotated_count}, actual items={len(items)}")

        # Check for hero image
        has_hero = any(img.get('is_hero', False) for img in items)
        if items and not has_hero:
            warnings.append("No hero image marked in items")

    # Check page_type if present
    internal = annotation.get('_internal', {})
    page_type = internal.get('page_type', {})

    if page_type:
        confidence = page_type.get('confidence', '')
        needs_review = page_type.get('needs_review', False)

        if confidence == 'low' and not needs_review:
            warnings.append("Low confidence but needs_review not set")

    return warnings


def validate_directory(directory: Path, schema_version: str = "2.0") -> Dict[str, Any]:
    """
    Validate all annotations in a directory

    Returns: summary dict
    """
    schema = load_schema(schema_version)

    results = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'warnings': 0,
        'version_mismatch': 0,
        'errors': [],
        'warning_files': []
    }

    json_files = sorted(directory.glob("*.json"))
    results['total'] = len(json_files)

    for json_file in json_files:
        try:
            with open(json_file) as f:
                annotation = json.load(f)
        except json.JSONDecodeError as e:
            results['invalid'] += 1
            results['errors'].append({
                'file': json_file.name,
                'errors': [f"JSON parse error: {e}"]
            })
            continue

        # Check version
        detected_version = detect_schema_version(annotation)
        if detected_version != schema_version:
            results['version_mismatch'] += 1
            if detected_version == '1.0' and schema_version == '2.0':
                results['errors'].append({
                    'file': json_file.name,
                    'errors': [f"Schema version mismatch: expected {schema_version}, detected {detected_version}"]
                })
                results['invalid'] += 1
                continue

        # Validate against schema
        is_valid, errors = validate_annotation(annotation, schema)

        if is_valid:
            results['valid'] += 1

            # Additional content checks
            warnings = validate_annotation_content(annotation)
            if warnings:
                results['warnings'] += 1
                results['warning_files'].append({
                    'file': json_file.name,
                    'warnings': warnings
                })
        else:
            results['invalid'] += 1
            results['errors'].append({
                'file': json_file.name,
                'errors': errors
            })

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate annotation files")
    parser.add_argument('--dir', type=Path, default=GROUND_TRUTH_DIR,
                        help="Directory containing annotation files")
    parser.add_argument('--schema', type=str, default="2.0",
                        help="Schema version to validate against")
    parser.add_argument('--verbose', '-v', action='store_true',
                        help="Show detailed errors and warnings")
    parser.add_argument('--file', type=Path,
                        help="Validate a single file instead of directory")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Annotation Validation")
    print(f"{'='*60}\n")

    if args.file:
        # Single file validation
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        with open(args.file) as f:
            annotation = json.load(f)

        schema = load_schema(args.schema)
        is_valid, errors = validate_annotation(annotation, schema)
        warnings = validate_annotation_content(annotation)

        print(f"File: {args.file.name}")
        print(f"Schema version: {args.schema}")
        print(f"Detected version: {detect_schema_version(annotation)}")
        print(f"Valid: {'Yes' if is_valid else 'No'}")

        if errors:
            print("\nErrors:")
            for e in errors:
                print(f"  - {e}")

        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w}")

        sys.exit(0 if is_valid else 1)

    # Directory validation
    if not args.dir.exists():
        print(f"Error: Directory not found: {args.dir}")
        sys.exit(1)

    print(f"Directory: {args.dir}")
    print(f"Schema version: {args.schema}")
    print()

    results = validate_directory(args.dir, args.schema)

    print(f"Total files: {results['total']}")
    print(f"Valid: {results['valid']}")
    print(f"Invalid: {results['invalid']}")
    print(f"With warnings: {results['warnings']}")

    if results['version_mismatch'] > 0:
        print(f"Version mismatch: {results['version_mismatch']}")

    if args.verbose and results['errors']:
        print(f"\n{'='*40}")
        print("ERRORS")
        print(f"{'='*40}")
        for item in results['errors'][:10]:  # Limit to first 10
            print(f"\n{item['file']}:")
            for e in item['errors']:
                print(f"  - {e}")
        if len(results['errors']) > 10:
            print(f"\n... and {len(results['errors']) - 10} more files with errors")

    if args.verbose and results['warning_files']:
        print(f"\n{'='*40}")
        print("WARNINGS")
        print(f"{'='*40}")
        for item in results['warning_files'][:10]:
            print(f"\n{item['file']}:")
            for w in item['warnings']:
                print(f"  - {w}")
        if len(results['warning_files']) > 10:
            print(f"\n... and {len(results['warning_files']) - 10} more files with warnings")

    print()

    # Exit code
    if results['invalid'] > 0:
        print("Validation FAILED")
        sys.exit(1)
    else:
        print("Validation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
