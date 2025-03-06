from app.search import bp
from datetime import datetime

@bp.app_template_filter('status_badge')
def status_badge_filter(status):
    """Convert a status to a Bootstrap badge class"""
    status_map = {
        'new': 'new',
        'contacted': 'contacted',
        'qualified': 'qualified',
        'unqualified': 'unqualified',
        'nurturing': 'nurturing',
        'converted': 'converted'
    }
    return status_map.get(status.lower(), 'secondary')

@bp.app_template_filter('format_datetime')
def format_datetime_filter(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object to a string"""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    return value.strftime(format)

@bp.app_template_filter('from_json')
def from_json_filter(value):
    """Convert a JSON string to a Python object"""
    import json
    if value is None:
        return {}
    try:
        return json.loads(value)
    except:
        return {}
