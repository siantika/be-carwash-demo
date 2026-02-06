from typing import List, Optional

import asyncpg

from domain.entities.service_type import ServiceType
from domain.repositories.i_service_type import IServiceTypeRepository
from domain.value_object.money import Money
from infra.error_handler import handle_db_error
from interfaces.i_logger import ILogger

SELECT_ALL_COLUMNS = """
                   id, name, description AS desc, 
                   price, is_active, 
                   is_primary,  created_at, updated_at
""".strip()

def _mapper(row: asyncpg.Record) -> ServiceType:
    return ServiceType(
        id = row["id"],
        name = row["name"],
        desc= row["desc"],
        price= Money(row['price']),
        is_active= row['is_active'],
        is_primary= row['is_primary'],
        created_at= row['created_at'],
        updated_at= row['updated_at']   
    )
    
    
class AsyncPgServiceTypeRepository(IServiceTypeRepository):
    def __init__(self, db: asyncpg.Connection, logger:ILogger):
        self.db = db  
        self.logger =logger 

    async def get_by_id(self, service_type_id: str) -> Optional[ServiceType]:
        async def _fetch():
            row = await self.db.fetchrow(f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_types
                WHERE id = $1
            """, service_type_id)
            return _mapper(row) if row else None
        
        return await handle_db_error(
            operation= _fetch,
            logger=self.logger,
            context={"service_type_id": service_type_id},
            operation_name="fetch service type by id"
        )

    async def get_by_name(self, service_name: str) -> Optional[ServiceType]:
        async def _fetch():
            row = await self.db.fetchrow(f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM service_types
                WHERE name = $1
            """, service_name)
            return _mapper(row) if row else None
        
        return await handle_db_error(
            operation= _fetch,
            logger=self.logger,
            context={"service_name": service_name},
            operation_name="fetch service type by service name"
        )
  
    async def add(self, data: ServiceType) -> ServiceType:
        async def _create():
            row = await self.db.fetchrow(f"""
                INSERT INTO service_types (name, description, 
                price, is_active, is_primary)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {SELECT_ALL_COLUMNS};
            """, data.name, data.desc, data.price ,data.is_active, data.is_primary)
            return _mapper(row)
        
        return await handle_db_error(
            operation= _create,
            logger=self.logger,
            context={"service_type_id": data.id},
            operation_name="create service type"
        )
        
    async def list(self, limit:int, offset:int) -> List[ServiceType]:
        async def _get():
            rows = await self.db.fetch(
                f"""
                    SELECT {SELECT_ALL_COLUMNS}
                    FROM service_types 
                    ORDER BY created_at DESC, id DESC
                    LIMIT $1 OFFSET $2
                """,
                limit,
                offset
            )
            return [_mapper(service_type) for service_type in rows]
        
        return await handle_db_error(
            operation= _get,
            logger=self.logger,
            context={"limit":limit, "offset":offset},
            operation_name="List service type"
        )
        
        
    async def save(
        self,
        data:ServiceType
    ) -> ServiceType:
        async def _update():
            row = await self.db.fetchrow(f"""
                UPDATE service_types
                SET name=$1, description = $2, 
                base_price= $3, is_active=$4,
                is_primary = $5
                WHERE id = $6
                RETURNING
                {SELECT_ALL_COLUMNS}
            """, data.name,
                data.desc,
                data.price.amount,
                data.is_active,
                data.is_primary,
                data.id
        )
            return _mapper(row)
        
        return await handle_db_error(
            operation= _update,
            logger=self.logger,
            context={"service_type_id": data.id},
            operation_name="update service type"
        )