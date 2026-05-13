DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'billing'
          AND table_name = 'transactions'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
    ) THEN
        ALTER TABLE billing.transactions
            RENAME TO payments;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND column_name = 'account_id'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND column_name = 'cashier_id'
    ) THEN
        ALTER TABLE billing.payments
            RENAME COLUMN account_id TO cashier_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'billing'
          AND indexname = 'idx_billing_transactions_account_id'
    ) THEN
        ALTER INDEX billing.idx_billing_transactions_account_id
            RENAME TO idx_billing_payments_cashier_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'billing'
          AND indexname = 'idx_billing_transactions_ticket_id'
    ) THEN
        ALTER INDEX billing.idx_billing_transactions_ticket_id
            RENAME TO idx_billing_payments_ticket_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'billing'
          AND indexname = 'idx_billing_transactions_cashier_id'
    ) THEN
        ALTER INDEX billing.idx_billing_transactions_cashier_id
            RENAME TO idx_billing_payments_cashier_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'billing'
          AND indexname = 'idx_billing_transactions_payment_status'
    ) THEN
        ALTER INDEX billing.idx_billing_transactions_payment_status
            RENAME TO idx_billing_payments_payment_status;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'billing'
          AND indexname = 'idx_billing_transactions_created_at'
    ) THEN
        ALTER INDEX billing.idx_billing_transactions_created_at
            RENAME TO idx_billing_payments_created_at;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'transactions_ticket_id_unique'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'payments_ticket_id_unique'
    ) THEN
        ALTER TABLE billing.payments
            RENAME CONSTRAINT transactions_ticket_id_unique TO payments_ticket_id_unique;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'transactions_payment_method_check'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'payments_payment_method_check'
    ) THEN
        ALTER TABLE billing.payments
            RENAME CONSTRAINT transactions_payment_method_check TO payments_payment_method_check;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'transactions_payment_status_check'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'payments_payment_status_check'
    ) THEN
        ALTER TABLE billing.payments
            RENAME CONSTRAINT transactions_payment_status_check TO payments_payment_status_check;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'transactions_amounts_non_negative_check'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'payments_amounts_non_negative_check'
    ) THEN
        ALTER TABLE billing.payments
            RENAME CONSTRAINT transactions_amounts_non_negative_check TO payments_amounts_non_negative_check;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'transactions_paid_at_status_check'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'billing'
          AND table_name = 'payments'
          AND constraint_name = 'payments_paid_at_status_check'
    ) THEN
        ALTER TABLE billing.payments
            RENAME CONSTRAINT transactions_paid_at_status_check TO payments_paid_at_status_check;
    END IF;
END $$;
