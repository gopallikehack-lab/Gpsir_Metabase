import os
import json
import subprocess
import tempfile

# ========== METADATA CATEGORIES ==========
CATEGORIES = {
    '📷 Camera & Lens': {
        'icon': '📷',
        'keys': ['Make', 'Model', 'CameraModelName', 'LensModel', 'LensInfo', 'LensID', 
                'LensMake', 'LensSerialNumber', 'LensSpecification']
    },
    '⚙️ Camera Settings': {
        'icon': '⚙️',
        'keys': ['ISO', 'ExposureTime', 'FNumber', 'FocalLength', 'FocalLengthIn35mmFormat',
                'Aperture', 'ShutterSpeed', 'ExposureProgram', 'ExposureMode', 'MeteringMode',
                'WhiteBalance', 'Flash', 'FlashMode', 'DigitalZoomRatio', 'ExposureCompensation',
                'ExposureTime', 'ApertureValue', 'BrightnessValue', 'MaxApertureValue']
    },
    '🖼️ Image Properties': {
        'icon': '🖼️',
        'keys': ['ImageWidth', 'ImageHeight', 'BitsPerSample', 'ColorSpace', 'ImageSize',
                'Megapixels', 'Resolution', 'ResolutionUnit', 'XResolution', 'YResolution',
                'Orientation', 'Compression', 'Quality', 'JFIFVersion', 'PixelDimensions']
    },
    '📅 Date & Time': {
        'icon': '📅',
        'keys': ['DateTimeOriginal', 'CreateDate', 'ModifyDate', 'DateTimeDigitized',
                'DateCreated', 'TimeCreated', 'SubSecTimeOriginal', 'OffsetTime',
                'ModifyDate', 'MetadataDate', 'DateAcquired']
    },
    '🌍 GPS Location': {
        'icon': '🌍',
        'keys': ['GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSPosition',
                'GPSLatitudeRef', 'GPSLongitudeRef', 'GPSAltitudeRef', 'GPSDateStamp',
                'GPSTimeStamp', 'GPSImgDirection', 'GPSDestBearing', 'GPSHPositioningError']
    },
    '📝 File Information': {
        'icon': '📝',
        'keys': ['FileName', 'FileSize', 'FileType', 'MIMEType', 'FilePermissions',
                'FileModifyDate', 'FileAccessDate', 'FileInodeChangeDate', 'FileExtension',
                'FileSize', 'Directory']
    },
    '🎨 Author & Copyright': {
        'icon': '🎨',
        'keys': ['Artist', 'Author', 'Creator', 'Copyright', 'CopyrightNotice',
                'Rights', 'Credit', 'Source', 'OwnerName', 'UsageTerms', 'CreatorWorkURL']
    },
    '🏷️ Description & Tags': {
        'icon': '🏷️',
        'keys': ['Description', 'ImageDescription', 'Caption', 'Title', 'ObjectName',
                'Keywords', 'Subject', 'Category', 'Headline', 'City', 'State', 'Country',
                'Location', 'CountryCode', 'ProvinceState', 'Sub-location']
    },
    '📱 Software & Device': {
        'icon': '📱',
        'keys': ['Software', 'HostComputer', 'CreatorTool', 'Producer', 'ApplicationName',
                'DeviceModel', 'DeviceManufacturer', 'Platform', 'OperatingSystem']
    },
    '🔧 Advanced EXIF': {
        'icon': '🔧',
        'keys': ['ExifVersion', 'FlashpixVersion', 'ComponentsConfiguration', 'ExposureIndex',
                'SensingMethod', 'SceneType', 'SceneCaptureType', 'GainControl',
                'Contrast', 'Saturation', 'Sharpness', 'SubjectDistance', 'SubjectArea',
                'LightSource', 'FocalPlaneXResolution', 'FocalPlaneYResolution']
    }
}

def extract_metadata(file_path):
    """Extract metadata using exiftool"""
    try:
        cmd = ['exiftool', '-j', '-a', '-G', '-n', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {'error': f'ExifTool error: {result.stderr}'}
        
        data = json.loads(result.stdout)
        if data and isinstance(data, list) and len(data) > 0:
            metadata = data[0]
            metadata.pop('SourceFile', None)
            metadata.pop('ExifToolVersion', None)
            return {'metadata': metadata}
        else:
            return {'error': 'No metadata found'}
            
    except FileNotFoundError:
        return {'error': 'ExifTool not installed. Install: apt-get install exiftool'}
    except subprocess.TimeoutExpired:
        return {'error': 'File processing timed out'}
    except Exception as e:
        return {'error': f'Error: {str(e)}'}

def parse_metadata_to_readable(raw_metadata):
    """Convert raw metadata into organized, user-friendly format"""
    
    result = {
        'summary': {},
        'categories': {},
        'all_raw': raw_metadata,
        'gps': None
    }
    
    # Extract summary
    summary_keys = ['FileName', 'Make', 'Model', 'DateTimeOriginal', 'ImageSize', 'FileSize']
    for key in summary_keys:
        if key in raw_metadata and raw_metadata[key]:
            result['summary'][key] = raw_metadata[key]
    
    # Extract GPS
    if 'GPSPosition' in raw_metadata:
        result['gps'] = raw_metadata['GPSPosition']
    elif 'GPSLatitude' in raw_metadata and 'GPSLongitude' in raw_metadata:
        result['gps'] = f"{raw_metadata['GPSLatitude']}, {raw_metadata['GPSLongitude']}"
    
    # Categorize
    for cat_name, cat_info in CATEGORIES.items():
        cat_data = {}
        for key in cat_info['keys']:
            if key in raw_metadata and raw_metadata[key] not in [None, '', '0']:
                value = raw_metadata[key]
                if isinstance(value, str):
                    value = value.strip()
                if value:
                    cat_data[key] = value
        if cat_data:
            result['categories'][cat_name] = {
                'icon': cat_info['icon'],
                'data': cat_data
            }
    
    # Unknown metadata
    known_keys = set()
    for cat in CATEGORIES.values():
        known_keys.update(cat['keys'])
    
    unknown_data = {}
    for key, value in raw_metadata.items():
        if key not in known_keys and key not in ['SourceFile', 'ExifToolVersion']:
            if value not in [None, '', '0']:
                unknown_data[key] = value
    
    if unknown_data:
        result['categories']['🔍 Other Information'] = {
            'icon': '🔍',
            'data': unknown_data
        }
    
    return result
