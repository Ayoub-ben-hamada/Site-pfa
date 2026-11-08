"""
Cache layer for analytics results to avoid expensive recalculations.
"""
from datetime import datetime
from sqlalchemy.orm import Session

# Global cache for target_analysis results
_ANALYSIS_CACHE: dict = {}
_ANALYSIS_CACHE_TTL_SECONDS = 300  # 5 minutes


def get_cached_target_analysis(db: Session, variable: str, target_analysis_fn):
    """
    Retrieve target_analysis result from cache if valid, else compute and cache.
    
    Args:
        db: Database session
        variable: Analysis variable name
        target_analysis_fn: The actual target_analysis function to call if cache misses
    
    Returns:
        Cached or freshly computed target_analysis result
    """
    from app.services.analytics import _rows
    
    global _ANALYSIS_CACHE
    now = datetime.now()
    
    # Check if cached result exists and is still fresh
    if variable in _ANALYSIS_CACHE:
        cached = _ANALYSIS_CACHE[variable]
        elapsed = (now - cached["timestamp"]).total_seconds()
        # Get current row count for validation
        try:
            current_rows = len(_rows(db))
        except Exception:
            current_rows = None
        
        # Return cached if not expired and row count unchanged
        if (elapsed < _ANALYSIS_CACHE_TTL_SECONDS and 
            current_rows is not None and 
            cached["n_rows"] == current_rows):
            return cached["result"]
    
    # Cache miss or invalidated: compute fresh result
    result = target_analysis_fn(db, variable)
    try:
        n_rows = len(_rows(db))
    except Exception:
        n_rows = 0
    
    _ANALYSIS_CACHE[variable] = {
        "result": result,
        "timestamp": now,
        "n_rows": n_rows,
    }
    return result


def clear_cache(variable: str = None):
    """Clear cache for a specific variable or all variables."""
    global _ANALYSIS_CACHE
    if variable:
        _ANALYSIS_CACHE.pop(variable, None)
    else:
        _ANALYSIS_CACHE.clear()
