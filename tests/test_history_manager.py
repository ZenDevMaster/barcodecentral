"""
Unit tests for HistoryManager
"""
import pytest
import os
import json
from datetime import datetime, timedelta
from history_manager import HistoryManager


class TestHistoryManager:
    """Tests for HistoryManager class"""
    
    @pytest.fixture
    def temp_history_file(self, tmp_path):
        """Create a temporary history file"""
        history_file = tmp_path / "history.json"
        return str(history_file)
    
    @pytest.fixture
    def manager(self, temp_history_file):
        """Create a HistoryManager instance with temp file"""
        return HistoryManager(history_file=temp_history_file, max_entries=100)
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample print job data"""
        return {
            'template': 'test_template.zpl.j2',
            'printer_id': 'test-printer-001',
            'printer_name': 'Test Printer',
            'variables': {'text': 'Test Label'},
            'copies': 1,
            'status': 'success',
            'zpl_content': '^XA^FO50,50^FDTest Label^FS^XZ'
        }
    
    # Initialization tests
    def test_init_creates_history_file(self, temp_history_file):
        """Test that initialization creates history file"""
        manager = HistoryManager(history_file=temp_history_file)
        assert os.path.exists(temp_history_file)
        
        # Verify structure
        with open(temp_history_file, 'r') as f:
            data = json.load(f)
        assert 'entries' in data
        assert isinstance(data['entries'], list)
    
    def test_init_with_existing_file(self, temp_history_file):
        """Test initialization with existing file"""
        # Create file with data
        initial_data = {
            'entries': [{'id': 'test-1', 'timestamp': '2024-01-15T10:00:00Z'}],
            'last_updated': '2024-01-15T10:00:00Z'
        }
        with open(temp_history_file, 'w') as f:
            json.dump(initial_data, f)
        
        manager = HistoryManager(history_file=temp_history_file)
        entries, _ = manager.get_entries()
        assert len(entries) == 1
    
    # Add entry tests
    def test_add_entry_success(self, manager, sample_job_data):
        """Test adding a history entry"""
        success, entry_id = manager.add_entry(sample_job_data)
        
        assert success is True
        assert entry_id is not None
        
        # Verify entry was added
        entry = manager.get_entry(entry_id)
        assert entry is not None
        assert entry['template'] == 'test_template.zpl.j2'
    
    def test_add_entry_generates_id(self, manager, sample_job_data):
        """Test that entry ID is generated if not provided"""
        success, entry_id = manager.add_entry(sample_job_data)
        
        assert success is True
        assert entry_id is not None
        assert len(entry_id) > 0
    
    def test_add_entry_uses_provided_id(self, manager, sample_job_data):
        """Test that provided ID is used"""
        sample_job_data['id'] = 'custom-id-123'
        success, entry_id = manager.add_entry(sample_job_data)
        
        assert success is True
        assert entry_id == 'custom-id-123'
    
    def test_add_entry_adds_timestamp(self, manager, sample_job_data):
        """Test that timestamp is added if not present"""
        success, entry_id = manager.add_entry(sample_job_data)
        
        entry = manager.get_entry(entry_id)
        assert 'timestamp' in entry
        assert entry['timestamp'] is not None
    
    def test_add_entry_preserves_timestamp(self, manager, sample_job_data):
        """Test that existing timestamp is preserved"""
        custom_timestamp = '2024-01-15T10:00:00Z'
        sample_job_data['timestamp'] = custom_timestamp
        
        success, entry_id = manager.add_entry(sample_job_data)
        entry = manager.get_entry(entry_id)
        assert entry['timestamp'] == custom_timestamp
    
    def test_add_entry_rotation(self, manager, sample_job_data):
        """Test that old entries are rotated when max is reached"""
        # Set low max for testing
        manager.max_entries = 10
        
        # Add more than max entries
        for i in range(15):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            manager.add_entry(job)
        
        # Should only have last 10 entries
        entries, total = manager.get_entries(limit=100)
        assert len(entries) == 10
        assert entries[0]['id'] == 'job-14'  # Newest first
        assert entries[-1]['id'] == 'job-5'  # Oldest kept
    
    # Get entries tests
    def test_get_entries_empty(self, manager):
        """Test getting entries when none exist"""
        entries, total = manager.get_entries()
        assert entries == []
        assert total == 0
    
    def test_get_entries_pagination(self, manager, sample_job_data):
        """Test pagination of entries"""
        # Add multiple entries
        for i in range(25):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            manager.add_entry(job)
        
        # Get first page
        entries, total = manager.get_entries(limit=10, offset=0)
        assert len(entries) == 10
        assert total == 25
        
        # Get second page
        entries, total = manager.get_entries(limit=10, offset=10)
        assert len(entries) == 10
        assert total == 25
    
    def test_get_entries_sorted_newest_first(self, manager, sample_job_data):
        """Test that entries are sorted newest first"""
        # Add entries with different timestamps
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['timestamp'] = f'2024-01-{15+i:02d}T10:00:00Z'
            manager.add_entry(job)
        
        entries, _ = manager.get_entries()
        assert entries[0]['id'] == 'job-4'  # Newest
        assert entries[-1]['id'] == 'job-0'  # Oldest
    
    def test_get_entries_filter_by_template(self, manager, sample_job_data):
        """Test filtering entries by template"""
        # Add entries with different templates
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['template'] = f'template{i % 2}.zpl.j2'
            manager.add_entry(job)
        
        entries, total = manager.get_entries(template='template0.zpl.j2')
        assert len(entries) == 3
        assert all(e['template'] == 'template0.zpl.j2' for e in entries)
    
    def test_get_entries_filter_by_printer(self, manager, sample_job_data):
        """Test filtering entries by printer ID"""
        # Add entries with different printers
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['printer_id'] = f'printer-{i % 2}'
            manager.add_entry(job)
        
        entries, total = manager.get_entries(printer_id='printer-0')
        assert len(entries) == 3
        assert all(e['printer_id'] == 'printer-0' for e in entries)
    
    def test_get_entries_filter_by_status(self, manager, sample_job_data):
        """Test filtering entries by status"""
        # Add entries with different statuses
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['status'] = 'success' if i % 2 == 0 else 'failed'
            manager.add_entry(job)
        
        entries, total = manager.get_entries(status='success')
        assert len(entries) == 3
        assert all(e['status'] == 'success' for e in entries)
    
    def test_get_entries_filter_by_date_range(self, manager, sample_job_data):
        """Test filtering entries by date range"""
        # Add entries with different dates
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['timestamp'] = f'2024-01-{15+i:02d}T10:00:00Z'
            manager.add_entry(job)
        
        entries, total = manager.get_entries(
            start_date='2024-01-16T00:00:00Z',
            end_date='2024-01-18T23:59:59Z'
        )
        assert len(entries) == 3  # Days 16, 17, 18
    
    def test_get_entries_limit_cap(self, manager, sample_job_data):
        """Test that limit is capped at 500"""
        # Add many entries
        for i in range(600):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            manager.add_entry(job)
        
        entries, total = manager.get_entries(limit=1000)
        assert len(entries) <= 500
    
    # Get entry tests
    def test_get_entry_success(self, manager, sample_job_data):
        """Test getting a specific entry"""
        success, entry_id = manager.add_entry(sample_job_data)
        
        entry = manager.get_entry(entry_id)
        assert entry is not None
        assert entry['id'] == entry_id
        assert entry['template'] == 'test_template.zpl.j2'
    
    def test_get_entry_not_found(self, manager):
        """Test getting non-existent entry returns None"""
        entry = manager.get_entry('nonexistent')
        assert entry is None
    
    # Delete entry tests
    def test_delete_entry_success(self, manager, sample_job_data):
        """Test deleting an entry"""
        success, entry_id = manager.add_entry(sample_job_data)
        
        success, message = manager.delete_entry(entry_id)
        assert success is True
        
        # Verify deletion
        entry = manager.get_entry(entry_id)
        assert entry is None
    
    def test_delete_entry_not_found(self, manager):
        """Test deleting non-existent entry"""
        success, message = manager.delete_entry('nonexistent')
        assert success is False
        assert 'not found' in message.lower()
    
    # Search entries tests
    def test_search_entries_all_fields(self, manager, sample_job_data):
        """Test searching across all fields"""
        # Add entries with different data
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['variables'] = {'text': f'Label {i}'}
            manager.add_entry(job)
        
        results = manager.search_entries('Label 2')
        assert len(results) == 1
        assert results[0]['variables']['text'] == 'Label 2'
    
    def test_search_entries_specific_field(self, manager, sample_job_data):
        """Test searching specific field"""
        # Add entries
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['printer_name'] = f'Printer {i}'
            manager.add_entry(job)
        
        results = manager.search_entries('Printer 3', field='printer_name')
        assert len(results) == 1
        assert results[0]['printer_name'] == 'Printer 3'
    
    def test_search_entries_case_insensitive(self, manager, sample_job_data):
        """Test that search is case insensitive"""
        sample_job_data['printer_name'] = 'Test Printer'
        manager.add_entry(sample_job_data)
        
        results = manager.search_entries('test printer')
        assert len(results) == 1
    
    def test_search_entries_no_results(self, manager, sample_job_data):
        """Test search with no matching results"""
        manager.add_entry(sample_job_data)
        
        results = manager.search_entries('nonexistent')
        assert results == []
    
    # Get statistics tests
    def test_get_statistics_empty(self, manager):
        """Test statistics with no entries"""
        stats = manager.get_statistics()
        assert stats['total_jobs'] == 0
        assert stats['successful_jobs'] == 0
        assert stats['failed_jobs'] == 0
    
    def test_get_statistics_with_data(self, manager, sample_job_data):
        """Test statistics calculation"""
        # Add successful jobs
        for i in range(7):
            job = sample_job_data.copy()
            job['id'] = f'success-{i}'
            job['status'] = 'success'
            manager.add_entry(job)
        
        # Add failed jobs
        for i in range(3):
            job = sample_job_data.copy()
            job['id'] = f'failed-{i}'
            job['status'] = 'failed'
            manager.add_entry(job)
        
        stats = manager.get_statistics()
        assert stats['total_jobs'] == 10
        assert stats['successful_jobs'] == 7
        assert stats['failed_jobs'] == 3
        assert stats['success_rate'] == 70.0
    
    def test_get_statistics_most_used_template(self, manager, sample_job_data):
        """Test most used template statistic"""
        # Add jobs with different templates
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['template'] = 'template1.zpl.j2' if i < 3 else 'template2.zpl.j2'
            manager.add_entry(job)
        
        stats = manager.get_statistics()
        assert stats['most_used_template'] == 'template1.zpl.j2'
    
    def test_get_statistics_most_used_printer(self, manager, sample_job_data):
        """Test most used printer statistic"""
        # Add jobs with different printers
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['printer_id'] = 'printer-1' if i < 4 else 'printer-2'
            manager.add_entry(job)
        
        stats = manager.get_statistics()
        assert stats['most_used_printer'] == 'printer-1'
    
    # Cleanup old entries tests
    def test_cleanup_old_entries(self, manager, sample_job_data):
        """Test cleaning up old entries"""
        # Add old entries
        old_date = (datetime.utcnow() - timedelta(days=100)).isoformat() + 'Z'
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'old-{i}'
            job['timestamp'] = old_date
            manager.add_entry(job)
        
        # Add recent entries
        recent_date = datetime.utcnow().isoformat() + 'Z'
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'recent-{i}'
            job['timestamp'] = recent_date
            manager.add_entry(job)
        
        # Cleanup entries older than 60 days
        success, message = manager.cleanup_old_entries(days=60)
        assert success is True
        
        # Should only have recent entries
        entries, total = manager.get_entries(limit=100)
        assert total == 5
        assert all('recent' in e['id'] for e in entries)
    
    def test_cleanup_no_old_entries(self, manager, sample_job_data):
        """Test cleanup when no old entries exist"""
        # Add only recent entries
        manager.add_entry(sample_job_data)
        
        success, message = manager.cleanup_old_entries(days=30)
        assert success is True
        assert 'removed' in message.lower() or 'deleted' in message.lower()
    
    # Export history tests
    def test_export_history(self, manager, sample_job_data):
        """Test exporting history"""
        # Add some entries
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            manager.add_entry(job)
        
        export_data = manager.export_history()
        assert 'entries' in export_data
        assert len(export_data['entries']) == 5
        assert 'exported_at' in export_data
        assert 'total_entries' in export_data
    
    def test_export_history_filtered(self, manager, sample_job_data):
        """Test exporting filtered history"""
        # Add entries with different templates
        for i in range(5):
            job = sample_job_data.copy()
            job['id'] = f'job-{i}'
            job['template'] = f'template{i % 2}.zpl.j2'
            manager.add_entry(job)
        
        export_data = manager.export_history(template='template0.zpl.j2')
        assert len(export_data['entries']) == 3