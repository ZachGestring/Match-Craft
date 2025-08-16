import asyncio
import asyncpg
import os
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionType(Enum):
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    GET_ALL_ROLES = "get_all_roles"
    CHECK_ROLE = "check_role"

@dataclass
class DatabaseTransaction:
    transaction_type: TransactionType
    role_id: Optional[int] = None
    future: Optional[asyncio.Future] = None

class DatabaseManager:
    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.transaction_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the database connection pool and start the worker"""
        try:
            # Get database connection details from environment
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                # Fallback to individual environment variables
                host = os.getenv('DB_HOST', 'db')
                port = int(os.getenv('DB_PORT', '5432'))
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', 'postgres')
                database = os.getenv('DB_NAME', 'postgres')
                
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("Database connection pool created successfully")
            
            # Start the transaction worker
            self.is_running = True
            self.worker_task = asyncio.create_task(self._transaction_worker())
            
            # Test the connection
            async with self.connection_pool.acquire() as conn:
                await conn.execute("SELECT 1")
                logger.info("Database connection test successful")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _transaction_worker(self):
        """Worker that processes database transactions from the queue"""
        while self.is_running:
            try:
                # Wait for a transaction
                transaction = await asyncio.wait_for(
                    self.transaction_queue.get(), 
                    timeout=1.0
                )
                
                # Process the transaction
                result = await self._execute_transaction(transaction)
                
                # Set the result in the future
                if transaction.future and not transaction.future.done():
                    transaction.future.set_result(result)
                    
            except asyncio.TimeoutError:
                # No transactions in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in transaction worker: {e}")
                # Set exception in future if available
                if transaction.future and not transaction.future.done():
                    transaction.future.set_exception(e)
    
    async def _execute_transaction(self, transaction: DatabaseTransaction):
        """Execute a single database transaction"""
        if not self.connection_pool:
            raise RuntimeError("Database not initialized")
            
        async with self.connection_pool.acquire() as conn:
            try:
                if transaction.transaction_type == TransactionType.ADD_ROLE:
                    await conn.execute(
                        "INSERT INTO declared_roles (role_id) VALUES ($1) ON CONFLICT (role_id) DO NOTHING",
                        transaction.role_id
                    )
                    return True
                    
                elif transaction.transaction_type == TransactionType.REMOVE_ROLE:
                    result = await conn.execute(
                        "DELETE FROM declared_roles WHERE role_id = $1",
                        transaction.role_id
                    )
                    return result.split()[-1] != "0"  # Return True if a row was deleted
                    
                elif transaction.transaction_type == TransactionType.GET_ALL_ROLES:
                    rows = await conn.fetch("SELECT role_id FROM declared_roles ORDER BY role_id")
                    return [row['role_id'] for row in rows]
                    
                elif transaction.transaction_type == TransactionType.CHECK_ROLE:
                    row = await conn.fetchrow(
                        "SELECT role_id FROM declared_roles WHERE role_id = $1",
                        transaction.role_id
                    )
                    return row is not None
                    
            except Exception as e:
                logger.error(f"Database transaction failed: {e}")
                raise
    
    async def add_role(self, role_id: int) -> bool:
        """Add a role to the declared roles table"""
        future = asyncio.Future()
        transaction = DatabaseTransaction(
            transaction_type=TransactionType.ADD_ROLE,
            role_id=role_id,
            future=future
        )
        
        await self.transaction_queue.put(transaction)
        return await future
    
    async def remove_role(self, role_id: int) -> bool:
        """Remove a role from the declared roles table"""
        future = asyncio.Future()
        transaction = DatabaseTransaction(
            transaction_type=TransactionType.REMOVE_ROLE,
            role_id=role_id,
            future=future
        )
        
        await self.transaction_queue.put(transaction)
        return await future
    
    async def get_all_roles(self) -> List[int]:
        """Get all declared role IDs"""
        future = asyncio.Future()
        transaction = DatabaseTransaction(
            transaction_type=TransactionType.GET_ALL_ROLES,
            future=future
        )
        
        await self.transaction_queue.put(transaction)
        return await future
    
    async def check_role(self, role_id: int) -> bool:
        """Check if a role is declared as administrative"""
        future = asyncio.Future()
        transaction = DatabaseTransaction(
            transaction_type=TransactionType.CHECK_ROLE,
            role_id=role_id,
            future=future
        )
        
        await self.transaction_queue.put(transaction)
        return await future
    
    async def close(self):
        """Close the database manager and clean up resources"""
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()
