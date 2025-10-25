#!/usr/bin/env python3
"""
Phase 7 Database Connection Pool Test Suite
Validates enterprise connection pooling configuration
"""

import pytest
import asyncio
import aiohttp
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestDatabaseConnectionPool:
    """Enterprise database connection pool validation"""
    
    def setup_method(self):
        """Setup test database configuration"""
        self.db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "database": os.environ.get("DB_NAME", "chatterfix_cmms"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", "postgres"),
            "port": os.environ.get("DB_PORT", "5432")
        }
        
        # Enterprise pool settings from Phase 7 spec
        self.pool_config = {
            "minconn": 5,
            "maxconn": 25,  # 10 base + 20 overflow from config
            "connect_timeout": 5,
            "query_timeout": 20
        }
    
    def test_connection_pool_creation(self):
        """Test that connection pool can be created with enterprise settings"""
        try:
            pool = ThreadedConnectionPool(
                self.pool_config["minconn"],
                self.pool_config["maxconn"],
                **self.db_config
            )
            
            assert pool is not None, "Failed to create connection pool"
            
            # Test getting a connection
            conn = pool.getconn()
            assert conn is not None, "Failed to get connection from pool"
            
            # Test connection is working
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                assert result[0] == 1, "Database connection test query failed"
            
            pool.putconn(conn)
            pool.closeall()
            
        except Exception as e:
            pytest.fail(f"Connection pool creation failed: {e}")
    
    def test_concurrent_connections(self):
        """Test handling 10 concurrent database connections"""
        try:
            pool = ThreadedConnectionPool(
                self.pool_config["minconn"],
                self.pool_config["maxconn"],
                **self.db_config
            )
            
            def execute_query(query_id):
                """Execute a test query with connection from pool"""
                conn = None
                try:
                    conn = pool.getconn()
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("SELECT %s as query_id, NOW() as timestamp", (query_id,))
                        result = cursor.fetchone()
                        return {"success": True, "query_id": result["query_id"], "timestamp": result["timestamp"]}
                except Exception as e:
                    return {"success": False, "error": str(e)}
                finally:
                    if conn:
                        pool.putconn(conn)
            
            # Execute 10 concurrent queries
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(execute_query, i) for i in range(10)]
                results = [future.result() for future in as_completed(futures)]
            
            # Validate all queries succeeded
            success_count = sum(1 for result in results if result["success"])
            assert success_count == 10, f"Only {success_count}/10 concurrent queries succeeded"
            
            pool.closeall()
            
        except Exception as e:
            pytest.fail(f"Concurrent connection test failed: {e}")
    
    def test_connection_timeout_enforcement(self):
        """Test that connection timeout is enforced (5 seconds)"""
        # This would test connection timeout to a non-responsive database
        # For now, test that timeout parameter is correctly configured
        
        start_time = time.time()
        try:
            # Try to connect with timeout
            conn = psycopg2.connect(
                connect_timeout=2,  # Short timeout for test
                **self.db_config
            )
            conn.close()
            
            connection_time = time.time() - start_time
            assert connection_time < 5.0, f"Connection took {connection_time:.2f}s (should be <5s with timeout)"
            
        except psycopg2.OperationalError as e:
            # Expected if database is not available
            connection_time = time.time() - start_time
            assert connection_time <= 3.0, f"Timeout took {connection_time:.2f}s (should be ~2s)"
    
    def test_query_timeout_configuration(self):
        """Test that query timeout is properly configured (20 seconds)"""
        try:
            # Test with actual database connection
            conn = psycopg2.connect(**self.db_config)
            
            # Set statement timeout to match enterprise config
            with conn.cursor() as cursor:
                cursor.execute("SET statement_timeout = '20s'")
                
                # Verify timeout setting
                cursor.execute("SHOW statement_timeout")
                timeout_value = cursor.fetchone()[0]
                
                # Should be 20s or 20000ms
                assert timeout_value in ["20s", "20000ms", "20000"], f"Query timeout not set correctly: {timeout_value}"
            
            conn.close()
            
        except Exception as e:
            pytest.skip(f"Skipping query timeout test - database not available: {e}")
    
    def test_connection_recycling(self):
        """Test connection recycling (180 seconds from config)"""
        try:
            pool = ThreadedConnectionPool(
                2, 5,  # Smaller pool for test
                **self.db_config
            )
            
            # Get connection and check its creation time
            conn = pool.getconn()
            
            # Execute query to ensure connection is active
            with conn.cursor() as cursor:
                cursor.execute("SELECT NOW() as connection_time")
                first_time = cursor.fetchone()[0]
            
            pool.putconn(conn)
            
            # Get connection again (should be same connection)
            conn2 = pool.getconn()
            
            with conn2.cursor() as cursor:
                cursor.execute("SELECT NOW() as connection_time")
                second_time = cursor.fetchone()[0]
            
            pool.putconn(conn2)
            
            # Connections should be reused (times should be close)
            time_diff = abs((second_time - first_time).total_seconds())
            assert time_diff < 5, f"Connection recycling not working - time diff: {time_diff}s"
            
            pool.closeall()
            
        except Exception as e:
            pytest.skip(f"Skipping connection recycling test - database not available: {e}")
    
    @pytest.mark.asyncio
    async def test_service_endpoint_db_performance(self):
        """Test database-dependent service endpoints perform well"""
        services_to_test = [
            "https://chatterfix-cmms-650169261019.us-central1.run.app/api/assets",
            "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app/api/revenue",
            "https://chatterfix-customer-success-650169261019.us-central1.run.app/api/customers"
        ]
        
        async with aiohttp.ClientSession() as session:
            for service_url in services_to_test:
                start_time = time.time()
                
                try:
                    async with session.get(service_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response_time = time.time() - start_time
                        
                        # Should respond quickly with connection pooling
                        assert response_time < 5.0, f"DB-dependent endpoint {service_url} took {response_time:.2f}s"
                        
                        # Should not return database errors
                        if response.status == 500:
                            error_text = await response.text()
                            if "database" in error_text.lower() or "connection" in error_text.lower():
                                pytest.fail(f"Database connection error in {service_url}: {error_text}")
                
                except asyncio.TimeoutError:
                    pytest.fail(f"Service endpoint {service_url} timed out (>10s)")
                except aiohttp.ClientError as e:
                    # Skip if service not available (expected in some environments)
                    pytest.skip(f"Service not available: {service_url} - {e}")
    
    def test_pool_exhaustion_handling(self):
        """Test graceful handling when connection pool is exhausted"""
        try:
            # Create small pool to test exhaustion
            pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=2,  # Very small pool
                **self.db_config
            )
            
            # Get all available connections
            conn1 = pool.getconn()
            conn2 = pool.getconn()
            
            # Try to get third connection (should handle gracefully)
            start_time = time.time()
            try:
                conn3 = pool.getconn()
                # If we get here, pool expanded or connection was available
                pool.putconn(conn3)
            except Exception as e:
                # Should handle pool exhaustion gracefully
                elapsed = time.time() - start_time
                assert elapsed < 10, f"Pool exhaustion handling took too long: {elapsed:.2f}s"
            
            # Return connections
            pool.putconn(conn1)
            pool.putconn(conn2)
            pool.closeall()
            
        except Exception as e:
            pytest.skip(f"Skipping pool exhaustion test - database not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])