from typing import Any, Optional


class AppError(Exception):
    """Base exception"""
    pass


class DomainError(AppError):
    """ Exception for Domain (Business)"""
    pass


# ===========================
# INFRA
# ===========================

class RepositoryError(AppError):
    """Error repository (DB, cache, dll)."""
    pass


# ===========================
# GENERIC — UNTUK KASUS BIASA
# (Gunakan ini untuk 80% kasus "not found" dan "already exists")
# ===========================

class EntityNotFound(AppError):
    """Entitas tidak ditemukan."""
    def __init__(self, entity: str, entity_id: Optional[Any] = None ):
        self.entity = entity
        self.entity_id = entity_id
        
        super().__init__(f"{entity}")


class EntityAlreadyExists(AppError):
    """Entitas sudah ada."""
    def __init__(self, entity: str, identifier: Any = None ):
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity}")


class BusinessRuleViolation(DomainError):
    """Pelanggaran aturan bisnis umum."""
    pass


# ===========================
# SPESIFIK — HANYA JIKA BUTUH LOGIKA BERBEDA
# ===========================

# --- Authentication ---
class InvalidPasswordError(AppError):
    """Password salah saat login."""
    pass

class InactiveUserError(AppError):
    """User ditemukan tapi status tidak aktif."""
    pass

# --- service snapshot --- 
class InvalidServiceValue(BusinessRuleViolation):
    """ Kesalahan nilai pada service type (jenis layanan)"""
    pass 

# ---  generic value object ---
class InvalidValueObject(DomainError):
    pass 

# --- Ticket & Transaksi ---

class InvalidTicketNumber(BusinessRuleViolation):
    pass 

class InvalidEntryTime(BusinessRuleViolation):
    pass 


class InvalidTicketStateError(BusinessRuleViolation):
    """Operasi tidak valid untuk status tiket saat ini."""
    pass

class TicketAlreadyInTransactionError(BusinessRuleViolation):
    """Tiket sudah terlibat dalam transaksi aktif."""
    pass

class FailedToSaveTransactionError(AppError):
    """Gagal menyimpan transaksi ke database."""
    pass

class FailedToSetTicketStatusError(AppError):
    """Gagal memperbarui status tiket di database."""
    pass


# --- Service ---
class InvalidServiceKeysError(AppError):
    """Konfigurasi layanan tidak valid (missing/wrong keys)."""
    pass