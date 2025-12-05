"""
Resource monitoring for ingestion process
"""
import psutil
import os

def check_system_resources() -> dict:
    """Check current system resource usage"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024),
        'pid': os.getpid()
    }

def should_pause_ingestion(memory_threshold: float = 80.0) -> bool:
    """
    Check if ingestion should pause due to resource constraints
    
    Args:
        memory_threshold: Pause if memory usage exceeds this percentage
        
    Returns:
        True if should pause
    """
    resources = check_system_resources()
    
    if resources['memory_percent'] > memory_threshold:
        print(f"\n⚠️  High memory usage: {resources['memory_percent']:.1f}%")
        print(f"   Available: {resources['memory_available_mb']:.0f} MB")
        return True
    
    return False