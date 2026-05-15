from datetime import date, datetime, time, timedelta
from decimal import Decimal

import asyncpg

from app.modules.analytics.application.dto import (
    DailyRevenueDTO,
    DashboardSummaryDTO,
    PaymentMethodSummaryDTO,
    TopServiceDTO,
)
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger


class AsyncPgAnalyticsQueryRepository:
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger
        
    
    async def get_payment_method_summary(self, start_date: date, end_date:date)-> list[PaymentMethodSummaryDTO]:
        async def _fetch():
            start_timestamp  = datetime.combine(start_date, time.min)
            end_timestamp = datetime.combine(end_date, time.min) + timedelta(days=1)
            
            rows = await self.db.fetch(
                """
                SELECT
                    payment_method,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) AS total_amount
                FROM billing.payments
                WHERE payment_status = 'PAID'
                AND paid_at >= $1
                AND paid_at < $2
                GROUP BY payment_method
                ORDER BY total_amount;                
                """,
                start_timestamp,
                end_timestamp                
            )
            
            return [
                PaymentMethodSummaryDTO(
                    payment_method=row['payment_method'],
                    transaction_count= row['transaction_count'],
                    total_amount=row['total_amount']
                ) for row in rows
            ]
            
        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            operation_name="get payment method"
        )
        
    
    async def get_top_service(self, start_date: date, end_date: date, limit:int) -> list[TopServiceDTO]:
        async def _fetch():
            start_timestamp  = datetime.combine(start_date, time.min)
            end_timestamp = datetime.combine(end_date, time.min) + timedelta(days=1)
            
            rows = await self.db.fetch(
                """
                SELECT 
                    service_name_snapshot as service_name,
                    COUNT(*) AS total_sold,
                    SUM(service_base_price_snapshot) AS total_revenue  
                FROM
                    carwash_operation.tickets
                WHERE status = 'PAID'
                AND updated_at >= $1
                AND updated_at < $2
                GROUP BY service_name
                ORDER BY total_sold DESC
                LIMIT $3;
                
                """,
                start_timestamp,
                end_timestamp,
                limit
            )
            
            return [
                TopServiceDTO(
                    service_name=row['service_name'],
                    total_sold = row['total_sold'],
                    total_revenue=row['total_revenue']
                ) for row in rows
            ]
        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            operation_name="get top services"
        )
    
    async def get_daily_revenue(self, start_date: date, end_date: date) -> list[DailyRevenueDTO]:
        async def _fetch():
            start_timestamp  = datetime.combine(start_date, time.min)
            end_timestamp = datetime.combine(end_date, time.min) + timedelta(days=1)
            
            rows = await self.db.fetch(
                """
                SELECT
                    d.date_at::date AS date_at,
                    COALESCE(SUM(p.total_amount), 0) AS revenue,
                    COUNT(p.id) AS transaction_count
                FROM generate_series(
                    $1::date,
                    $2::date,
                    interval '1 day'
                ) AS d(date_at)
                LEFT JOIN billing.payments p
                    ON p.paid_at::date = d.date_at::date
                    AND p.payment_status = 'PAID'
                GROUP BY d.date_at
                ORDER BY d.date_at;
                """,
                start_timestamp,
                end_timestamp,
            ) 
            return [DailyRevenueDTO(
                date_at= row['date_at'],
                revenue= row['revenue'],
                transaction_count= row['transaction_count']
            ) for row in rows] 
        
        return await handle_db_error(
            operation= _fetch,
            logger= self.logger,
            operation_name= "Get daily revenue from start date till end date"
        )
    
    async def get_dashboard_summary(self, target_date: date) -> DashboardSummaryDTO:
        async def _fetch():
            start_date = datetime.combine(target_date, time.min)
            end_date = start_date + timedelta(days=1)
          
            row = await self.db.fetchrow(
                """
                WITH paid_today AS (
                    SELECT
                        COALESCE(SUM(total_amount), 0) AS today_revenue,
                        COUNT(*) AS today_transactions
                    FROM billing.payments
                    WHERE payment_status = 'PAID'
                    AND paid_at >= $1
                    AND paid_at < $2
                ),

                ticket_summary AS (
                    SELECT
                        COUNT(*) FILTER (
                            WHERE status IN ('IN_PROGRESS')
                        ) AS active_tickets,

                        COUNT(*) FILTER (
                            WHERE status = 'PAID'
                            AND updated_at >= $1
                            AND updated_at < $2
                        ) AS completed_tickets
                    FROM carwash_operation.tickets
                ),

                voided_today AS (
                    SELECT
                        COUNT(*) AS voided_transactions
                    FROM carwash_operation.ticket_voids
                    WHERE void_time >= $1
                    AND void_time < $2
                )

                SELECT
                    paid_today.today_revenue,
                    paid_today.today_transactions,
                    ticket_summary.active_tickets,
                    ticket_summary.completed_tickets,
                    voided_today.voided_transactions
                FROM paid_today
                CROSS JOIN ticket_summary
                CROSS JOIN voided_today;
                """,
                start_date,
                end_date,
            )

            return  DashboardSummaryDTO(
                today_revenue=row["today_revenue"] or Decimal("0"),
                today_transactions=row["today_transactions"],
                active_tickets=row["active_tickets"],
                completed_tickets=row["completed_tickets"],
                voided_transactions=row["voided_transactions"],
            )
       
        return await handle_db_error(
           operation=_fetch,
           logger=self.logger,
           context={
               
           },
           operation_name="Get dashboard summary based on date"
        )