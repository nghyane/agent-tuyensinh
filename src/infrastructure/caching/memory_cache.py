"""
In-memory cache implementation
"""

import time
from typing import Optional, Any, Dict
from collections import OrderedDict


class MemoryCacheService:
    """
    In-memory cache implementation with TTL and LRU eviction
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache storage: key -> (value, expiry_time)
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "expired": 0
        }
        
        print(f"💾 Memory cache initialized: max_size={max_size}, ttl={default_ttl}s")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            current_time = time.time()
            
            if key in self._cache:
                value, expiry_time = self._cache[key]
                
                # Check if expired
                if current_time > expiry_time:
                    del self._cache[key]
                    self._stats["expired"] += 1
                    self._stats["misses"] += 1
                    return None
                
                # Move to end (LRU)
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                
                return value
            else:
                self._stats["misses"] += 1
                return None
                
        except Exception as e:
            print(f"❌ Cache get failed for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl_seconds or self.default_ttl
            expiry_time = time.time() + ttl
            
            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Remove oldest item (LRU)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            # Set the value
            self._cache[key] = (value, expiry_time)
            self._cache.move_to_end(key)  # Move to end
            self._stats["sets"] += 1
            
        except Exception as e:
            print(f"❌ Cache set failed for key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        try:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                
        except Exception as e:
            print(f"❌ Cache delete failed for key {key}: {e}")
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        try:
            cache_size = len(self._cache)
            self._cache.clear()
            print(f"🧹 Cache cleared: {cache_size} entries removed")
            
        except Exception as e:
            print(f"❌ Cache clear failed: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        
        # Count expired entries
        expired_count = 0
        for value, expiry_time in self._cache.values():
            if current_time > expiry_time:
                expired_count += 1
        
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "type": "memory",
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "expired_entries": expired_count,
            **self._stats
        }
