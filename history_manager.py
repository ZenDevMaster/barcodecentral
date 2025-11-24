"""
History Manager Module for Barcode Central
Handles print job history tracking, storage, and retrieval
"""
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.json_storage import read_json, write_json

# Configure logging
logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages print job history with JSON file storage"""
    
    def __init__(self, history_file: str = 'history.json', max_entries: int = 1000):
        """
        Initialize the history manager
        
        Args:
            history_file: Path to the history JSON file
            max_entries: Maximum number of entries to keep (oldest are removed)
        """
        self.history_file = history_file
        self.max_entries = max_entries
        self._ensure_history_file()
    
    def _ensure_history_file(self) -> None:
        """Ensure history file exists with proper structure"""
        try:
            data = read_json(self.history_file)
            if not isinstance(data, dict) or 'entries' not in data:
                # Initialize with proper structure
                initial_data = {
                    'entries': [],
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }
                write_json(self.history_file, initial_data)
                logger.info(f"Initialized history file: {self.history_file}")
        except Exception as e:
            logger.error(f"Error ensuring history file: {e}")
    
    def _load_history(self) -> Dict[str, Any]:
        """
        Load history data from file
        
        Returns:
            Dictionary containing entries and metadata
        """
        data = read_json(self.history_file, default={'entries': [], 'last_updated': None})
        if not isinstance(data.get('entries'), list):
            data['entries'] = []
        return data
    
    def _save_history(self, data: Dict[str, Any]) -> bool:
        """
        Save history data to file
        
        Args:
            data: History data to save
            
        Returns:
            True if successful, False otherwise
        """
        data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        return write_json(self.history_file, data)
    
    def add_entry(self, job_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add a new history entry
        
        Args:
            job_data: Print job data to log
            
        Returns:
            Tuple of (success, entry_id_or_error_message)
        """
        try:
            # Load current history
            history = self._load_history()
            
            # Generate unique ID if not provided
            entry_id = job_data.get('id', str(uuid.uuid4()))
            
            # Ensure timestamp is present
            if 'timestamp' not in job_data:
                job_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            # Create entry with ID
            entry = {
                'id': entry_id,
                **job_data
            }
            
            # Add to entries list
            history['entries'].append(entry)
            
            # Rotate if needed (keep only the most recent max_entries)
            if len(history['entries']) > self.max_entries:
                history['entries'] = history['entries'][-self.max_entries:]
                logger.info(f"Rotated history, keeping last {self.max_entries} entries")
            
            # Save to file
            if self._save_history(history):
                logger.info(f"Added history entry: {entry_id}")
                return True, entry_id
            else:
                return False, "Failed to save history"
                
        except Exception as e:
            error_msg = f"Error adding history entry: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        template: Optional[str] = None,
        printer_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paginated and filtered history entries
        
        Args:
            limit: Maximum number of entries to return (max 500)
            offset: Number of entries to skip
            template: Filter by template name
            printer_id: Filter by printer ID
            status: Filter by status (success/failed)
            start_date: Filter by start date (ISO 8601)
            end_date: Filter by end date (ISO 8601)
            
        Returns:
            Tuple of (entries_list, total_count)
        """
        try:
            # Load history
            history = self._load_history()
            entries = history.get('entries', [])
            
            # Apply filters
            filtered_entries = []
            for entry in entries:
                # Template filter
                if template and entry.get('template') != template:
                    continue
                
                # Printer filter
                if printer_id and entry.get('printer_id') != printer_id:
                    continue
                
                # Status filter
                if status and entry.get('status') != status:
                    continue
                
                # Date range filter
                if start_date or end_date:
                    entry_timestamp = entry.get('timestamp', '')
                    if start_date and entry_timestamp < start_date:
                        continue
                    if end_date and entry_timestamp > end_date:
                        continue
                
                filtered_entries.append(entry)
            
            # Sort by timestamp (newest first)
            filtered_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Get total count before pagination
            total_count = len(filtered_entries)
            
            # Apply pagination
            limit = min(limit, 500)  # Cap at 500
            paginated_entries = filtered_entries[offset:offset + limit]
            
            return paginated_entries, total_count
            
        except Exception as e:
            logger.error(f"Error getting history entries: {e}")
            return [], 0
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry by ID
        
        Args:
            entry_id: The entry ID to retrieve
            
        Returns:
            Entry dictionary or None if not found
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            for entry in entries:
                if entry.get('id') == entry_id:
                    return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting history entry {entry_id}: {e}")
            return None
    
    def delete_entry(self, entry_id: str) -> Tuple[bool, str]:
        """
        Delete a history entry
        
        Args:
            entry_id: The entry ID to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            # Find and remove entry
            original_count = len(entries)
            entries = [e for e in entries if e.get('id') != entry_id]
            
            if len(entries) == original_count:
                return False, "Entry not found"
            
            history['entries'] = entries
            
            if self._save_history(history):
                logger.info(f"Deleted history entry: {entry_id}")
                return True, "Entry deleted successfully"
            else:
                return False, "Failed to save history"
                
        except Exception as e:
            error_msg = f"Error deleting history entry: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def search_entries(
        self,
        query: str,
        field: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search history entries
        
        Args:
            query: Search query string
            field: Specific field to search (None = search all fields)
            
        Returns:
            List of matching entries
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            query_lower = query.lower()
            matching_entries = []
            
            for entry in entries:
                if field:
                    # Search specific field
                    field_value = str(entry.get(field, '')).lower()
                    if query_lower in field_value:
                        matching_entries.append(entry)
                else:
                    # Search all string fields
                    entry_str = str(entry).lower()
                    if query_lower in entry_str:
                        matching_entries.append(entry)
            
            # Sort by timestamp (newest first)
            matching_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return matching_entries
            
        except Exception as e:
            logger.error(f"Error searching history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics from history
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            if not entries:
                return {
                    'total_prints': 0,
                    'total_labels': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'success_rate': 0.0,
                    'templates': {},
                    'printers': {},
                    'users': {}
                }
            
            # Calculate statistics
            total_prints = len(entries)
            total_labels = sum(entry.get('quantity', 1) for entry in entries)
            success_count = sum(1 for entry in entries if entry.get('status') == 'success')
            failed_count = sum(1 for entry in entries if entry.get('status') == 'failed')
            success_rate = (success_count / total_prints * 100) if total_prints > 0 else 0.0
            
            # Count by template
            templates = {}
            for entry in entries:
                template = entry.get('template', 'unknown')
                templates[template] = templates.get(template, 0) + 1
            
            # Count by printer
            printers = {}
            for entry in entries:
                printer = entry.get('printer_id', 'unknown')
                printers[printer] = printers.get(printer, 0) + 1
            
            # Count by user
            users = {}
            for entry in entries:
                user = entry.get('user', 'unknown')
                users[user] = users.get(user, 0) + 1
            
            return {
                'total_prints': total_prints,
                'total_labels': total_labels,
                'success_count': success_count,
                'failed_count': failed_count,
                'success_rate': round(success_rate, 2),
                'templates': templates,
                'printers': printers,
                'users': users,
                'average_quantity': round(total_labels / total_prints, 2) if total_prints > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def cleanup_old_entries(self, days: int = 90) -> Tuple[bool, int]:
        """
        Delete entries older than specified days
        
        Args:
            days: Number of days to keep (delete older entries)
            
        Returns:
            Tuple of (success, number_deleted)
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            # Calculate cutoff date
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
            
            # Filter entries
            original_count = len(entries)
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_date]
            deleted_count = original_count - len(entries)
            
            if deleted_count > 0:
                history['entries'] = entries
                if self._save_history(history):
                    logger.info(f"Cleaned up {deleted_count} old history entries (older than {days} days)")
                    return True, deleted_count
                else:
                    return False, 0
            
            return True, 0
            
        except Exception as e:
            logger.error(f"Error cleaning up old entries: {e}")
            return False, 0
    
    def export_history(self, format: str = 'json') -> Tuple[bool, Any]:
        """
        Export history to specified format
        
        Args:
            format: Export format ('json' or 'csv')
            
        Returns:
            Tuple of (success, data_or_error_message)
        """
        try:
            history = self._load_history()
            entries = history.get('entries', [])
            
            if format == 'json':
                return True, entries
            
            elif format == 'csv':
                # Convert to CSV format
                if not entries:
                    return True, "id,timestamp,user,template,printer_id,quantity,status\n"
                
                # Get all unique keys
                keys = ['id', 'timestamp', 'user', 'template', 'printer_id', 'quantity', 'status']
                
                # Build CSV
                csv_lines = [','.join(keys)]
                for entry in entries:
                    values = [str(entry.get(key, '')) for key in keys]
                    csv_lines.append(','.join(values))
                
                return True, '\n'.join(csv_lines)
            
            else:
                return False, f"Unsupported format: {format}"
                
        except Exception as e:
            error_msg = f"Error exporting history: {str(e)}"
            logger.error(error_msg)
            return False, error_msg