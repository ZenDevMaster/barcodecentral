"""
Statistics utilities for Barcode Central
Provides functions for calculating print job statistics
"""
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict


def calculate_print_statistics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive print statistics from history entries
    
    Args:
        entries: List of history entries
        
    Returns:
        Dictionary containing various statistics
    """
    if not entries:
        return {
            'total_prints': 0,
            'total_labels': 0,
            'success_count': 0,
            'failed_count': 0,
            'success_rate': 0.0,
            'average_quantity': 0.0
        }
    
    total_prints = len(entries)
    total_labels = sum(entry.get('quantity', 1) for entry in entries)
    success_count = sum(1 for entry in entries if entry.get('status') == 'success')
    failed_count = sum(1 for entry in entries if entry.get('status') == 'failed')
    success_rate = (success_count / total_prints * 100) if total_prints > 0 else 0.0
    average_quantity = total_labels / total_prints if total_prints > 0 else 0.0
    
    return {
        'total_prints': total_prints,
        'total_labels': total_labels,
        'success_count': success_count,
        'failed_count': failed_count,
        'success_rate': round(success_rate, 2),
        'average_quantity': round(average_quantity, 2)
    }


def get_top_templates(entries: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most frequently used templates
    
    Args:
        entries: List of history entries
        limit: Maximum number of templates to return
        
    Returns:
        List of dictionaries with template name and count
    """
    template_counts = defaultdict(int)
    template_names = {}
    
    for entry in entries:
        template = entry.get('template', 'unknown')
        template_counts[template] += 1
        # Store template display name if available
        if 'template_name' in entry:
            template_names[template] = entry['template_name']
    
    # Sort by count (descending)
    sorted_templates = sorted(
        template_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [
        {
            'template': template,
            'name': template_names.get(template, template),
            'count': count
        }
        for template, count in sorted_templates
    ]


def get_top_printers(entries: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most frequently used printers
    
    Args:
        entries: List of history entries
        limit: Maximum number of printers to return
        
    Returns:
        List of dictionaries with printer ID and count
    """
    printer_counts = defaultdict(int)
    printer_names = {}
    
    for entry in entries:
        printer_id = entry.get('printer_id', 'unknown')
        printer_counts[printer_id] += 1
        # Store printer display name if available
        if 'printer_name' in entry:
            printer_names[printer_id] = entry['printer_name']
    
    # Sort by count (descending)
    sorted_printers = sorted(
        printer_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [
        {
            'printer_id': printer_id,
            'name': printer_names.get(printer_id, printer_id),
            'count': count
        }
        for printer_id, count in sorted_printers
    ]


def get_print_volume_by_date(
    entries: List[Dict[str, Any]],
    grouping: str = 'day'
) -> Dict[str, int]:
    """
    Get print volume grouped by date
    
    Args:
        entries: List of history entries
        grouping: Grouping level ('day', 'week', 'month')
        
    Returns:
        Dictionary mapping date strings to print counts
    """
    volume_by_date = defaultdict(int)
    
    for entry in entries:
        timestamp = entry.get('timestamp', '')
        if not timestamp:
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if grouping == 'day':
                date_key = dt.strftime('%Y-%m-%d')
            elif grouping == 'week':
                # ISO week format: YYYY-Www
                date_key = dt.strftime('%Y-W%W')
            elif grouping == 'month':
                date_key = dt.strftime('%Y-%m')
            else:
                date_key = dt.strftime('%Y-%m-%d')
            
            volume_by_date[date_key] += 1
            
        except (ValueError, AttributeError):
            continue
    
    # Sort by date
    return dict(sorted(volume_by_date.items()))


def get_success_rate(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate success vs failure rate
    
    Args:
        entries: List of history entries
        
    Returns:
        Dictionary with success/failure statistics
    """
    if not entries:
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'success_rate': 0.0,
            'failure_rate': 0.0
        }
    
    total = len(entries)
    success = sum(1 for entry in entries if entry.get('status') == 'success')
    failed = sum(1 for entry in entries if entry.get('status') == 'failed')
    
    success_rate = (success / total * 100) if total > 0 else 0.0
    failure_rate = (failed / total * 100) if total > 0 else 0.0
    
    return {
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': round(success_rate, 2),
        'failure_rate': round(failure_rate, 2)
    }


def get_average_quantity(entries: List[Dict[str, Any]]) -> float:
    """
    Calculate average labels per print job
    
    Args:
        entries: List of history entries
        
    Returns:
        Average quantity as float
    """
    if not entries:
        return 0.0
    
    total_labels = sum(entry.get('quantity', 1) for entry in entries)
    return round(total_labels / len(entries), 2)


def get_user_statistics(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get statistics by user
    
    Args:
        entries: List of history entries
        
    Returns:
        List of dictionaries with user statistics
    """
    user_stats = defaultdict(lambda: {'prints': 0, 'labels': 0, 'success': 0, 'failed': 0})
    
    for entry in entries:
        user = entry.get('user', 'unknown')
        user_stats[user]['prints'] += 1
        user_stats[user]['labels'] += entry.get('quantity', 1)
        
        if entry.get('status') == 'success':
            user_stats[user]['success'] += 1
        elif entry.get('status') == 'failed':
            user_stats[user]['failed'] += 1
    
    # Convert to list and calculate success rates
    result = []
    for user, stats in user_stats.items():
        success_rate = (stats['success'] / stats['prints'] * 100) if stats['prints'] > 0 else 0.0
        result.append({
            'user': user,
            'prints': stats['prints'],
            'labels': stats['labels'],
            'success': stats['success'],
            'failed': stats['failed'],
            'success_rate': round(success_rate, 2)
        })
    
    # Sort by print count (descending)
    result.sort(key=lambda x: x['prints'], reverse=True)
    
    return result


def get_label_size_distribution(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get distribution of label sizes used
    
    Args:
        entries: List of history entries
        
    Returns:
        Dictionary mapping label sizes to counts
    """
    size_counts = defaultdict(int)
    
    for entry in entries:
        label_size = entry.get('label_size', 'unknown')
        size_counts[label_size] += 1
    
    return dict(sorted(size_counts.items(), key=lambda x: x[1], reverse=True))


def get_hourly_distribution(entries: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Get print volume by hour of day
    
    Args:
        entries: List of history entries
        
    Returns:
        Dictionary mapping hour (0-23) to print counts
    """
    hourly_counts = defaultdict(int)
    
    for entry in entries:
        timestamp = entry.get('timestamp', '')
        if not timestamp:
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            hourly_counts[hour] += 1
        except (ValueError, AttributeError):
            continue
    
    # Ensure all hours are present (0-23)
    result = {hour: hourly_counts.get(hour, 0) for hour in range(24)}
    
    return result


def get_recent_activity(entries: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
    """
    Get activity statistics for recent period
    
    Args:
        entries: List of history entries
        days: Number of days to analyze
        
    Returns:
        Dictionary with recent activity statistics
    """
    from datetime import timedelta
    
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
    recent_entries = [e for e in entries if e.get('timestamp', '') >= cutoff_date]
    
    if not recent_entries:
        return {
            'period_days': days,
            'total_prints': 0,
            'total_labels': 0,
            'daily_average': 0.0
        }
    
    total_prints = len(recent_entries)
    total_labels = sum(entry.get('quantity', 1) for entry in recent_entries)
    daily_average = total_prints / days if days > 0 else 0.0
    
    return {
        'period_days': days,
        'total_prints': total_prints,
        'total_labels': total_labels,
        'daily_average': round(daily_average, 2)
    }